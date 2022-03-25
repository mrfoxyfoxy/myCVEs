"""
functions for retrieving and filtering the current jobs to run
"""

from datetime import datetime, timedelta
from itertools import groupby
from typing import Generator, Iterable

import yaml

from config import JobStates, Settings
from container import Job, JobList
from formatters import round_time


def get_last_job_start(states: JobStates, file: str, interval: int) -> datetime:
    """
    retrieve last time when the jobs were startet or actual time minus job interval

    file: name of the configuration file
    interval: interval for the job to execute
    """
    if file in states.last_run:
        return datetime.strptime(states.last_run[file], "%Y-%m-%d %H:%M:%S")
    else:
        return datetime.now() - timedelta(hours=interval)


def get_jobs(settings: Settings, states: JobStates) -> Generator[Job, None, None]:
    """
    generator reading jobs from the configuration folder
    """
    for file in settings.job_path.iterdir():
        with file.open("r") as config:
            jobs = yaml.safe_load(config)
            for job in jobs["jobs"]:                
                yield Job(
                    starttime=jobs["starttime"],
                    interval=jobs["interval"],
                    updates=jobs["updates"],
                    send_to=jobs["send_to"],
                    file=file.parts[-1],
                    last_run=get_last_job_start(
                        states, file.parts[-1], jobs["interval"]
                    ),
                    **job
                )


def get_job_status(job: Job) -> bool:
    """
    determine if a job has to be run now
    """
    current_hour = (
        datetime.now().hour if datetime.now().minute < 30 else datetime.now().hour + 1
    )
    return not bool((current_hour - job.starttime) % job.interval)


def get_current_jobs(settings: Settings, states: JobStates) -> Iterable[Job]:
    """
    get jobs to run for new published CVEs and for updates CVEs
    and filter for all jobs that have to be run now
    """
    jobs = get_jobs(settings, states)
    return filter(get_job_status, jobs)


def create_job_groups(settings: Settings, states: JobStates) -> list[JobList]:
    """
    group jobs by last update time and interval to make only one api request per group
    """
    current_jobs = get_current_jobs(settings, states)
    sorted_jobs = sorted(
        current_jobs, key=lambda job: (round_time(job.last_run), job.interval)
    )
    grouped_jobs = groupby(
        sorted_jobs, lambda job: (round_time(job.last_run), job.interval)
    )
    return [list(jobs[1]) for jobs in grouped_jobs]


def join_jobs_for_recipient(job_groups: list[JobList]):
    """
    group jobs by recipient to send only one email per recipient
    """
    jobs = [job for group in job_groups for job in group]
    grouped_jobs = groupby(jobs, lambda job: job.send_to)
    return [list(jobs[1]) for jobs in grouped_jobs]
