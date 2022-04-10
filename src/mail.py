"""
functions to format the CVE data and render the email
and for sending the emails to the recipients
"""

import ssl
from contextlib import asynccontextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ssl import SSLCertVerificationError
from typing import Optional

import aiosmtplib
from aiosmtplib.errors import (
    SMTPConnectError,
    SMTPConnectTimeoutError,
    SMTPServerDisconnected,
)
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import JobStates, Settings, logger, path
from container import JobList
from errors import EmailException, retry

env = Environment(
    loader=FileSystemLoader(path.joinpath("templates")),
    autoescape=select_autoescape(["html"]),
)

template = env.get_template("new_mail.html")


def create_subject_prefix(jobs: JobList) -> str:
    """
    check if there are new and/or updated CVEs in the jobs and create message prefix
    """
    new = any(job.new_cves for job in jobs)    
    updated = any(job.updated_cves for job in jobs)
    return "New and updated" if new and updated else "New" if new else "Updated"


def create_message_subject(jobs: JobList) -> tuple[str, str]:
    """
    create the subject and title for the message based on types of CVEs
    """
    vendors = ", ".join(job.vendor.capitalize() for job in jobs)
    prefix = create_subject_prefix(jobs)
    title = f"{prefix} CVEs"
    return f"{title} for your products from {vendors}", title


def create_email(settings: Settings, jobs: JobList) -> MIMEMultipart:
    """
    create one email for all jobs in the group to one recipient
    """
    subject, title = create_message_subject(jobs)
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = settings.mail.sender
    message["To"] = jobs[0].send_to
    updates = any(job.updated_cves for job in jobs)
    try:
        html = template.render(jobs=jobs, title=title, updates=updates, settings=settings)
    except Exception as e:
        logger.exception(e)
        raise EmailException("HTML rendering error")
    body = MIMEText(html, "html")
    message.attach(body)
    return message


@retry(EmailException, logger=logger)
async def create_connection(settings: Settings) -> aiosmtplib.SMTP:
    """
    create an smtp server based on configuration parameters and connect to it
    by default the coroutine will be tried 5 times before given up to connect
    """
    if settings.mail.verify:
        context = ssl.create_default_context()
    else:
        context = None
    if settings.mail.tls:
        server = aiosmtplib.SMTP(
            settings.mail.mailserver,
            settings.mail.port or 465,
            use_tls=True,
            tls_context=context,
        )
    elif settings.mail.starttls:
        server = aiosmtplib.SMTP(
            settings.mail.mailserver, settings.mail.port or 587, start_tls=True
        )
    else:
        server = aiosmtplib.SMTP(settings.mail.mailserver, settings.mail.port or 25)
    try:
        await server.connect()
        if not settings.mail.tls:
            await server.starttls(
                validate_certs=settings.mail.verify, tls_context=context
            )
        if settings.mail.auth:
            await server.login(
                username=settings.mail.username, password=settings.mail.smtp_password
            )
    except SMTPConnectTimeoutError as e:
        logger.exception(e)
        raise EmailException("SMTP timeout error")
    except (SMTPServerDisconnected, SMTPConnectError) as e:
        logger.exception(e)
        raise EmailException("SMTP connection error")
    except SSLCertVerificationError as e:
        logger.exception(e)
        raise EmailException("SMTP ssl validation error")
    else:
        return server


@asynccontextmanager
async def start_server(settings: Settings):
    """
    create an async smtp server an yield it as context manager
    """
    server = await create_connection(settings)
    try:
        yield server
    finally:
        await server.quit()


async def send_email(
    settings: Settings, states: JobStates, job_group: JobList
) -> Optional[bool]:
    """
    create the message for each job_group
    start a server
    and send the mail
    """
    # !Todo: move create_email out of this coro and apply retry deco to send_email instead of create_connection
    message = create_email(settings, job_group)
    try:
        # ! because smtp is a sequential protocl, we need multiple connections to split the work for multiple emails
        # ! thus sharing one server instance would bring no benefit
        async with start_server(settings) as server:
            await server.sendmail(message["From"], message["To"], message.as_string())
    except SMTPConnectTimeoutError as e:
        logger.exception(e)
        raise EmailException("SMTP timeout error")
    except SMTPConnectError as e:
        logger.exception(e)
        raise EmailException("SMTP connection error")
    else:
        for job in job_group:
            states.save_last_job_run(job)
        return True
