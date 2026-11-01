from html.parser import HTMLParser
from io import BytesIO
import re

import pandas as pd


class PriceListError(ValueError):
    """Raised when a supplied price list cannot be used for financial analysis."""


def format_inr(value):
    """Format a rupee amount with Indian digit grouping and no decimal suffix."""
    amount = int(round(float(value)))
    sign = "-" if amount < 0 else ""
    digits = str(abs(amount))
    if len(digits) > 3:
        last_three = digits[-3:]
        leading = digits[:-3]
        groups = []
        while leading:
            groups.insert(0, leading[-2:])
            leading = leading[:-2]
        digits = ",".join(groups + [last_three])
    return f"₹{sign}{digits}"


class _ExcelHtmlTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append(" ".join(" ".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def _read_excel_html(contents):
    parser = _ExcelHtmlTableParser()
    parser.feed(contents.decode("utf-8-sig", errors="replace"))
    if not parser.rows:
        raise PriceListError("The Excel-compatible price list contains no table rows.")

    headers = parser.rows[0]
    rows = [
        row[:len(headers)] + [""] * max(0, len(headers) - len(row))
        for row in parser.rows[1:]
    ]
    return pd.DataFrame(rows, columns=headers)


def _normalize_column_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


def _normalize_test_id(value):
    if pd.isna(value):
        return ""
    test_id = str(value).strip()
    if re.fullmatch(r"\d+\.0+", test_id):
        test_id = test_id.split(".", 1)[0]
    return test_id.upper()


def read_price_list(contents, file_name):
    """Read the supplied Excel/Excel-HTML price list into a validated table."""
    if not contents:
        raise PriceListError("The uploaded price list is empty.")

    if contents.lstrip().lower().startswith((b"<html", b"<!doctype", b"<table")):
        price_frame = _read_excel_html(contents)
    else:
        extension = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
        engine = "xlrd" if extension == "xls" else "openpyxl"
        try:
            price_frame = pd.read_excel(BytesIO(contents), engine=engine)
        except (ImportError, ValueError, OSError) as exc:
            raise PriceListError(
                f"Could not read the uploaded price list: {type(exc).__name__}: {exc}"
            ) from exc

    source_columns = {_normalize_column_name(column): column for column in price_frame.columns}
    required = {
        "testid": "Test Id",
        "testname": "Test Name",
        "opdcharge": "OPD Charge",
        "ipdcharge": "IPD Charge",
    }
    missing = [
        display_name for normalized, display_name in required.items()
        if normalized not in source_columns
    ]
    if missing:
        raise PriceListError(
            "Price list must include these columns: " + ", ".join(missing) + "."
        )

    prices = pd.DataFrame({
        "test_id": price_frame[source_columns["testid"]].map(_normalize_test_id),
        "test_name": price_frame[source_columns["testname"]].astype("string").str.strip(),
        "opd_price": pd.to_numeric(
            price_frame[source_columns["opdcharge"]].astype("string").str.replace(",", "", regex=False),
            errors="coerce",
        ),
        "ipd_price": pd.to_numeric(
            price_frame[source_columns["ipdcharge"]].astype("string").str.replace(",", "", regex=False),
            errors="coerce",
        ),
    })
    prices = prices[prices["test_id"] != ""].copy()
    if prices.empty:
        raise PriceListError("No rows with a Test Id were found in the price list.")

    duplicate_ids = prices[prices["test_id"].duplicated(keep=False)]
    if not duplicate_ids.empty:
        conflicts = duplicate_ids.groupby("test_id")[["test_name", "opd_price", "ipd_price"]].nunique(
            dropna=False
        )
        conflicting_ids = conflicts.index[(conflicts > 1).any(axis=1)].tolist()
        if conflicting_ids:
            raise PriceListError(
                "The price list contains conflicting prices for test IDs: "
                + ", ".join(conflicting_ids[:10])
            )
        prices = prices.drop_duplicates(subset=["test_id"])

    return prices.reset_index(drop=True)


def build_financial_summary(report_frames, price_list):
    """Estimate charges by test ID and booking mode from saved report rows."""
    if not report_frames:
        raise ValueError("No report rows were supplied for financial analysis.")

    report_rows = pd.concat(report_frames, ignore_index=True)
    required_columns = {"testid", "TestName", "BookingMode"}
    missing_columns = required_columns.difference(report_rows.columns)
    if missing_columns:
        raise ValueError(
            "Saved report data is missing columns required for financial analysis: "
            + ", ".join(sorted(missing_columns))
        )

    report_rows = report_rows[["testid", "TestName", "BookingMode"]].copy()
    report_rows["test_id"] = report_rows["testid"].map(_normalize_test_id)
    report_rows["test_name"] = report_rows["TestName"].astype("string").fillna("Unknown test").str.strip()
    report_rows["booking_mode"] = (
        report_rows["BookingMode"].astype("string").str.upper().str.contains("IPD", na=False)
        .map({True: "IPD", False: "OPD"})
    )
    report_rows = report_rows[report_rows["test_id"] != ""]
    if report_rows.empty:
        raise ValueError("No report rows with test IDs were found for financial analysis.")

    counts = (
        report_rows.groupby(["test_id", "test_name", "booking_mode"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["IPD", "OPD"], fill_value=0)
        .rename(columns={"IPD": "IPD tests", "OPD": "OPD tests"})
        .reset_index()
    )
    counts["Total tests"] = counts["IPD tests"] + counts["OPD tests"]
    summary = counts.merge(
        price_list[["test_id", "opd_price", "ipd_price"]],
        on="test_id",
        how="left",
        validate="many_to_one",
    )

    summary["IPD estimate"] = summary["IPD tests"] * summary["ipd_price"].fillna(0)
    summary["OPD estimate"] = summary["OPD tests"] * summary["opd_price"].fillna(0)
    has_missing_ipd_price = (summary["IPD tests"] > 0) & summary["ipd_price"].isna()
    has_missing_opd_price = (summary["OPD tests"] > 0) & summary["opd_price"].isna()
    summary["Price available"] = ~(has_missing_ipd_price | has_missing_opd_price)
    summary["Estimated charges"] = (
        summary["IPD estimate"] + summary["OPD estimate"]
    ).where(summary["Price available"])

    total_tests = int(summary["Total tests"].sum())
    priced_rows = summary[summary["Price available"]]
    total_ipd_charges = float(priced_rows["IPD estimate"].sum())
    total_opd_charges = float(priced_rows["OPD estimate"].sum())
    priced_tests = int(priced_rows["Total tests"].sum())
    totals = {
        "estimated_charges": total_ipd_charges + total_opd_charges,
        "ipd_estimated_charges": total_ipd_charges,
        "opd_estimated_charges": total_opd_charges,
        "tests_with_prices": priced_tests,
        "tests_without_prices": total_tests - priced_tests,
        "price_coverage_percent": (priced_tests / total_tests * 100) if total_tests else 0.0,
    }

    display = summary.rename(columns={
        "test_name": "Test",
        "ipd_price": "IPD price",
        "opd_price": "OPD price",
    })
    display = display[
        [
            "Test", "Total tests", "IPD tests", "IPD price", "OPD tests", "OPD price",
            "Estimated charges", "Price available",
        ]
    ].sort_values(["Total tests", "Test"], ascending=[False, True]).reset_index(drop=True)
    return display, totals
