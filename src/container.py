"""
dataclasses containing data for the configured jobs and the parsed CVEs
type aliases for typing
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from datetime import datetime
from functools import partial
from typing import Any, Optional, Union

import formatters
from data_parser import recursive_get

JSONDict = dict[str, Any]
JSONList = list[Any]
JSON = Union[JSONDict, JSONList]


@dataclass
class Job:
    """
    Job from a configuration file that should be run against the CVE database

    starttime: relative starttime of the jobs
    interval: interval of job execution relativ to starttime
    updates: fetch not only new CVEs but updated, too
    send_to: recipient email for the CVEs
    vendor: products vendor for lookup
    products: products to for lookup
    file: filename in configuration folder
    last_run: last execution of the job
    additional_parameters: dictionary containing additional_parameters parameters for the api request, can override default parameters
    new_cves: list of the retrieved CVES - initialized at runtime
    updated_cves: list of the updated CVES - initialized at runtime
    """

    starttime: int
    interval: int
    updates: bool
    send_to: str
    vendor: str
    products: list
    file: str
    last_run: datetime
    additional_parameters: dict[str, str] = field(default_factory=dict)
    new_cves: Optional[list[CVEReport]] = None
    updated_cves: Optional[list[CVEReport]] = None


JobList = list[Job]


@dataclass
class CVE:
    """
    parsed CVE information data from the request
    assigner and refsource are only used as search fields for vendors/products
    """

    data: InitVar[dict]
    id: Any = field(init=False)
    assigner: Any = field(init=False)
    urls: Any = field(init=False)
    refsource: Any = field(init=False)
    description: Any = field(init=False)
    published: Optional[Any] = field(init=False)
    modified: Any = field(init=False)

    def __post_init__(self, data):
        """
        fields get initialized after parsing the api response
        """
        get_cve = partial(recursive_get, data)
        self.id = get_cve("cve", "CVE_data_meta", "ID")
        self.assigner = get_cve("cve", "CVE_data_meta", "ASSIGNER")
        self.urls = get_cve("cve", "references", "reference_data", "url")
        self.refsource = get_cve("cve", "references", "reference_data", "refsource")
        self.description = get_cve("cve", "description", "description_data", "value")
        self.published = formatters.format_cpe_dates(get_cve("publishedDate"))  # type: ignore
        self.modified = formatters.format_cpe_dates(get_cve("lastModifiedDate"))  # type: ignore


@dataclass
class CPE:
    """parsed CPE data (affected products) from the request"""

    data: InitVar[JSON]
    vulnerable: Any = field(init=False)
    cpe_match: Any = field(init=False)
    version_start: Any = field(init=False)
    version_end: Any = field(init=False)

    def __post_init__(self, data):
        """
        fields get initialized after parsing the api response
        """
        get_cpe = partial(recursive_get, data)
        self.vulnerable = get_cpe("vulnerable")
        self.cpe_match = formatters.format_cpe_match(get_cpe("cpe23Uri"))  # type: ignore
        self.version_start = get_cpe("versionStartIncluding") or get_cpe(
            "versionStartExcluding"
        )
        self.version_end = get_cpe("versionEndIncluding") or get_cpe(
            "versionEndExcluding"
        )


@dataclass
class CVEScore:
    """
    parsed CVE scoring from the request
    """

    data: InitVar[JSON]
    attack_vector: Any = field(init=False)
    base_score: Any = field(init=False)
    base_severity: Any = field(init=False)
    exploitability_score: Any = field(init=False)
    impact_score: Any = field(init=False)

    def __post_init__(self, data):
        get_cve_score = partial(recursive_get, data)
        self.attack_vector = (
            get_cve_score("baseMetricV3", "cvssV3", "attackVector")
            or get_cve_score("baseMetricV2", "cvssV2", "attackVector")
            or "-"
        )
        self.base_score = (
            get_cve_score("baseMetricV3", "cvssV3", "baseScore")
            or get_cve_score("baseMetricV2", "cvssV2", "baseScore")
            or "-"
        )
        self.base_severity = (
            get_cve_score("baseMetricV3", "cvssV3", "baseSeverity")
            or get_cve_score("baseMetricV2", "cvssV2", "severity")
            or "-"
        )
        self.exploitability_score = (
            get_cve_score("baseMetricV3", "exploitabilityScore")
            or get_cve_score("baseMetricV2", "exploitabilityScore")
            or "-"
        )
        self.impact_score = (
            get_cve_score("baseMetricV3", "impactScore")
            or get_cve_score("baseMetricV2", "impactScore")
            or "-"
        )


@dataclass
class CVEReport:
    """
    full dataset of the CVE request
    """

    data: InitVar[JSON]
    cve: CVE = field(init=False)
    cpes: list[CPE] = field(init=False)
    cve_score: CVEScore = field(init=False)

    def __post_init__(self, data):
        """
        fields get initialized after parsing the api response
        """
        get_cve_report = partial(recursive_get, data)
        get_cpes = get_cve_report("configurations", "nodes", "cpe_match")
        get_cve_score = get_cve_report("impact")
        self.cve = CVE(data)  # type: ignore
        self.cpes = [CPE(cpe) for cpe in get_cpes]  # type: ignore
        self.cve_score = CVEScore(get_cve_score)  # type: ignore
