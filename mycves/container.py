"""
dataclasses containing data for the configured jobs and the parsed CVEs
type aliases for typing
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from datetime import datetime
from functools import partial
from typing import Any, Optional, Union

from mycves import formatters
from mycves.data_parser import recursive_get
from mycves.typing import JSON, JSONDict, JSONList


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

    data: InitVar[JSON]
    id: str = field(init=False)
    # assigner: Any = field(init=False)
    urls: list[str] = field(init=False)
    sources: list[str] = field(init=False)
    descriptions: list[str] = field(init=False)
    published: Optional[str] = field(init=False)
    modified: Optional[str] = field(init=False)

    def __post_init__(self, data):
        """
        fields get initialized after parsing the api response
        """
        get_cve = partial(recursive_get, data, "cve")
        self.id = get_cve("id")
        # self.assigner = get_cve("cve", "CVE_data_meta", "ASSIGNER")
        self.urls = get_cve("references", "url")
        self.sources = get_cve("references", "source")
        self.descriptions = get_cve("descriptions", "value")

        self.published = (
            formatters.format_cve_dates(pub_date)
            if (pub_date := get_cve("published")) is not None
            else pub_date
        )
        self.modified = (
            formatters.format_cve_dates(mod_date)
            if (mod_date := get_cve("lastModified")) is not None
            else mod_date
        )


@dataclass
class CPE:
    """parsed CPE data (affected products) from the request"""

    data: InitVar[JSON]
    vulnerable: bool = field(init=False)
    cpe_match: str = field(init=False)
    version_start: str = field(init=False)
    version_end: str = field(init=False)

    def __post_init__(self, data):
        """
        fields get initialized after parsing the api response
        """
        get_cpe = partial(recursive_get, data)
        self.vulnerable = get_cpe("vulnerable")
        self.cpe_match = formatters.format_cpe_match(get_cpe("criteria"))
        self.version_start = (
            f"incl. {including}"
            if (including := get_cpe("versionStartIncluding"))
            else f"excl. {excluding}"
            if (excluding := get_cpe("versionStartExcluding"))
            else ""
        )
        self.version_end = (
            f"incl. {including}"
            if (including := get_cpe("versionEndIncluding"))
            else f"excl. {excluding}"
            if (excluding := get_cpe("versionEndExcluding"))
            else ""
        )


@dataclass
class CVEScore:
    """
    parsed CVE scoring from the request
    """

    data: InitVar[JSON]
    attack_vector: str = field(init=False)
    base_score: float = field(init=False)
    base_severity: str = field(init=False)
    exploitability_score: float = field(init=False)
    impact_score: float = field(init=False)

    def __post_init__(self, data):
        _get_cve_score = data["metrics"]
        if "cvssMetricV31" in _get_cve_score:
            get_cve_score = partial(recursive_get, _get_cve_score["cvssMetricV31"][0])
        elif "cvssMetricV30" in _get_cve_score:
            get_cve_score = partial(recursive_get, _get_cve_score["cvssMetricV30"][0])
        elif "cvssMetricV2" in _get_cve_score:
            get_cve_score = partial(recursive_get, _get_cve_score["cvssMetricV2"][0])
        else:
            get_cve_score = partial(recursive_get, {})
        self.attack_vector = (
            get_cve_score("cvssData", "attackVector")
            or get_cve_score("cvssData", "accessVector")
            or ""
        )
        self.base_score = get_cve_score("cvssData", "baseScore") or ""
        self.base_severity = (
            get_cve_score("cvssData", "baseSeverity")
            or get_cve_score("baseSeverity")
            or ""
        )
        self.exploitability_score = get_cve_score("exploitabilityScore") or ""
        self.impact_score = get_cve_score("impactScore") or ""


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
        get_cpes = get_cve_report("cve", "configurations", "nodes", "cpeMatch")
        get_cve_score = get_cve_report("cve")
        self.cve = CVE(data)  # type: ignore
        self.cpes = [CPE(cpe) for cpe in get_cpes]  # type: ignore
        self.cve_score = CVEScore(get_cve_score)  # type: ignore
