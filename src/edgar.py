"""EDGAR fetch + parse for 13F filings.

Fetch path (verified in notes/research/02-data-source-landscape.md):
  data.sec.gov/submissions/CIK##########.json  -> accessions of 13F-HR / 13F-HR/A
  www.sec.gov/Archives/.../{accession}/index.json -> file list
  primary_doc.xml (cover page) + filer-named infotable XML (one <infoTable> per row)

Raw responses land in data/raw/<cik>/... (gitignored, re-fetchable).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from common import RAW, fetch_cached, load_json

SUBMISSIONS_URL = "https://data.sec.gov/submissions/{name}"
ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{fname}"


@dataclass
class Filing:
    cik: int
    accession: str          # with dashes, e.g. 0000950123-25-008361
    form: str               # 13F-HR or 13F-HR/A
    filing_date: str        # YYYY-MM-DD
    report_date: str        # period of report, YYYY-MM-DD

    @property
    def acc_nodash(self) -> str:
        return self.accession.replace("-", "")


@dataclass
class ParsedFiling:
    filing: Filing
    report_type: str                    # 13F HOLDINGS REPORT / 13F COMBINATION REPORT / ...
    is_amendment: bool
    amendment_no: int | None
    amendment_type: str | None          # RESTATEMENT / NEW HOLDINGS / None
    table_entry_total: int | None       # from Summary Page (cover doc)
    table_value_total: int | None
    rows: list[dict] = field(default_factory=list)


def _cik_url_name(cik: int) -> str:
    return f"CIK{cik:010d}.json"


def list_13f_filings(cik: int, earliest_report_date: str) -> list[Filing]:
    """All 13F-HR / 13F-HR/A filings for cik with report_date >= earliest_report_date.

    Reads the 'recent' block of the submissions JSON; follows the paged history
    files if 'recent' does not reach back to earliest_report_date.
    """
    sub_path = fetch_cached(
        SUBMISSIONS_URL.format(name=_cik_url_name(cik)),
        RAW / str(cik) / "submissions.json",
        mutable=True,
    )
    sub = load_json(sub_path)
    blocks = [sub["filings"]["recent"]]

    recent_dates = blocks[0].get("filingDate", [])
    oldest_recent = recent_dates[-1] if recent_dates else "9999-99-99"
    if oldest_recent > earliest_report_date:
        for extra in sub["filings"].get("files", []):
            extra_path = fetch_cached(
                SUBMISSIONS_URL.format(name=extra["name"]),
                RAW / str(cik) / extra["name"],
                mutable=True,
            )
            blocks.append(load_json(extra_path))

    filings = []
    for block in blocks:
        for form, acc, fdate, rdate in zip(
            block["form"], block["accessionNumber"],
            block["filingDate"], block["reportDate"],
        ):
            if form in ("13F-HR", "13F-HR/A") and rdate >= earliest_report_date:
                filings.append(Filing(cik, acc, form, fdate, rdate))
    # Dedup (recent and paged files can overlap), stable order by filing date.
    seen, unique = set(), []
    for f in sorted(filings, key=lambda f: (f.report_date, f.filing_date, f.accession)):
        if f.accession not in seen:
            seen.add(f.accession)
            unique.append(f)
    return unique


def fetch_filing_docs(f: Filing) -> tuple[Path, Path]:
    """Download the filing's cover-page XML and infotable XML; return their paths.

    The infotable filename is filer-chosen, so locate it via index.json and
    identify it by root element rather than by name.
    """
    fdir = RAW / str(f.cik) / f.acc_nodash
    index_path = fetch_cached(
        ARCHIVES_URL.format(cik=f.cik, acc_nodash=f.acc_nodash, fname="index.json"),
        fdir / "index.json",
    )
    names = [item["name"] for item in load_json(index_path)["directory"]["item"]]
    xml_names = [n for n in names if n.lower().endswith(".xml")
                 and not n.lower().startswith("index")]

    cover_path = infotable_path = None
    for name in xml_names:
        p = fetch_cached(
            ARCHIVES_URL.format(cik=f.cik, acc_nodash=f.acc_nodash, fname=name),
            fdir / name,
        )
        root_tag = _root_localname(p)
        if root_tag == "edgarSubmission":
            cover_path = p
        elif root_tag == "informationTable":
            infotable_path = p
    if cover_path is None:
        raise ValueError(f"{f.accession}: no cover-page XML found among {xml_names}")
    return cover_path, infotable_path


def _root_localname(path: Path) -> str:
    for _, elem in ET.iterparse(path, events=("start",)):
        return elem.tag.rsplit("}", 1)[-1]
    return ""


def _text(elem: ET.Element | None, *path: str) -> str | None:
    """Namespace-agnostic descent by local names."""
    node = elem
    for name in path:
        if node is None:
            return None
        node = next((c for c in node if c.tag.rsplit("}", 1)[-1] == name), None)
    return node.text.strip() if node is not None and node.text else None


def parse_filing(f: Filing, cover_path: Path, infotable_path: Path | None) -> ParsedFiling:
    cover = ET.parse(cover_path).getroot()
    form_data = next(c for c in cover if c.tag.rsplit("}", 1)[-1] == "formData")
    cover_page = next(c for c in form_data if c.tag.rsplit("}", 1)[-1] == "coverPage")

    is_amendment = (_text(cover_page, "isAmendment") or "false").lower() == "true"
    amendment_no = _text(cover_page, "amendmentNo")
    amendment_type = _text(cover_page, "amendmentInfo", "amendmentType")
    report_type = _text(form_data, "coverPage", "reportType") or ""
    entry_total = _text(form_data, "summaryPage", "tableEntryTotal")
    value_total = _text(form_data, "summaryPage", "tableValueTotal")

    rows = []
    if infotable_path is not None:
        table = ET.parse(infotable_path).getroot()
        for it in table:
            if it.tag.rsplit("}", 1)[-1] != "infoTable":
                continue
            rows.append({
                "issuer": _text(it, "nameOfIssuer"),
                "class": _text(it, "titleOfClass"),
                "cusip": (_text(it, "cusip") or "").upper(),
                "value_usd": _text(it, "value"),
                "shares": _text(it, "shrsOrPrnAmt", "sshPrnamt"),
                "sh_prn_type": _text(it, "shrsOrPrnAmt", "sshPrnamtType"),
                "put_call": _text(it, "putCall") or "",
                "discretion": _text(it, "investmentDiscretion"),
                "other_manager": _text(it, "otherManager") or "",
                "vote_sole": _text(it, "votingAuthority", "Sole"),
                "vote_shared": _text(it, "votingAuthority", "Shared"),
                "vote_none": _text(it, "votingAuthority", "None"),
            })

    return ParsedFiling(
        filing=f,
        report_type=report_type,
        is_amendment=is_amendment,
        amendment_no=int(amendment_no) if amendment_no else None,
        amendment_type=amendment_type.upper() if amendment_type else None,
        table_entry_total=int(entry_total) if entry_total else None,
        table_value_total=int(value_total) if value_total else None,
        rows=rows,
    )
