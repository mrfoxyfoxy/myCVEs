"""
functions for retrieving and filtering the current jobs to run
"""

from datetime import datetime, timedelta
from itertools import groupby
from typing import Generator, Iterable

import yaml
from yaml.scanner import ScannerError

from config import JobStates, Settings, logger
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
        now = datetime.now() 
        now -= timedelta(seconds=now.second, microseconds=now.microsecond)        
        now -= timedelta(hours=interval)         
        return now


def get_jobs(settings: Settings, states: JobStates) -> Generator[Job, None, None]:
    """
    generator reading jobs from the configuration folder
    """
    for file in settings.job_path.iterdir():
        with file.open("r") as config:
            try:
                jobs = yaml.safe_load(config)
            except ScannerError as e:
                logger.exception(e)
                logger.error(f'Skipping file {file}')
                continue
            
            for job in jobs["jobs"]:
                for address in jobs["send_to"]:
                    try:
                        yield Job(
                            starttime=jobs["starttime"],
                            interval=jobs["interval"],
                            updates=jobs["updates"],
                            send_to=address,
                            file=file.parts[-1],
                            last_run=get_last_job_start(
                                states, file.parts[-1], jobs["interval"]
                            ),
                            **job
                        )
                    except Exception as e:
                        logger.error(f'Jobs for the file {file} could not be created due to the following error:')
                        logger.exception(e)


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
        current_jobs,
        key=lambda job: (
            round_time(job.last_run),
            job.interval,
            tuple(job.additional_parameters.keys()),
            tuple(job.additional_parameters.values()),
        ),
    )
    grouped_jobs = groupby(
        sorted_jobs,
        lambda job: (
            round_time(job.last_run),
            job.interval,
            tuple(job.additional_parameters.keys()),
            tuple(job.additional_parameters.values()),
        ),
    )
    return [list(jobs[1]) for jobs in grouped_jobs]


def join_jobs_for_recipient(job_groups: list[JobList]):
    """
    group jobs by recipient to send only one email per recipient
    """
    jobs = [job for group in job_groups for job in group]
    sorted_jobs = sorted(jobs, key=lambda job: job.send_to)
    grouped_jobs = groupby(sorted_jobs, lambda job: job.send_to)
    return [list(jobs[1]) for jobs in grouped_jobs]
