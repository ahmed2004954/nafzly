import requests
from bs4 import BeautifulSoup

URL = "https://nafezly.com/projects"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def _find_section_by_heading(soup: BeautifulSoup, heading_text: str):
    heading = soup.find(string=lambda s: s and heading_text in s)
    if not heading:
        return None

    section = heading.parent
    while section is not None:
        classes = section.get("class", [])
        if "main-nafez-box-styles" in classes:
            return section
        section = section.parent
    return None


def _extract_card_rows(card_section) -> dict[str, str]:
    details = {}
    if card_section is None:
        return details

    for row in card_section.select("div.col-12.row[style*='padding:4px 5px']"):
        columns = row.find_all("div", recursive=False)
        if len(columns) < 2:
            continue

        label = columns[0].get_text(" ", strip=True)
        value = columns[1].get_text(" ", strip=True)
        if label and value:
            details[label] = value

    return details


def fetch_projects() -> list[dict]:
    """
    Returns a list of project dicts, newest first.
    Assumption from plan: keep returned fields aligned to the implementation
    block (`id`, `title`, `url`, `raw`) even though the prose mentions more.
    """
    soup = _get_soup(URL)

    projects = []
    # NOTE: CSS selectors must be verified against live HTML on first run.
    # The selectors below are based on page inspection — adjust if needed.
    first_card = soup.select_one("a[href*='/project/']")
    # Debug helper requested by user; uncomment to inspect the first raw card HTML.
    # print(first_card.prettify() if first_card else "No matching card found")
    for card in soup.select("a[href*='/project/']"):
        href = card.get("href", "")
        if not href.startswith("http"):
            href = "https://nafezly.com" + href

        # Extract numeric project ID from URL slug
        # e.g. /project/44627-taqyimat-booking → "44627"
        try:
            project_id = href.split("/project/")[1].split("-")[0]
        except IndexError:
            continue

        title = card.get_text(strip=True)
        if not title or not project_id.isdigit():
            continue

        # Assumption from plan: keep find_parent() exactly as specified even though
        # richer project metadata currently appears higher in the live HTML card.
        parent = card.find_parent()
        raw_text = parent.get_text(" ", strip=True) if parent else ""

        projects.append(
            {
                "id": project_id,
                "title": title,
                "url": href,
                "raw": raw_text,
            }
        )

    # Deduplicate by ID (page may have duplicate links per card)
    seen = set()
    unique = []
    for project in projects:
        if project["id"] not in seen:
            seen.add(project["id"])
            unique.append(project)

    return unique


def enrich_project(project: dict) -> dict:
    """
    Fetches the project detail page and augments the project dict with:
    description, published_at, budget, applicants_count.
    """
    soup = _get_soup(project["url"])

    details_section = _find_section_by_heading(soup, "تفاصيل المشروع")
    description_node = details_section.select_one("h2") if details_section else None
    description = description_node.get_text(" ", strip=True) if description_node else ""

    card_section = _find_section_by_heading(soup, "بطاقة المشروع")
    card_details = _extract_card_rows(card_section)

    enriched = dict(project)
    enriched["description"] = description
    enriched["published_at"] = card_details.get("تاريخ النشر", "")
    enriched["budget"] = card_details.get("الميزانية", "")
    enriched["applicants_count"] = card_details.get("عدد المتقدمين", "")
    return enriched
