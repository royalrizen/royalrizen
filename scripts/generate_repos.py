import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape
import random

USERNAME = "royalrizen"
LIMIT = max(1, min(int(os.getenv("REPO_LIMIT") or "5"), 10))

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


def fetch_repos():
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?sort=updated&direction=desc&per_page=100&type=owner"
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "royalrizen-repo-svg-generator"
    }

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=30) as response:
        repos = json.load(response)

    repos = [
        repo for repo in repos
        if repo.get("name", "").lower() != USERNAME.lower()
    ]

    return sorted(
        repos,
        key=lambda repo: (
            repo.get("pushed_at") or repo.get("updated_at") or ""
        ),
        reverse=True
    )


def esc(value):
    return escape(
        str(value or ""),
        {'"': "&quot;", "'": "&apos;"}
    )


def make_row(repo, y):
    name = esc(repo.get("name", "Untitled"))

    description = (
        repo.get("description") or "No description provided"
    ).strip()

    if len(description) > 55:
        description = description[:52].rstrip() + "..."

    description = esc(description)

    language = repo.get("language") or "Unspecified"
    icon = LANGUAGE_ICONS.get(language)

    stars = int(repo.get("stargazers_count") or 0)

    url = esc(
        repo.get("html_url")
        or f"https://github.com/{USERNAME}/{name}"
    )

    name_width = len(name) * 9.6
    desc_x = min(390, 35 + name_width + 14)

    if icon:
        language_element = (
            f'<image x="35" y="{y+18}" '
            f'width="17" height="17" '
            f'href="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/{icon}/{icon}-original.svg"/>'
        )
    else:
        language_element = (
            f'<text x="35" y="{y+24}" '
            f'class="roboto small" fill="#8b95a7">'
            f'{esc(language)}</text>'
        )

    parts = [
        f'<a href="{url}">',

        (
            f'<rect x="17" y="{y-20}" '
            f'width="616" height="76" rx="10" '
            f'fill="#151b25" stroke="#222c3a"/>'
        ),

        (
            f'<rect x="17" y="{y-20}" '
            f'width="3" height="76" rx="1.5" '
            f'fill="#FF6B81"/>'
        ),

        (
            f'<text x="35" y="{y}" '
            f'class="roboto repo">{name}</text>'
        ),

        (
            f'<text x="{desc_x:.1f}" y="{y}" '
            f'class="sans muted" font-size="11">'
            f'{description}</text>'
        ),

        language_element,

        (
            f'<text x="615" y="{y+24}" '
            f'text-anchor="end" '
            f'class="roboto small muted">'
            f'<tspan fill="#FFD43B">★</tspan> {stars}'
            f'</text>'
        ),

        '</a>'
    ]

    return "\n    ".join(parts)


def main():
    repos = fetch_repos()
    shown = random.sample(repos, min(LIMIT, len(repos)))

    height = 100 + len(shown) * 85 + 35

    script_dir = Path(__file__).resolve().parent
    template_path = script_dir / "card-template.svg"
    svg = template_path.read_text(encoding="utf-8")

    rows = "\n  ".join(
        make_row(repo, 108 + i * 85)
        for i, repo in enumerate(shown)
    )

    replacements = {
        "%%HEIGHT%%": str(height),
        "%%HEIGHT_MINUS2%%": str(height - 2),
        "%%COUNT%%": str(len(repos)),
        "%%ROWS%%": rows,
        "%%FOOTER_Y%%": str(height - 18)
    }

    for key, value in replacements.items():
        svg = svg.replace(key, value)

    output_path = script_dir / "repos.svg"
    output_path.write_text(svg, encoding="utf-8")

    print(
        f"Generated repos.svg: showing {len(shown)} "
        f"of {len(repos)} eligible repositories."
    )


if __name__ == "__main__":
    main()
