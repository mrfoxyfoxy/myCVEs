"""
higher level exceptions passed to the user
a retry decorator for executing a function/coroutine multiple times if one of a set of specified errors occurs
"""

import asyncio
import logging
from functools import wraps
from inspect import iscoroutinefunction
from time import sleep
from typing import TYPE_CHECKING, Callable, Optional, Type, Union

if TYPE_CHECKING:
    from mycves.container import JobList


def retry(
    exceptions_to_check: Union[tuple[Type[Exception], ...], Type[Exception]],
    tries: int = 5,
    delay: Union[int, float] = 1,
    backoff: Union[int, float] = 2,
    logger: Optional[logging.Logger] = None,
    raises: Optional[Type[Exception]] = None,
) -> Callable:
    """
    decorator for executing a function/coroutine multiple times if one of a set of specified errors occurs

    exceptions_to_check: exceptions that are valid for a retry
    tries: number of retries
    delay: initial delay for next retry
    backoff: multiplicator for the for the nex retry
    logger: optinal logger
    raises: optional exception to raise when all retries fail
    """

    def deco_retry(callable: Callable):
        @wraps(callable)
        def func_retry(*args, **kwargs):
            mdelay, mbackoff = delay, backoff
            for _ in range(tries - 1):
                try:
                    return callable(*args, **kwargs)
                except exceptions_to_check as e:
                    msg = f"Retrying {callable.__name__} for {_+1}. time. Catched error:\n{e} "
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    sleep(mdelay)
                    mdelay *= mbackoff
            else:
                if raises:
                    try:
                        data = callable(*args, **kwargs)
                    except exceptions_to_check as e:
                        if logger:
                            logger.exception(e)
                        else:
                            print(e)
                        raise raises(f"{raises.__name__}: {e}")
                    else:
                        return data
                return callable(*args, **kwargs)

        @wraps(callable)
        async def coro_retry(*args, **kwargs):
            mdelay, mbackoff = delay, backoff
            for _ in range(tries - 1):
                try:
                    return await callable(*args, **kwargs)
                except exceptions_to_check as e:
                    msg = f"Retrying {callable.__name__} for {_+1}. time. Catched error:{str(e)} "
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    await asyncio.sleep(mdelay)
                    mdelay *= mbackoff
            else:
                if raises:
                    try:
                        data = await callable(*args, **kwargs)
                    except exceptions_to_check as e:
                        if logger:
                            logger.exception(e)
                        else:
                            print(e)
                        raise raises(f"{raises.__name__}: {e}")
                    else:
                        return data
                return await callable(*args, **kwargs)

        return coro_retry if iscoroutinefunction(callable) else func_retry

    return deco_retry


def filter_errors(
    results: list, job_groups: list["JobList"], logger: logging.Logger
) -> list["JobList"]:
    """
    filter results of asyncio gather
    returns: successfull jobs
    logs errored jobs
    """
    succeseded_jobs: list["JobList"] = []
    errored_jobs: list[tuple[Exception, "JobList"]] = []
    for result, jobs in zip(results, job_groups):
        if isinstance(result, Exception):
            errored_jobs.append((result, jobs))
        else:
            succeseded_jobs.append(result)
    if errored_jobs:
        log_errored_jobs(errored_jobs, logger)
    return succeseded_jobs


def log_errored_jobs(
    errored_jobs: list[tuple[Exception, "JobList"]], logger: logging.Logger
) -> None:
    """
    log errored jobs and the raised exception
    """
    for error, jobs in errored_jobs:
        logger.error(
            f'Jobs in the following files failed: {", ".join(job.file for job in jobs)} with exceptions: {str(error)}'
        )


class FormatException(Exception):
    """
    errors while formating data
    """

    pass


class EmailException(Exception):
    """
    errors while sending emails
    """

    pass


class RequestException(Exception):
    """
    errors while excuting api calls
    """

    pass
