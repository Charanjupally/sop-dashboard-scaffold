"""
Trigger rule engine.

Each rule is a pure function: (data_dict) -> TriggerResult | None.
The engine runs all rules, collects results, and returns fired triggers
in priority order.

Adding a new trigger: add a function decorated with @rule() below.
No other files need to change.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Types ─────────────────────────────────────────────


@dataclass
class TriggerResult:
    id: str                      # e.g. "btc_drop"
    sop_name: str                # SOP to execute
    severity: str                # "critical" | "warning" | "info"
    summary: str                 # One-line message for the action queue
    source: str                  # API source label
    sla_hours: int               # SLA in hours
    assignee: str = ""
    extra: dict = field(default_factory=dict)


# ── Registry ──────────────────────────────────────────

_rules: list[Callable] = []


def rule(fn: Callable) -> Callable:
    _rules.append(fn)
    return fn


async def evaluate_all(data: dict) -> list[TriggerResult]:
    """Run every registered rule against the aggregated data snapshot."""
    results: list[TriggerResult] = []
    for fn in _rules:
        try:
            result = fn(data)
            if result is not None:
                results.append(result)
        except Exception as exc:
            logger.warning("Trigger rule %s failed: %s", fn.__name__, exc)

    # Sort: critical first, then warning, then info
    order = {"critical": 0, "warning": 1, "info": 2}
    results.sort(key=lambda r: order.get(r.severity, 9))
    return results


# ── Rules ─────────────────────────────────────────────

@rule
def btc_drop(data: dict) -> TriggerResult | None:
    pct = data.get("crypto", {}).get("btc_change_24h", 0.0)
    if pct <= -settings.TRIGGER_BTC_DROP_PCT:
        return TriggerResult(
            id="btc_drop",
            sop_name="Treasury Reserve Review SOP",
            severity="critical",
            summary=f"BTC dropped {abs(pct):.1f}% in 24 h (threshold: {settings.TRIGGER_BTC_DROP_PCT}%)",
            source="CoinGecko · A1",
            sla_hours=12,
            assignee="Finance Lead",
            extra={"btc_price": data["crypto"].get("btc_price"), "change_pct": pct},
        )
    return None


@rule
def eth_drop(data: dict) -> TriggerResult | None:
    pct = data.get("crypto", {}).get("eth_change_24h", 0.0)
    if pct <= -settings.TRIGGER_ETH_DROP_PCT:
        return TriggerResult(
            id="eth_drop",
            sop_name="Treasury Reserve Review SOP",
            severity="warning",
            summary=f"ETH dropped {abs(pct):.1f}% in 24 h (threshold: {settings.TRIGGER_ETH_DROP_PCT}%)",
            source="CoinGecko · A1",
            sla_hours=24,
            assignee="Finance Lead",
        )
    return None


@rule
def fx_move(data: dict) -> TriggerResult | None:
    pct = abs(data.get("fx", {}).get("usd_inr_change_wow", 0.0))
    if pct >= settings.TRIGGER_FX_MOVE_PCT:
        return TriggerResult(
            id="fx_move",
            sop_name="Cross-border Invoicing SOP",
            severity="warning",
            summary=f"USD/INR moved {pct:.1f}% WoW (threshold: {settings.TRIGGER_FX_MOVE_PCT}%)",
            source="Frankfurter FX · A2",
            sla_hours=24,
            assignee="Finance Lead",
        )
    return None


@rule
def cpi_spike(data: dict) -> TriggerResult | None:
    mom = data.get("macro", {}).get("cpi_mom", 0.0)
    if mom >= settings.TRIGGER_CPI_MOM_PCT:
        return TriggerResult(
            id="cpi_spike",
            sop_name="Pricing Review SOP",
            severity="warning",
            summary=f"CPI MoM = {mom:.2f}% — exceeds {settings.TRIGGER_CPI_MOM_PCT}% threshold",
            source="FRED · B4",
            sla_hours=48,
            assignee="Strategy Lead",
        )
    return None


@rule
def aqi_critical(data: dict) -> TriggerResult | None:
    cities = data.get("aqi", {}).get("cities", [])
    bad = [c for c in cities if c.get("aqi", 0) >= settings.TRIGGER_AQI_CRITICAL]
    if bad:
        names = ", ".join(c["city"] for c in bad)
        return TriggerResult(
            id="aqi_critical",
            sop_name="WFH Advisory SOP",
            severity="critical",
            summary=f"Critical AQI in {names} — WFH advisory required",
            source="AQICN · B10",
            sla_hours=4,
            assignee="HR Lead",
            extra={"cities": bad},
        )
    return None


@rule
def aqi_warning(data: dict) -> TriggerResult | None:
    cities = data.get("aqi", {}).get("cities", [])
    bad = [
        c for c in cities
        if settings.TRIGGER_AQI_WARN <= c.get("aqi", 0) < settings.TRIGGER_AQI_CRITICAL
    ]
    if bad:
        names = ", ".join(c["city"] for c in bad)
        return TriggerResult(
            id="aqi_warning",
            sop_name="WFH Advisory SOP",
            severity="warning",
            summary=f"Elevated AQI in {names}",
            source="Open-Meteo · A6",
            sla_hours=24,
            assignee="HR Lead",
            extra={"cities": bad},
        )
    return None


@rule
def utilization_cap(data: dict) -> TriggerResult | None:
    members = data.get("hr", {}).get("members", [])
    over = [m for m in members if m.get("utilization_pct", 0) >= settings.TRIGGER_UTILIZATION_PCT]
    if over:
        names = ", ".join(m["name"] for m in over)
        return TriggerResult(
            id="utilization_cap",
            sop_name="Capacity Reallocation SOP",
            severity="warning",
            summary=f"{names} at or above {settings.TRIGGER_UTILIZATION_PCT}% utilization",
            source="Clockify · B6",
            sla_hours=48,
            assignee="Ops Lead",
            extra={"members": over},
        )
    return None


@rule
def sec_filing(data: dict) -> TriggerResult | None:
    filings = data.get("news", {}).get("sec_filings", [])
    new_8k = [f for f in filings if f.get("form") == "8-K"]
    if new_8k:
        company = new_8k[0].get("company", "Unknown")
        return TriggerResult(
            id="sec_8k",
            sop_name="Material Event Memo SOP",
            severity="critical",
            summary=f"New 8-K filing: {company}",
            source="SEC EDGAR · C1",
            sla_hours=24,
            assignee="Ops Lead",
            extra={"filings": new_8k[:3]},
        )
    return None


@rule
def sop_stale(data: dict) -> TriggerResult | None:
    stale = data.get("sop", {}).get("stale_sops", [])
    if stale:
        titles = ", ".join(s["title"] for s in stale[:3])
        return TriggerResult(
            id="sop_stale",
            sop_name="SOP Refresh Workflow",
            severity="info",
            summary=f"{len(stale)} SOP(s) not reviewed in {settings.TRIGGER_SOP_STALE_DAYS} days: {titles}",
            source="Notion · B7",
            sla_hours=168,  # 7 days
            assignee="Ops Lead",
            extra={"stale_sops": stale},
        )
    return None


@rule
def alpha_move(data: dict) -> TriggerResult | None:
    alpha = data.get("alpha_vantage", {})
    pct = alpha.get("daily_change_pct", 0.0) or 0.0
    if abs(pct) >= 5:
        symbol = alpha.get("symbol", "Equity")
        return TriggerResult(
            id="alpha_move",
            sop_name="Investor Update SOP",
            severity="warning" if pct > 0 else "critical",
            summary=f"{symbol} moved {pct:.1f}% today",
            source="Alpha Vantage · B1",
            sla_hours=24,
            assignee="Finance Lead",
            extra={"symbol": symbol, "daily_change_pct": pct},
        )
    return None


@rule
def wikipedia_spike(data: dict) -> TriggerResult | None:
    wiki = data.get("wikipedia", {})
    for series in wiki.get("series", []):
        points = series.get("points", [])
        if len(points) >= 5:
            last = points[-1].get("views", 0) or 0
            baseline = mean([p.get("views", 0) or 0 for p in points[-5:-1]])
            if baseline > 0 and last >= 2 * baseline:
                article = series.get("article", "Wikipedia article")
                return TriggerResult(
                    id=f"wiki_spike_{article.replace(' ', '_').lower()}",
                    sop_name="Reputation Audit SOP",
                    severity="warning",
                    summary=f"{article} pageviews are {last / baseline:.1f}x the rolling mean",
                    source="Wikipedia · C6",
                    sla_hours=72,
                    assignee="Comms Lead",
                    extra={"article": article, "latest": last, "baseline": baseline},
                )
    return None


@rule
def usajobs_posting(data: dict) -> TriggerResult | None:
    jobs = data.get("usajobs", {}).get("jobs", [])
    if jobs:
        job = jobs[0]
        return TriggerResult(
            id="usajobs_posting",
            sop_name="Capture Management SOP",
            severity="info",
            summary=f"New compliance posting: {job.get('title', 'Unknown')}",
            source="USAJOBS · B5",
            sla_hours=72,
            assignee="Ops Lead",
            extra={"job": job},
        )
    return None


@rule
def newsapi_sentiment(data: dict) -> TriggerResult | None:
    articles = data.get("newsapi", {}).get("articles", [])
    negative_terms = ("lawsuit", "probe", "fraud", "loss", "slump", "crash", "ban", "recall")
    for article in articles:
        haystack = " ".join(
            str(article.get(field, "")) for field in ("title", "description", "source")
        ).lower()
        if any(term in haystack for term in negative_terms):
            return TriggerResult(
                id="newsapi_sentiment",
                sop_name="Crisis Comms SOP",
                severity="warning",
                summary=f"Negative business headline detected: {article.get('title', 'headline')}",
                source="NewsAPI · B3",
                sla_hours=24,
                assignee="Comms Lead",
                extra={"article": article},
            )
    return None


@rule
def reddit_complaints(data: dict) -> TriggerResult | None:
    posts = data.get("reddit", {}).get("posts", [])
    if posts:
        complaint_terms = ("complaint", "angry", "problem", "issue", "refund", "support")
        score = 0
        for post in posts:
            title = str(post.get("title", "")).lower()
            if any(term in title for term in complaint_terms):
                score += 1
        if score >= 2:
            return TriggerResult(
                id="reddit_complaints",
                sop_name="Competitive Intelligence Briefing SOP",
                severity="info",
                summary="Complaint-related posts are spiking in r/Entrepreneur",
                source="Reddit · A8",
                sla_hours=48,
                assignee="Strategy Lead",
                extra={"matches": score, "posts": posts},
            )
    return None


@rule
def who_compliance(data: dict) -> TriggerResult | None:
    cells = data.get("who", {}).get("cells", [])
    if len(cells) >= 3:
        values = [c.get("value", 0) or 0 for c in cells if c.get("value") is not None]
        if values:
            latest = values[0]
            baseline = mean(values[1:]) if len(values) > 1 else latest
            if baseline > 0 and latest >= baseline:
                return TriggerResult(
                    id="who_compliance",
                    sop_name="Compliance Audit SOP",
                    severity="info",
                    summary=f"WHO mortality indicator is elevated in {cells[0].get('country', 'top country')}",
                    source="WHO · A5",
                    sla_hours=72,
                    assignee="Risk Lead",
                    extra={"top_cell": cells[0], "baseline": baseline},
                )
    return None
