#!/usr/bin/env python3
"""Pull the headline SPARÁN figures from statespend.ie into the site markup.

statespend.ie is the live front end for the SPARÁN dataset, and it publishes the
same totals its own pages render over a small read-only JSON API:

    GET https://statespend.ie/api/summary
        {"records": 598292, "cents": 10548457155598, "bodies": 217,
         "suppliers": 42690, "period_min": "2011-Q1", "period_max": "2026-Q2"}

    GET https://statespend.ie/api/meta
        {"profile": {"ingested_at": "...", ...}, ...}

The API sends no CORS headers, so the browser cannot read it from tpsa.ie. This
script closes the gap at build time instead: it fetches the totals and rewrites
the figures in place inside the elements carrying a `data-statespend` attribute,
so the deployed HTML always ships the numbers as they stood at the last build.
The page needs no JavaScript for the figures to be right, and nothing on it
depends on statespend.ie being up when a visitor arrives.

`.github/workflows/build-deploy.yml` runs this before every build and on a
weekly schedule. Run it by hand any time:

    python3 scripts/statespend_stats.py            # rewrite the figures
    python3 scripts/statespend_stats.py --check    # report drift, change nothing

Nothing is written unless every figure passes the sanity floors below, so an
outage, a redesign of the API or a truncated response leaves the previous
(correct) numbers in place rather than publishing zeros.

The elements this script owns are rewritten wholesale from the templates in
FIELDS — edit the markup here, not in index.html, or the next run will
overwrite it. Adding a figure means adding a FIELDS entry plus a matching
`data-statespend` element in the page.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "site" / "problem-solving" / "index.html"

API_BASE = "https://statespend.ie"
SUMMARY_URL = f"{API_BASE}/api/summary"
META_URL = f"{API_BASE}/api/meta"
SITE_URL = f"{API_BASE}/"

TIMEOUT = 20
ATTEMPTS = 3
USER_AGENT = "tpsa.ie-build/1.0 (+https://tpsa.ie/problem-solving)"

# Floors that a plausible response clears comfortably. The dataset only ever
# grows, so anything under these means the response is wrong, not that Irish
# public spending collapsed.
MIN_CENTS = 1_000_000_000_000  # €10bn
MIN_RECORDS = 100_000
MIN_BODIES = 50

PERIOD_RE = re.compile(r"^(\d{4})-Q([1-4])$")

MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


# --------------------------------------------------------------------------- #
# fetching
# --------------------------------------------------------------------------- #

def fetch_json(url: str) -> dict:
    """GET one JSON document, retrying briefly on transport errors."""
    last: Exception | None = None
    for attempt in range(1, ATTEMPTS + 1):
        request = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError, RuntimeError) as exc:
            last = exc
            if attempt < ATTEMPTS:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"could not fetch {url}: {last}")


def positive_int(payload: dict, key: str) -> int:
    """Read one figure, tolerating the API's habit of quoting large integers."""
    if key not in payload:
        raise ValueError(f"response is missing {key!r}")
    try:
        value = int(str(payload[key]).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{key!r} is not a whole number: {payload[key]!r}")
    if value <= 0:
        raise ValueError(f"{key!r} is not positive: {value}")
    return value


def load_totals() -> dict:
    """Fetch and validate everything the page needs."""
    summary = fetch_json(SUMMARY_URL)
    cents = positive_int(summary, "cents")
    records = positive_int(summary, "records")
    bodies = positive_int(summary, "bodies")

    if cents < MIN_CENTS:
        raise ValueError(f"total of {cents} cents is below the €10bn floor")
    if records < MIN_RECORDS:
        raise ValueError(f"{records} records is below the {MIN_RECORDS} floor")
    if bodies < MIN_BODIES:
        raise ValueError(f"{bodies} bodies is below the {MIN_BODIES} floor")

    period_max = str(summary.get("period_max", ""))
    if not PERIOD_RE.match(period_max):
        raise ValueError(f"unusable period_max: {period_max!r}")

    # The ingest timestamp is nice to show but not worth failing over: fall back
    # to the build date if /api/meta ever stops carrying it.
    try:
        profile = fetch_json(META_URL).get("profile") or {}
        synced = parse_timestamp(str(profile.get("ingested_at", "")))
    except (RuntimeError, ValueError):
        synced = None

    return {
        "cents": cents,
        "records": records,
        "bodies": bodies,
        "period_max": period_max,
        "synced": synced or datetime.now(timezone.utc),
    }


def parse_timestamp(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# formatting
# --------------------------------------------------------------------------- #
# Every figure is rounded *down*. The tiles carry a "+" so a floored count still
# reads truthfully, and a spending total that trails the live one by a rounding
# step is always the safer claim to put on a page about public money.

def floor_to(value: int, step: int) -> int:
    return (value // step) * step


def billions(cents: int) -> str:
    """1054845715559 -> '105.4' (euro billions, one decimal, truncated)."""
    return f"{math.floor(cents / 1e11 * 10) / 10:.1f}"


def compact_count(n: int) -> tuple[str, str, int]:
    """598292 -> ('590', 'K+', 0); 1234567 -> ('1.2', 'm+', 1)."""
    if n >= 1_000_000:
        return f"{math.floor(n / 100_000) / 10:.1f}", "m+", 1
    return str(floor_to(n, 10_000) // 1_000), "K+", 0


def prose_count(n: int) -> str:
    """598292 -> '590,000+'."""
    step = 100_000 if n >= 1_000_000 else 10_000
    return f"{floor_to(n, step):,}+"


def format_period(period_max: str) -> str:
    """'2026-Q2' -> '2026 Q2'."""
    year, quarter = PERIOD_RE.match(period_max).groups()
    return f"{year} Q{quarter}"


def format_date(moment: datetime) -> str:
    """'28 July 2026', in the site's Irish English."""
    moment = moment.astimezone(timezone.utc)
    return f"{moment.day} {MONTHS[moment.month - 1]} {moment.year}"


# --------------------------------------------------------------------------- #
# the figures the page carries
# --------------------------------------------------------------------------- #
# key -> (tag, attributes, inner HTML). `data-count-to` and friends drive the
# scroll-in animation in js/counters.js; the inner text is the same value, so
# the figure is correct with JavaScript switched off.

def build_fields(totals: dict) -> dict[str, tuple[str, dict, str]]:
    spend = billions(totals["cents"])
    count, count_suffix, count_decimals = compact_count(totals["records"])
    bodies = str(floor_to(totals["bodies"], 10))

    tiles = {
        "spend": ("span", {
            "data-count-to": spend,
            "data-decimals": "1",
            "data-prefix": "€",
            "data-suffix": "bn",
        }, f"€{spend}bn"),
        "records": ("span", {
            "data-count-to": count,
            **({"data-decimals": str(count_decimals)} if count_decimals else {}),
            "data-suffix": count_suffix,
        }, f"{count}{count_suffix}"),
        "bodies": ("span", {
            "data-count-to": bodies,
            "data-suffix": "+",
        }, f"{bodies}+"),
    }

    prose = {
        "spend-prose": ("span", {}, f"€{spend} billion"),
        "records-prose": ("span", {}, prose_count(totals["records"])),
        "bodies-prose": ("span", {}, bodies),
        "bodies-short": ("span", {}, f"{bodies}+"),
    }

    source = {
        "asof": ("p", {"class": "stats__src"},
                 "Public-finance figures from "
                 f'<a href="{SITE_URL}" target="_blank" rel="noopener noreferrer">statespend.ie</a>'
                 f" — published records to {format_period(totals['period_max'])},"
                 f" synced {format_date(totals['synced'])}."),
    }

    return {**tiles, **prose, **source}


def render(key: str, tag: str, attrs: dict, inner: str) -> str:
    opening = f'<{tag} data-statespend="{key}"'
    for name, value in attrs.items():
        opening += f' {name}="{value}"'
    return f"{opening}>{inner}</{tag}>"


def element_re(tag: str, key: str) -> re.Pattern:
    """Match one marked element, opening tag to closing tag.

    The closing quote in the attribute match keeps `bodies` from also matching
    `bodies-prose`. The inner match is non-greedy, so a marked element must not
    nest another element of the same tag — none of the figures do, and none
    should: they hold a number and nothing else.
    """
    return re.compile(
        rf'<{tag}\b[^>]*\bdata-statespend="{re.escape(key)}"[^>]*>.*?</{tag}>',
        re.DOTALL,
    )


def apply_fields(html: str, fields: dict) -> tuple[str, list[str], list[str]]:
    """Rewrite every marked element. Returns (html, stale keys, missing keys)."""
    stale: list[str] = []
    missing: list[str] = []

    for key, (tag, attrs, inner) in fields.items():
        replacement = render(key, tag, attrs, inner)
        found = element_re(tag, key).findall(html)
        if not found:
            missing.append(key)
            continue
        if any(match != replacement for match in found):
            stale.append(key)
            html = element_re(tag, key).sub(lambda _: replacement, html)

    return html, stale, missing


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

def display_path(path: Path) -> str:
    """Repo-relative where possible, so the CI log stays readable."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report drift and exit 1 if the page is stale; write nothing")
    parser.add_argument("--file", type=Path, default=TARGET,
                        help=f"page to rewrite (default: {display_path(TARGET)})")
    args = parser.parse_args(argv)

    try:
        totals = load_totals()
    except (RuntimeError, ValueError) as exc:
        print(f"statespend: leaving the figures alone — {exc}", file=sys.stderr)
        return 2

    print(f"statespend: €{totals['cents'] / 1e11:.2f}bn across "
          f"{totals['records']:,} records from {totals['bodies']} bodies, "
          f"to {totals['period_max']}")

    if not args.file.is_file():
        print(f"statespend: no such file: {args.file}", file=sys.stderr)
        return 2

    old_html = args.file.read_text(encoding="utf-8")
    new_html, stale, missing = apply_fields(old_html, build_fields(totals))

    if missing:
        print("statespend: no data-statespend element for: " + ", ".join(missing),
              file=sys.stderr)
        return 2

    if not stale:
        print("statespend: page already current")
        return 0

    if args.check:
        print("statespend: stale figures: " + ", ".join(stale), file=sys.stderr)
        return 1

    args.file.write_text(new_html, encoding="utf-8")
    print(f"statespend: updated {', '.join(stale)} in {display_path(args.file)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
