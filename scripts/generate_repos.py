import json
import os
import random
import urllib.request
import urllib.parse
import urllib.error
import html
import base64
from pathlib import Path

USERNAME = os.getenv("GITHUB_USERNAME", "royalrizen")
REPO_LIMIT = max(1, min(int(os.getenv("REPO_LIMIT") or "6"), 12))

BG = "#0d1117"
BORDER = "#21262d"
MUTED = "#8b949e"
ACCENT = "#2E8B57"

LANGUAGE_ICONS = {
    "Python": "python",
    "Java": "java",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "Kotlin": "kotlin",
    "C": "c",
    "C++": "cplusplus",
    "C#": "csharp",
    "Rust": "rust",
    "Go": "go",
    "Dart": "dart",
    "Ruby": "ruby",
    "PHP": "php",
    "Swift": "swift",
    "HTML": "html5",
    "CSS": "css3",
    "Shell": "bash",
    "D": "d",
    "Lua": "lua",
    "R": "r",
    "Scala": "scala",
    "Perl": "perl",
    "Haskell": "haskell",
    "Objective-C": "objectivec",
}

ICON_CACHE = {}


def fetch_repos():
    url = (
        "https://api.github.com/users/"
        + urllib.parse.quote(USERNAME, safe="")
        + "/repos?sort=updated&per_page=100"
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Repo-Cards",
    }

    # Use a token to increase the GitHub API rate limit.
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"
        print("Using authenticated GitHub API.")
    else:
        print(
            "WARNING: No GitHub token found. "
            "Using the unauthenticated API."
        )

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            repos = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        if error.code in (403, 429):
            remaining = error.headers.get("X-RateLimit-Remaining")
            reset = error.headers.get("X-RateLimit-Reset")

            message = (
                "GitHub API rate limit exceeded or access forbidden. "
                f"HTTP status: {error.code}. "
                f"Remaining requests: {remaining}. "
                f"Reset timestamp: {reset}. "
                "Check that GH_TOKEN is configured correctly."
            )

            raise RuntimeError(message) from error

        if error.code == 401:
            raise RuntimeError(
                "GitHub rejected the token. Check your GH_TOKEN secret."
            ) from error

        raise

    repos = [
        repo
        for repo in repos
        if repo["name"].casefold() != USERNAME.casefold()
    ]

    random.shuffle(repos)

    return repos[:REPO_LIMIT]


def esc(value):
    return html.escape(str(value or ""), quote=True)


def get_icon(language):
    icon = LANGUAGE_ICONS.get(language)

    if not icon:
        return None

    if icon in ICON_CACHE:
        return ICON_CACHE[icon]

    url = (
        "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/"
        f"{icon}/{icon}-original.svg"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "GitHub-Repo-Cards"},
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            svg_data = response.read()

        encoded = base64.b64encode(svg_data).decode("ascii")
        result = f"data:image/svg+xml;base64,{encoded}"

    except Exception as error:
        print(f"Could not load icon for {language}: {error}")
        result = None

    ICON_CACHE[icon] = result

    return result


def make_card(repo, x, y, width=300, height=76):
    name = esc(repo["name"])

    raw_description = (
        repo.get("description") or "No description available."
    )

    description = raw_description[:43]

    if len(raw_description) > 43:
        description += "..."

    description = esc(description)

    language_raw = repo.get("language") or "Other"
    language = esc(language_raw)

    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    url = esc(repo["html_url"])

    icon_data = get_icon(language_raw)

    if icon_data:
        language_icon = (
            f'<image x="{x + 12}" y="{y + 11}" '
            f'width="15" height="15" '
            f'href="{icon_data}" '
            f'xlink:href="{icon_data}"/>'
        )
        name_x = x + 33
    else:
        language_icon = ""
        name_x = x + 12

    return f"""
    <a xlink:href="{url}" target="_blank">
      <g>
        <rect
            x="{x}" y="{y}"
            width="{width}" height="{height}"
            rx="6"
            fill="{BG}"
            stroke="{BORDER}"
        />

        {language_icon}

        <text
            x="{name_x}" y="{y + 23}"
            fill="{ACCENT}"
            font-size="12"
            font-weight="bold"
            font-family="'Roboto Mono', monospace"
        >{name}</text>

        <text
            x="{x + 12}" y="{y + 42}"
            fill="{MUTED}"
            font-size="10"
        >{description}</text>

        <text
            x="{x + 12}" y="{y + 63}"
            fill="{MUTED}"
            font-size="9"
        >{language}</text>

        <text
            x="{x + width - 72}" y="{y + 63}"
            fill="{MUTED}"
            font-size="9"
        >
          <tspan fill="#e3b341">★</tspan> {stars}
          <tspan>  ⑂ {forks}</tspan>
        </text>
      </g>
    </a>
    """


def generate_svg(repos):
    columns = 2
    card_width = 300
    card_height = 76
    gap_x = 10
    gap_y = 10
    padding = 5

    rows = max(1, (len(repos) + columns - 1) // columns)

    width = (
        padding * 2
        + columns * card_width
        + (columns - 1) * gap_x
    )

    height = (
        padding * 2
        + rows * card_height
        + (rows - 1) * gap_y
    )

    cards = []

    for index, repo in enumerate(repos):
        col = index % columns
        row = index // columns

        x = padding + col * (card_width + gap_x)
        y = padding + row * (card_height + gap_y)

        cards.append(
            make_card(repo, x, y, card_width, card_height)
        )

    return f"""<svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
>
    {"".join(cards)}
</svg>
"""


def main():
    repos = fetch_repos()

    if not repos:
        raise RuntimeError(
            "No eligible public repositories found."
        )

    svg = generate_svg(repos)

    script_dir = Path(__file__).resolve().parent
    output_path = script_dir.parent / "repo_card.svg"

    output_path.write_text(svg, encoding="utf-8")

    print(
        f"Generated {output_path} with "
        f"{len(repos)} random repositories."
    )


if __name__ == "__main__":
    main()
