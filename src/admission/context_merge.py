from admission.schemas import RequestContext


COUNTRY_LABELS = {
    "CA": {"ca", "캐나다", "canada"},
}


def merge_context(
    previous: RequestContext,
    update: RequestContext,
) -> RequestContext:
    merged = previous.model_dump()

    for field, value in update.model_dump().items():
        if value is not None and field != "outOfScopeRequests":
            merged[field] = value

    remaining = list(previous.outOfScopeRequests or [])

    if update.preferredCountries is not None:
        old_country_labels = set()

        for country in previous.preferredCountries or []:
            code = country.strip().upper()
            old_country_labels.add(code.casefold())
            old_country_labels.update(COUNTRY_LABELS.get(code, set()))

        remaining = [
            item
            for item in remaining
            if item.strip().casefold() not in old_country_labels
        ]

    # Keep unresolved non-country requests and add new scope flags.
    combined = remaining + list(update.outOfScopeRequests or [])
    merged["outOfScopeRequests"] = list(dict.fromkeys(combined)) or None

    return RequestContext.model_validate(merged)