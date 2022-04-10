"""
functions for retrieving and filtering the current jobs to run
"""

from datetime import datetime, timedelta
from itertools import groupby
from pathlib import Path
from typing import Generator, Iterable

import yaml
from yaml.scanner import ScannerError

from config import JobStates, Settings, logger
from container import Job, JobList, JSONDict
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


def read_job_files(settings: Settings) -> Generator[tuple[JSONDict, Path], None, None]:
    """
    generator reading job configs from the configuration folder
    """
    for file in settings.job_path.iterdir():
        with file.open("r") as config:
            try:
                jobs = yaml.safe_load(config)
            except ScannerError as e:
                logger.exception(e)
                logger.error(f"Skipping file {file}")
                continue
            else:
                yield jobs, file


def update_job_configs(
    job_configs: Generator[tuple[JSONDict, Path], None, None], states: JobStates
) -> Generator[JSONDict, None, None]:
    """
    updtate the config dictionary with filename and last runtime of the jobs
    """
    for jobs, file in job_configs:
        jobs["file"] = file.parts[-1]
        jobs["last_run"] = get_last_job_start(states, file.parts[-1], jobs["interval"])
        yield jobs


def get_jobs(
    job_configs: Generator[JSONDict, None, None]
) -> Generator[Job, None, None]:
    """
    generator yielding jobs from the imported job configs
    """
    for jobs in job_configs:
        for job in jobs["jobs"]:
            for address in jobs["send_to"]:
                try:
                    yield Job(
                        starttime=jobs["starttime"],
                        interval=jobs["interval"],
                        updates=jobs["updates"],
                        send_to=address,
                        file=jobs["file"],
                        last_run=jobs["last_run"],
                        **job,
                    )
                except Exception as e:
                    logger.error(
                        f'Jobs for the file {jobs["file"]} could not be created due to the following error:'
                    )
                    logger.exception(e)


def get_job_status(job: Job) -> bool:
    """
    determine if a job has to be run now
    """
    current_hour = (
        datetime.now().hour if datetime.now().minute < 30 else datetime.now().hour + 1
    )
    return not bool((current_hour - job.starttime) % job.interval)


def get_current_jobs(jobs: Generator[Job, None, None]) -> Iterable[Job]:
    """
    filter for all jobs that have to be run now
    """
    return filter(get_job_status, jobs)


def group_jobs(jobs: Iterable[Job]) -> list[JobList]:
    """
    group jobs by last update time and interval to make only one api request per group
    """
    sorted_jobs = sorted(
        jobs,
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


def create_job_groups(settings: Settings, states: JobStates) -> list[JobList]:
    """
    pipeline for creating job groups from all config files
    """
    job_configs = read_job_files(settings)
    updated_job_configs = update_job_configs(job_configs, states)
    jobs = get_jobs(updated_job_configs)
    current_jobs = get_current_jobs(jobs)
    return group_jobs(current_jobs)


def join_jobs_for_recipient(job_groups: list[JobList]):
    """
    group email jobs by recipient to send only one email per recipient
    """
    jobs = [job for group in job_groups for job in group]
    sorted_jobs = sorted(jobs, key=lambda job: job.send_to)
    grouped_jobs = groupby(sorted_jobs, lambda job: job.send_to)
    return [list(jobs[1]) for jobs in grouped_jobs]
