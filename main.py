import json
from pathlib import Path

from notifier import notify
from scraper import fetch_projects

DB_PATH = Path("seen_ids.json")
FIRST_RUN_N = 3


def load_seen() -> set[str]:
    if DB_PATH.exists():
        return set(json.loads(DB_PATH.read_text()))
    return set()


def save_seen(seen: set[str]):
    DB_PATH.write_text(json.dumps(sorted(seen), indent=2))


def main():
    seen = load_seen()
    projects = fetch_projects()

    if not projects:
        print("No projects found — check scraper selectors.")
        return

    is_first_run = len(seen) == 0

    if is_first_run:
        # First run: send last N projects, save ALL IDs.
        to_notify = projects[:FIRST_RUN_N]
        for project in to_notify:
            print(f"[FIRST RUN] Sending: {project['title']}")
            notify(project)
        # Mark ALL projects as seen so we don't re-send them next cycle.
        seen = {project["id"] for project in projects}
    else:
        # Normal run: only send truly new projects.
        new_projects = [project for project in projects if project["id"] not in seen]
        for project in reversed(new_projects):
            print(f"[NEW] Sending: {project['title']}")
            notify(project)
            seen.add(project["id"])

    save_seen(seen)
    print(f"Done. Seen IDs total: {len(seen)}")


if __name__ == "__main__":
    main()
