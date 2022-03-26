"""
run the application one time
"""

import asyncio
from contextlib import AsyncExitStack

import httpx

from api import get_cves_by_group
from config import JobStates, Settings, logger, settings, states
from errors import filter_errors
from jobs_ import create_job_groups, join_jobs_for_recipient
from mail import send_email


async def run_jobs(settings: Settings, states: JobStates) -> None:
    """
    get all current jobs
    get new/updated CVEs
    send emails with new/updated CVEs
    update last run time for successfull jobs
    """
    job_groups = create_job_groups(settings, states)
    if not job_groups:
        logger.info("No Jobs to run right now.")
        return
    async with AsyncExitStack() as stack:
        stack.callback(states.dump)
        client = await stack.enter_async_context(httpx.AsyncClient())
        cve_groups = await asyncio.gather(
            *(
                get_cves_by_group(settings, states, group, client)
                for group in job_groups
            ),
            return_exceptions=True
        )
        succeeded_requests = filter_errors(cve_groups, job_groups, logger)
        email_groups = join_jobs_for_recipient(succeeded_requests)
        if not email_groups:
            logger.info("No new CVEs for your products found.")
            return
        # ! because jobs habe to be rejoined first, all emails are sent as bulk
        mail_results = await asyncio.gather(
            *(send_email(settings, states, group) for group in email_groups),
            return_exceptions=True
        )
        filter_errors(mail_results, email_groups, logger)


async def main(settings: Settings, states: JobStates):
    while True:
        await run_jobs(settings, states)
        await asyncio.sleep(1800)


if __name__ == "__main__":
    asyncio.run(main(settings, states))
