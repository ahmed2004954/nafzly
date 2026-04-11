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


def fetch_projects() -> list[dict]:
    """
    Returns a list of project dicts, newest first.
    Assumption from plan: keep returned fields aligned to the implementation
    block (`id`, `title`, `url`, `raw`) even though the prose mentions more.
    """
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

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
