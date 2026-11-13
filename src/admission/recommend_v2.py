"""Recommendation rules added on 2026-11-14 (SPEC F06-F09, AC21-AC27).

Implemented step by step against tests/harness/recommend_v2_cases.yaml.
Step 5: detect_language (AC21).
"""

from __future__ import annotations

import re

HANGUL = re.compile(r"[가-힣ㄱ-ㆎ]")
LATIN = re.compile(r"[A-Za-z]")


def _language_of(text: str) -> str | None:
    """Return "ko" or "en" for one message, or None when it has no letters (e.g. "4.5", "KR")."""
    hangul = len(HANGUL.findall(text or ""))
    latin = len(LATIN.findall(text or ""))
    if hangul == 0 and latin <= 3:  # numbers or short codes like "KR", "MM" say nothing about language
        return None
    return "ko" if hangul >= 0.3 * (hangul + latin) else "en"


def detect_language(messages: list[str], default: str = "en") -> str:
    """Language of the user's latest message that has words (AC21).

    Mixed history follows the last message; a short answer such as "4.5" or "KR"
    keeps the language of the message before it.
    """
    for message in reversed(messages):
        language = _language_of(message)
        if language:
            return language
    return default


# ---------------------------------------------------------------------------
# Step 6: difficulty tiers (AC25), budget filter (AC24), five distinct universities (AC22)
# ---------------------------------------------------------------------------

from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEGREE_ALIASES = {"bachelor": "undergraduate", "undergraduate": "undergraduate",
                  "master": "master", "doctoral": "phd", "phd": "phd"}
SOURCE_RANK = {"team_verified": 0, "official_dataset": 1, "web_verified": 2}
BUDGET_RANK = {"within": 0, None: 0, "needs_check": 1}
TIER_ORDER = {"match": 0, "reach": 1, "safety": 2, "unknown": 3}
PERIOD_TO_YEAR = {"year": 1.0, "semester": 2.0}


def load_rules() -> dict:
    return yaml.safe_load((ROOT / "config" / "tiers.yaml").read_text(encoding="utf-8"))


def load_rates() -> dict[str, float]:
    return yaml.safe_load((ROOT / "config" / "fx_rates.yaml").read_text(encoding="utf-8"))["to_usd"]


def applicant_score(applicant: dict) -> float | None:
    score, maximum = applicant.get("academicScore"), applicant.get("maximumScore")
    if score is None or not maximum:
        return None
    return 100.0 * float(score) / float(maximum)


def tier_for(applicant: dict, university_index: float | None, rules: dict) -> str:
    """reach / match / safety from the gap between university index and applicant score (AC25)."""
    score = applicant_score(applicant)
    if score is None or university_index is None:
        return "unknown"
    gap = float(university_index) - score
    if gap > rules["reach_if_gap_above"]:
        return "reach"
    if gap < rules["safety_if_gap_below"]:
        return "safety"
    return "match"


def _yearly_usd(amount, currency, period, rates) -> float | None:
    if amount is None or currency not in rates or period not in PERIOD_TO_YEAR:
        return None
    return float(amount) * rates[currency] * PERIOD_TO_YEAR[period]


def budget_fit(program: dict, context: dict, rates: dict) -> str | None:
    """within / over / needs_check; None when the user gave no budget (AC24)."""
    if not context.get("maximumTuition"):
        return None
    limit = _yearly_usd(context["maximumTuition"], context.get("tuitionCurrency"),
                        context.get("tuitionPeriod") or "year", rates)
    tuition = program.get("tuition") or {}
    cost = _yearly_usd(tuition.get("amount"), tuition.get("currency"), tuition.get("period"), rates)
    if limit is None or cost is None:
        return "needs_check"
    return "within" if cost <= limit else "over"


def _matches(program: dict, context: dict) -> bool:
    countries = context.get("preferredCountries") or []
    if countries and program["country"] not in countries:
        return False
    wanted = context.get("applicantType")
    if wanted and DEGREE_ALIASES.get(program["degreeLevel"]) != DEGREE_ALIASES.get(wanted):
        return False
    fields = set(context.get("engineeringFields") or [])
    return not fields or bool(fields & set(program.get("engineeringFields") or []))


def _university_id(program: dict) -> str:
    return program.get("universityKey") or program.get("universityId") or program["universityName"]


def _index(program: dict):
    value = program.get("difficultyPercentile", program.get("universityIndex"))
    return None if value is None else float(value)


def recommend(context: dict, catalogue: list[dict], rates: dict | None = None,
              web_results: list[dict] | None = None, rules: dict | None = None) -> dict:
    """Pick up to five distinct universities that meet every hard condition (AC22-AC25, AC27)."""
    rates = rates or load_rates()
    rules = rules or load_rules()
    wanted = rules.get("results_per_request", 5)
    score = applicant_score(context)

    best: dict[str, dict] = {}
    excluded_over_budget = 0
    requested = set(context.get("engineeringFields") or [])

    def preference(p: dict):
        # Within a university prefer: trusted source, a programme whose MAIN field is the one asked
        # for (EE over Computer Engineering when EE is asked), then the most specific programme.
        fields = p.get("engineeringFields") or []
        primary_hit = 0 if (not requested or (fields and fields[0] in requested)) else 1
        return (SOURCE_RANK.get(p.get("source"), 3), primary_hit, len(fields), p["programId"])

    for program in sorted(catalogue, key=preference):
        if not _matches(program, context):
            continue
        fit = budget_fit(program, context, rates)
        if fit == "over":
            excluded_over_budget += 1
            continue
        uid = _university_id(program)
        if uid in best:  # one programme per university; the first is the most trusted source
            continue
        index = _index(program)
        best[uid] = {**program, "source": program.get("source") or "official_dataset",
                     "budgetFit": fit, "difficultyPercentile": index,
                     "admissionTier": tier_for(context, index, rules) if score is not None else None}

    candidates = list(best.values())

    def closeness(item: dict) -> float:
        if score is None or item["difficultyPercentile"] is None:
            return 999.0
        return abs(item["difficultyPercentile"] - score)

    def base_key(item: dict):
        return (BUDGET_RANK.get(item["budgetFit"], 1), SOURCE_RANK.get(item["source"], 3))

    if score is None:
        # No grade: most selective first, so the list is not arbitrary.
        candidates.sort(key=lambda c: (*base_key(c), -(c["difficultyPercentile"] or -1), c["programId"]))
        picked = candidates[:wanted]
    else:
        candidates.sort(key=lambda c: (*base_key(c), closeness(c), c["programId"]))
        picked = _pick_mix(candidates, rules.get("mix_when_possible", {}), wanted)
        picked.sort(key=lambda c: (BUDGET_RANK.get(c["budgetFit"], 1), TIER_ORDER[c["admissionTier"]],
                                   closeness(c), c["programId"]))

    if len(picked) < wanted and web_results:
        picked += _web_fill(web_results, context, picked, best, wanted - len(picked), score)

    shortfall = None
    if len(picked) < wanted:
        shortfall = (f"Only {len(picked)} universities meet every condition "
                     f"(country, degree, field{', budget' if context.get('maximumTuition') else ''}). "
                     "Conditions were not relaxed.")
        if excluded_over_budget:
            shortfall += f" {excluded_over_budget} programmes were over budget."
    return {"results": picked, "shortfallReason": shortfall}


def _pick_mix(ordered: list[dict], mix: dict, wanted: int) -> list[dict]:
    """Take reach/match/safety counts from the best-ordered candidates, then fill (AC25)."""
    picked: list[dict] = []
    for tier in ("match", "reach", "safety"):
        pool = [c for c in ordered if c["admissionTier"] == tier and c not in picked]
        picked += pool[: mix.get(tier, 0)]
    for c in ordered:
        if len(picked) >= wanted:
            break
        if c not in picked:
            picked.append(c)
    return picked[:wanted]


def load_catalogue() -> list[dict]:
    import json
    path = ROOT / "data" / "catalogue" / "programs_unified.json"
    return json.loads(path.read_text(encoding="utf-8"))["programs"]


# ---------------------------------------------------------------------------
# Step 7: web results only when the link opens and the domain is the university's (AC19, AC23)
# ---------------------------------------------------------------------------

from functools import lru_cache  # noqa: E402
from urllib.parse import urlparse  # noqa: E402


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _domain_matches(url: str, domains: list[str]) -> bool:
    host = _host(url)
    for domain in domains or []:
        domain = domain.lower().removeprefix("www.")
        if domain and (host == domain or host.endswith("." + domain)):
            return True
    return False


def filter_web_results(items: list[dict], probe=None, domains_for=None) -> list[dict]:
    """Keep a web result only if its https link answers 200 and sits on the university's ROR domain.

    `probe(url) -> status code` and `domains_for(name, country) -> [domains]` are injected so tests
    stay offline; items may also carry `http_status` / `ror_domains` already (golden cases).
    """
    kept = []
    for item in items:
        url = str(item.get("sourceUrl") or "")
        if not url.startswith("https://"):
            continue
        status = item.get("http_status")
        if status is None and probe is not None:
            status = probe(url)
        domains = item.get("ror_domains")
        if domains is None and domains_for is not None:
            domains = domains_for(item.get("universityName", ""), item.get("country"))
        if status == 200 and _domain_matches(url, domains or []):
            kept.append({**item, "source": "web_verified", "officialDomain": _host(url)})
    return kept


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", "", (name or "").lower().replace("the ", ""))


def _web_fill(web_results, context, picked, best, room, score) -> list[dict]:
    countries = set(context.get("preferredCountries") or [])
    taken = {_norm_name(p["universityName"]) for p in best.values()} | {_norm_name(p.get("universityNameEnglish") or "") for p in best.values()}
    taken |= {_host(p.get("sourceUrl") or "") for p in picked}
    added = []
    for item in web_results:
        if len(added) >= room:
            break
        if item.get("source") != "web_verified" or (countries and item.get("country") not in countries):
            continue
        key = _norm_name(item.get("universityName", ""))
        if not key or key in taken or _host(item["sourceUrl"]) in taken:
            continue
        taken |= {key, _host(item["sourceUrl"])}
        added.append({
            **item,
            "programId": item.get("programId") or "web_" + _host(item["sourceUrl"]) + "_" + _norm_name(item.get("programName", ""))[:30],
            "degreeLevel": DEGREE_ALIASES.get(context.get("applicantType"), context.get("applicantType")),
            "engineeringFields": item.get("engineeringFields") or list(context.get("engineeringFields") or []),
            "universityKey": "web:" + _host(item["sourceUrl"]),
            "difficultyPercentile": None,
            "budgetFit": "needs_check" if context.get("maximumTuition") else None,
            "admissionTier": "unknown" if score is not None else None,
            "verificationStatus": "needs_check",
        })
    return added


# Live helpers used by the app (not by tests) -------------------------------

def http_status(url: str, timeout: float = 6.0) -> int | None:
    import requests
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        if response.status_code in (403, 405):  # some sites refuse HEAD
            response = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
        return response.status_code
    except Exception:
        return None


@lru_cache(maxsize=512)
def official_domains(name: str, country: str | None) -> tuple[str, ...]:
    """University domains: first from our catalogue, then from the ROR registry."""
    key = _norm_name(name)
    for p in _catalogue_cached():
        if p.get("officialDomain") and key in {_norm_name(p["universityName"]), _norm_name(p.get("universityNameEnglish") or "")}:
            return (p["officialDomain"],)
    import requests
    try:
        data = requests.get("https://api.ror.org/v2/organizations", params={"query": name}, timeout=8).json()
    except Exception:
        return ()
    domains: list[str] = []
    for org in data.get("items", [])[:3]:
        codes = {loc.get("geonames_details", {}).get("country_code") for loc in org.get("locations", [])}
        if country and country not in codes and not (country == "GB" and "UK" in codes):
            continue
        domains += org.get("domains", [])
        domains += [_host(link.get("value", "")) for link in org.get("links", []) if link.get("type") == "website"]
    return tuple(d for d in domains if d)


@lru_cache(maxsize=1)
def _catalogue_cached() -> tuple:
    return tuple(load_catalogue())


def web_results_from_gemini(raw_items: list[dict], context: dict) -> list[dict]:
    """Shape Gemini exploration items and keep only verified ones (live network)."""
    shaped = [{**i, "country": i.get("country") or (context.get("preferredCountries") or [None])[0]} for i in raw_items]
    return filter_web_results(shaped, probe=http_status, domains_for=lambda n, c: list(official_domains(n, c)))
