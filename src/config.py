"""
dataclasses containing application-, mail settings and job states
initialisation of the settings, states and the logger for the application
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
import logging

import yaml
from yaml.scanner import ScannerError

if TYPE_CHECKING:
    from container import Job

from dataclasses import dataclass, field

from logger import get_logger

path = Path(__file__).parent.parent


@dataclass
class MailSettings:
    """
    setting for email transmission
    sender: sender address of the email
    mailserver: hostname or IP address of the mailserver
    port: optinal port (defaults are smtp: 25, tls: 465, starttls: 587)
    tls: use tls (is preferred over starttls if both are set to true
    starttls: use starttls (even if not specified, for plain smtp it will be tried to init starttls after connecting to the server)
    verify: verify server certificates
    auth: use authentication
    username: smtp server username
    smtp_password: smtp server password
    """

    sender: str
    mailserver: str
    port: int
    tls: bool
    starttls: bool
    verify: bool
    auth: bool
    username: str
    smtp_password: str


@dataclass
class Settings:
    """
    settings class containing base settings for the application from the config file
    url: api url
    log_path: logfile path
    job_path: path for the folder containing the job configurations
    admin_email: email address of the administrator the get error messages
    api_key: optional api key for the nist cve api
    mail: MailSettings object containing the email transmission configuration
    """

    url: str
    log_path: Path
    job_path: Path
    api_key: str
    offset: int
    bg_heading: str
    bg_header: str
    bg_table: str
    mail: MailSettings

    @classmethod
    def create(cls) -> "Settings":
        """
        alternative constructor
        creates settings object from the configuration files in the hardcoded path
        """
        with path.joinpath("settings", "settings.yaml").open("r") as file:
            try:
                settings = yaml.safe_load(file)
            except ScannerError as e:
                logging.exception(e)
                logging.error("Could not load settings")
                exit()
        with path.joinpath("settings", ".secrets.yaml").open("r") as file:
            try:
                secrets = yaml.safe_load(file)
            except ScannerError as e:
                logging.exception(e)
                logging.error("Could not load secrets")
                exit()
                
        mail_settings = MailSettings(
            **settings["mail"], smtp_password=secrets["smtp_password"]
        )
        return cls(
            url=settings["url"],
            log_path=path.joinpath(settings["log_path"]),
            job_path=path.joinpath(settings["job_path"]),
            api_key=secrets["api_key"],
            offset=settings["offset"],
            bg_heading=settings["bg_heading"],
            bg_header=settings["bg_header"],
            bg_table=settings["bg_table"],
            mail=mail_settings,
        )


@dataclass
class JobStates:
    """
    class containing states of the job to be updated on runtime
    last_run: last time the jobs were finished
    """

    last_run: dict = field(init=False)

    def __post_init__(self):
        """
        load last run of all jobs after initialisation
        """
        self.last_run = self.load()

    def load(self) -> dict[str, str]:
        """
        retrieve last time when the jobs were startet
        """
        last_run_path = path.joinpath("settings", "last_run.yaml")
        if last_run_path.exists():
            with last_run_path.open("r") as file:
                last_run = yaml.safe_load(file)
                return last_run if last_run is not None else {}
        else:
            return {}

    def dump(self) -> None:
        """
        save last time when the jobs were startet to file
        """
        with path.joinpath("settings", "last_run.yaml").open("w") as file:
            yaml.safe_dump(self.last_run, file)

    def save_last_job_run(self, job: "Job") -> None:
        """
        store successfull run of a single jobs
        """
        now = datetime.now()
        now -= timedelta(seconds=now.second, microseconds=now.microsecond)
        self.last_run[job.file] = now.strftime("%Y-%m-%d %H:%M:%S")
        

settings = Settings.create()
states = JobStates()
logger = get_logger(settings.log_path)
