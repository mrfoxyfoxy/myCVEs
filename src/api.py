"""
function and coroutines for making the requests to the NIST CVE API
and to filter new and updated cves for the configured products
"""

import asyncio
from datetime import datetime
from typing import AsyncIterable, Optional

import httpx
from httpx import NetworkError, TimeoutException

from config import JobStates, Settings, logger
from container import CVEReport, Job, JobList, JSONDict
from errors import RequestException, retry
from formatters import format_parameter_time


def create_params(job: Job) -> tuple[dict[str, str], dict[str, str]]:
    """
    create parameters for a job
    the keyword parameter is not used because results are not 100% accurate for vendor
    for products would be separate requests needed
    """

    params_pub = {
        "pubStartDate": format_parameter_time(job.last_run),
        "pubEndDate": format_parameter_time(datetime.now()),
        "resultsPerPage": "100",
    }
    params_mod = {
        "modStartDate": params_pub["pubStartDate"],
        "modEndDate": params_pub["pubEndDate"],
        "resultsPerPage": "100",
    }

    if job.additional_parameters:
        for param in job.additional_parameters:
            if param in ("pubStartDate", "pubEndDate"):
                params_pub[param] = job.additional_parameters[param]
                continue
            if param in ("modStartDate", "modEndDate"):
                params_mod[param] = job.additional_parameters[param]
                continue
            params_pub[param] = job.additional_parameters[param]
            params_mod[param] = job.additional_parameters[param]

    return params_pub, params_mod


def get_next_index(data: JSONDict) -> Optional[int]:
    """
    determine if paging is needed and return the next index if needed
    """
    results_per_page = data["resultsPerPage"]
    start_index = data["startIndex"]
    total_results = data["totalResults"]
    if total_results - results_per_page > start_index + 1:
        return start_index + results_per_page
    return None


def extend_product_name_list(job: Job) -> set[str]:
    """
    setting all products to lower case
    extend the products list with versions of the products replacing ' ' with '_' and vice versa
    """
    products: set[str] = set(map(lambda product: product.lower(), job.products))
    new_products: set[str] = set()
    for product in products:
        if " " in product:
            new_products.add(product.replace(" ", "_"))
        elif "_" in product:
            new_products.add(product.replace("_", " "))
    return products | new_products


def check_for_relevant_cve(cve_report: CVEReport, job: Job) -> bool:
    """
    determine if a product specified in the configuration file is present in the cve
    """
    vendor_fields = {
        field.lower()
        for field in (
            cve_report.cve.assigner,
            *cve_report.cve.refsource,
            *cve_report.cve.description,
            *(cpe.cpe_match for cpe in cve_report.cpes),
        )
    }
    if any(job.vendor.lower() in field for field in vendor_fields):
        for product in extend_product_name_list(job):
            if any(product in field for field in vendor_fields):
                return True
    return False


def filter_cves(cves: list[CVEReport], job: Job) -> list[CVEReport]:
    """
    filter all retrieved cves for the relevant products
    """
    return [cve for cve in cves if check_for_relevant_cve(cve, job)]


def filter_empty_jobs(states: JobStates, jobs: JobList) -> JobList:
    """
    discard jobs without new or updated cves and save their run state
    """
    new_jobs: list[Job] = []
    for job in jobs:
        if job.new_cves or job.updated_cves:
            new_jobs.append(job)
        else:
            states.save_last_job_run(job)
    return new_jobs


def sort_and_deduplicate_cves(jobs: JobList) -> JobList:
    """
    sort cves by base score and remove duplicate entries if a new cve was already updated in the same timeslot
    """
    for job in jobs:
        if job.new_cves:
            job.new_cves = sorted(
                job.new_cves, key=lambda job: job.cve_score.base_score, reverse=True
            )
        if job.updated_cves:
            if job.new_cves:
                new_cve_ids = [new_cve.cve.id for new_cve in job.new_cves]
                job.updated_cves = [
                    cve for cve in job.updated_cves if not cve.cve.id in new_cve_ids
                ]
            job.updated_cves = sorted(
                job.updated_cves, key=lambda job: job.cve_score.base_score, reverse=True
            )
    return jobs


@retry(
    (TimeoutException, NetworkError, RequestException),
    logger=logger,
    raises=RequestException,
)
async def make_api_request(
    settings: Settings, params: dict, client: httpx.AsyncClient
) -> JSONDict:
    """
    make one single api request
    put to seperate coroutine to have retries only on a single page not all, if one fails
    """
    response = await client.get(settings.url, params=params)
    if response.status_code != 200:
        raise RequestException(
            f"Requests not successfull: status code {response.status_code}. {response.json().get('message', 'No error message retrieved')}"
        )
    return response.json()


async def get_cve_page(
    settings: Settings,
    params: dict,
    client: httpx.AsyncClient,
    index: Optional[int] = 0,
) -> AsyncIterable:
    """
    async generator - yielding the request pages from the api
    """
    while index is not None:
        data = await make_api_request(settings, params, client)
        # ! if paging is needed, the new startIndex is updated to params for the next request
        if (index := get_next_index(data)) is not None:
            params["startIndex"] = index
        yield data


async def get_all_new_pages(
    settings: Settings, params: dict, client: httpx.AsyncClient
) -> list[CVEReport]:
    """
    trigger the requests for one cve and parse the data while starting the next request
    """
    cves = []
    async for raw_data in get_cve_page(settings, params, client):
        data = raw_data["result"]["CVE_Items"]
        results = [CVEReport(cve) for cve in data]
        cves.extend(results)
    return cves


async def get_cves_by_group(
    settings: Settings, states: JobStates, job_group: JobList, client: httpx.AsyncClient
) -> JobList:
    """
    get new and updated cves for a group of jobs with the same settings
    only apply updated cves to jobs that have this setting
    """
    params_new, params_updated = create_params(job_group[0])
    new_cves_task = asyncio.create_task(get_all_new_pages(settings, params_new, client))
    if any(job.updates is True for job in job_group):
        updated_cves_task = asyncio.create_task(
            get_all_new_pages(settings, params_updated, client)
        )
        new_cves, updated_cves = await asyncio.gather(
            new_cves_task, updated_cves_task, return_exceptions=True
        )
        if isinstance(updated_cves, BaseException):
            raise RequestException(
                f"Updated CVEs could not be retrieved: {updated_cves}"
            )
        for job in job_group:
            job.updated_cves = filter_cves(updated_cves, job) if job.updates else []
    else:
        new_cves_list = await asyncio.gather(new_cves_task, return_exceptions=True)
        new_cves = new_cves_list[0]
    if isinstance(new_cves, BaseException):
        raise RequestException(f"New CVEs could not be retrieved: {new_cves}")
    for job in job_group:
        job.new_cves = filter_cves(new_cves, job)
    filtered_group = filter_empty_jobs(states, job_group)
    return sort_and_deduplicate_cves(filtered_group)
