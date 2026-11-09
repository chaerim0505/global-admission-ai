
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag


ADMISSION_KEYWORDS = (
    "admission",
    "apply",
    "application",
    "graduate",
    "tuition",
    "scholarship",
    "입학",
    "모집",
    "장학",
    "등록금",
)

EXCLUDED_PATHS = (
    "/news.do",
    "/notice.do",
    "/notice_scholarship.do",
)

def fetch_official_page(url: str) -> dict:
    """Fetch and extract text from a university webpage."""

    if not url.startswith("https://"):
        raise ValueError("HTTPS URL is required")

    response = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "GlobalAdmissionAI/0.1"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup(["script", "style", "nav", "footer"]):
        element.decompose()

    title = (
        soup.title.get_text(strip=True)
        if soup.title
        else ""
    )

    content = soup.get_text(
        separator=" ",
        strip=True,
    )

    return {
        "sourceUrl": response.url,
        "pageTitle": title,
        "content": content[:15000],
        "status": "retrieved",
    }


def discover_admission_links(
    source_url: str,
    allowed_domain: str,
) -> list[dict]:
    """Discover potential admission links on a university webpage."""

    if not source_url.startswith("https://"):
        raise ValueError("HTTPS URL is required")

    response = requests.get(
        source_url,
        timeout=15,
        headers={"User-Agent": "GlobalAdmissionAI/0.1"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    seen = set()

    domain = allowed_domain.lower().strip(".")

    for anchor in soup.find_all("a", href=True):
        text = anchor.get_text(" ", strip=True)

        url = urljoin(
            response.url,
            anchor["href"],
        )

        # Remove URL fragments such as #711
        url, _ = urldefrag(url)

        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        # Only allow HTTPS links
        if parsed.scheme != "https":
            continue

        # Only allow the university's specified domain
        if hostname != domain and not hostname.endswith(
            "." + domain
        ):
            continue

        # Exclude unrelated news and announcements
        if any(
            path in parsed.path.lower()
            for path in EXCLUDED_PATHS
        ):
            continue

        # Avoid long news article titles
        if len(text) > 120:
            continue

        searchable = (
            text + " " + parsed.path
        ).lower()

        # Check admission-related keywords
        if not any(
            word in searchable
            for word in ADMISSION_KEYWORDS
        ):
            continue

        # Avoid duplicate URLs
        if url in seen:
            continue

        seen.add(url)

        results.append({
            "title": text or parsed.path,
            "sourceUrl": url,
            "verificationStatus": "needs_check",
        })

    return results
