
import os
import json
import argparse
import textwrap

from pathlib import Path
from collections import Counter
from html import escape
from urllib.parse import quote
from urllib.request import Request, urlopen

# ================= CONFIGURATION =================

USERNAME = "helium900"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "profile"
OUTPUT.mkdir(parents=True, exist_ok=True)

OLIVE = "#333B22"
DARK = "#28301D"
GOLD = "#DBB957"
IVORY = "#F2EBD8"
MUTED = "#C8C7B7"

# ================= GITHUB API =================

def fetch(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "helium900-profile-generator",
    }

    token = os.getenv("GH_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        "https://api.github.com" + path,
        headers=headers
    )

    with urlopen(request, timeout=30) as response:
        return json.load(response)


# ================= SVG HELPERS =================

def text(x, y, value, size=15, color=IVORY,
         weight="normal", anchor="start"):

    return (
        f'<text x="{x}" y="{y}" '
        f'fill="{color}" '
        f'font-family="Arial, sans-serif" '
        f'font-size="{size}" '
        f'font-weight="{weight}" '
        f'text-anchor="{anchor}">'
        f'{escape(str(value))}'
        '</text>'
    )


def save_svg(filename, width, height, content):

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        '<defs>'
        '<linearGradient id="background" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{OLIVE}"/>'
        f'<stop offset="100%" stop-color="{DARK}"/>'
        '</linearGradient>'
        '</defs>'
        f'<rect x="1" y="1" '
        f'width="{width-2}" height="{height-2}" '
        f'rx="14" fill="url(#background)" '
        f'stroke="{GOLD}" stroke-opacity="0.65"/>'
        + content +
        '</svg>'
    )

    (OUTPUT / filename).write_text(
        svg,
        encoding="utf-8"
    )

    print("Generated:", filename)


# ================= FOLLOWER BADGE =================

def create_follower_badge(count):

    content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        'width="180" height="28" viewBox="0 0 180 28">'
        f'<rect width="180" height="28" rx="5" fill="{OLIVE}"/>'
        f'<path d="M118 0 H175 Q180 0 180 5 V23 '
        f'Q180 28 175 28 H118 Z" fill="{GOLD}"/>'
        + text(
            12, 19, "FOLLOWERS",
            size=12, color=IVORY, weight="bold"
        )
        + text(
            149, 19, count,
            size=14, color="#000000",
            weight="bold", anchor="middle"
        )
        + '</svg>'
    )

    (OUTPUT / "followers.svg").write_text(
        content,
        encoding="utf-8"
    )


# ================= GITHUB STATS =================

def create_stats(user, repos):

    metrics = [
        ("REPOSITORIES", user.get("public_repos", 0)),
        (
            "TOTAL STARS",
            sum(r.get("stargazers_count", 0) for r in repos)
        ),
        ("FOLLOWERS", user.get("followers", 0)),
        ("FOLLOWING", user.get("following", 0)),
    ]

    content = text(
        30, 43, "GitHub Stats",
        size=23, color=GOLD, weight="bold"
    )

    content += text(
        30, 69,
        "Public GitHub activity",
        size=13, color=MUTED
    )

    for index, (name, value) in enumerate(metrics):

        x = 25 + index * 183

        content += (
            f'<rect x="{x}" y="86" '
            f'width="173" height="105" rx="12" '
            f'fill="{DARK}" '
            f'stroke="{GOLD}" stroke-opacity="0.3"/>'
        )

        content += text(
            x + 15, 135, value,
            size=29, color=GOLD, weight="bold"
        )

        content += text(
            x + 15, 164, name,
            size=12, color=IVORY
        )

    save_svg("stats.svg", 760, 210, content)


# ================= LANGUAGE CHART =================

def create_languages(language_counts):

    total = sum(language_counts.values())

    content = text(
        30, 43,
        "Most Used Languages",
        size=23, color=GOLD, weight="bold"
    )

    content += text(
        30, 66,
        "GitHub repository language distribution",
        size=13, color=MUTED
    )

    if total == 0:
        content += text(
            30, 130,
            "No language data available.",
            size=16
        )

    for index, (language, amount) in enumerate(
        language_counts.most_common(6)
    ):

        col = index // 3
        row = index % 3

        x = 35 + col * 365
        y = 112 + row * 62

        percent = amount / total * 100

        content += text(
            x, y, language,
            size=15, weight="bold"
        )

        content += text(
            x + 320, y,
            f"{percent:.1f}%",
            size=14, color=GOLD, anchor="end"
        )

        content += (
            f'<rect x="{x}" y="{y+12}" '
            f'width="320" height="10" rx="5" '
            f'fill="{DARK}"/>'
        )

        content += (
            f'<rect x="{x}" y="{y+12}" '
            f'width="{320 * amount / total:.1f}" '
            f'height="10" rx="5" fill="{GOLD}"/>'
        )

    save_svg("languages.svg", 760, 310, content)


# ================= PROJECT CARDS =================

def create_project_card(repo, filename, title):

    description = (
        repo.get("description")
        or "View project on GitHub"
    )

    description = " ".join(description.split())

    lines = textwrap.wrap(
        description,
        width=37,
        break_long_words=False
    )[:2]

    content = text(
        22, 37, title,
        size=20, color=GOLD, weight="bold"
    )

    content += (
        f'<line x1="20" y1="51" '
        f'x2="328" y2="51" '
        f'stroke="{GOLD}" stroke-opacity="0.4"/>'
    )

    for index, line in enumerate(lines):
        content += text(
            22, 78 + index * 19,
            line, size=13
        )

    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    language = repo.get("language") or "Not specified"

    content += (
        f'<line x1="20" y1="120" '
        f'x2="328" y2="120" '
        f'stroke="{GOLD}" stroke-opacity="0.3"/>'
    )

    content += text(
        22, 144,
        f"Stars: {stars}    Forks: {forks}",
        size=12
    )

    content += text(
        22, 165,
        language,
        size=13, color=GOLD, weight="bold"
    )

    save_svg(filename, 348, 180, content)


# ================= MAIN =================

def main(placeholders=False):

    projects = [
        ("chat-application", "chat.svg", "Chat Application"),
        ("my-todo", "todo.svg", "Todo Application"),
        (
            "Currency-Converter",
            "currency.svg",
            "Currency Converter"
        ),
        ("portfolio", "portfolio.svg", "Portfolio"),
    ]

    if placeholders:

        user = {}
        repositories = []
        languages = Counter()

        create_follower_badge("—")

        # Preview cards without fabricated stats
        preview_stats = text(
            30, 43,
            "GitHub Stats",
            size=23, color=GOLD, weight="bold"
        )

        preview_stats += text(
            30, 115,
            "Awaiting first GitHub data refresh",
            size=17
        )

        save_svg(
            "stats.svg",
            760, 210, preview_stats
        )

        create_languages(languages)

        for _, filename, title in projects:
            create_project_card(
                {
                    "description": "Awaiting GitHub data refresh",
                    "stargazers_count": "—",
                    "forks_count": "—",
                    "language": "Not yet loaded",
                },
                filename,
                title
            )

        return

    user = fetch(f"/users/{USERNAME}")

    repositories = []

    for page in range(1, 11):

        batch = fetch(
            f"/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&type=owner"
        )

        repositories.extend(
            repo for repo in batch
            if not repo.get("fork", False)
        )

        if len(batch) < 100:
            break

    # Obtain real GitHub-detected language bytes
    languages = Counter()

    for repo in repositories:

        name = quote(repo["name"], safe="")

        data = fetch(
            f"/repos/{USERNAME}/{name}/languages"
        )

        languages.update(data)

    create_follower_badge(
        user.get("followers", 0)
    )

    create_stats(user, repositories)

    create_languages(languages)

    for repo_name, filename, title in projects:

        repo = next(
            (
                item for item in repositories
                if item["name"].lower() == repo_name.lower()
            ),
            None
        )

        if repo is None:
            repo = fetch(
                f"/repos/{USERNAME}/{quote(repo_name, safe='')}"
            )

        create_project_card(repo, filename, title)


# ================= RUN =================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--placeholders",
        action="store_true"
    )

    args = parser.parse_args()

    main(placeholders=args.placeholders)
