#!/usr/bin/env python3
"""Render the neofetch-style profile card (dark_mode.svg / light_mode.svg).

Static info lives in INFO below; live GitHub stats are fetched at render time.
Set GITHUB_TOKEN to include commit counts (the GitHub Action does this).
"""
import json
import os
import urllib.request
from datetime import date
from html import escape

USER = "ThatRaccoonGuy"
BIRTH_YEAR = 2008  # shown as "Uptime"
CREATED = date(2022, 7, 21)  # GitHub account creation, start of commit count
WIDTH = 58  # characters per info line

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "raccoon.txt")) as f:
    ASCII = f.read().strip("\n").split("\n")
# Light mode flips the brightness ramp so dark fur (the mask) stays dark
RAMP = ".:-=+*#%@"
INVERT = str.maketrans(RAMP, RAMP[::-1])

# (key, value) pairs; None = blank line, str = section header
INFO = [
    ("OS", "Omarchy 4 (Arch Linux), Hyprland"),
    ("Uptime", "{uptime}"),
    ("Kernel", "R&D Assistant"),
    ("IDE", "Neovim, VS Code"),
    None,
    ("Languages.Programming", "Python, C, C++, Java, Bash"),
    ("Languages.Computer", "HTML, JSON, YAML, Markdown"),
    ("Languages.Real", "English, Russian, Hebrew"),
    None,
    ("Hobbies.Security", "OSINT, CTFs, networking"),
    ("Hobbies.Software", "Self-made tools, self-hosting"),
    ("Hobbies.Hardware", "ESP32, Arduino"),
    "Contact",
    ("GitHub", "@" + USER),
    "GitHub Stats",
    ("Repos", "{repos}"),
    ("Stars", "{stars}"),
    ("Commits", "{commits}"),
    ("Followers", "{followers}"),
]

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff", dots="#616e7f", art="#c9d1d9"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069", dots="#c2cfde", art="#24292f"),
}


def api(url, data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def stats():
    user = api(f"https://api.github.com/users/{USER}")
    repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    commits = "n/a"
    if os.environ.get("GITHUB_TOKEN"):
        total = 0
        for year in range(CREATED.year, date.today().year + 1):
            q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){
                   contributionsCollection(from:$f,to:$t){totalCommitContributions restrictedContributionsCount}}}"""
            v = {"u": USER, "f": f"{year}-01-01T00:00:00Z", "t": f"{year}-12-31T23:59:59Z"}
            c = api("https://api.github.com/graphql", {"query": q, "variables": v})["data"]["user"]["contributionsCollection"]
            total += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        commits = f"{total:,}"
    return {
        "repos": str(user["public_repos"]),
        "stars": str(sum(r["stargazers_count"] for r in repos if not r["fork"])),
        "followers": str(user["followers"]),
        "commits": commits,
    }


def uptime():
    # Year difference only: it ticks over on Jan 1, so the card never reveals the birth date.
    return f"{date.today().year - BIRTH_YEAR} years"


def info_lines(values):
    yield f'<tspan class="key">{USER.lower()}</tspan>@<tspan class="key">github</tspan>'
    yield "-" * WIDTH
    for item in INFO:
        if item is None:
            yield ""
        elif isinstance(item, str):
            yield ""
            yield f"- {escape(item)} " + "-" * (WIDTH - len(item) - 3)
        else:
            key, val = item[0], item[1].format(**values)
            dots = WIDTH - len(key) - len(val) - 4
            k = '<tspan class="dots">.</tspan>'.join(f'<tspan class="key">{escape(p)}</tspan>' for p in key.split("."))
            yield (f'<tspan class="dots">. </tspan>{k}:<tspan class="dots"> {"." * max(dots, 1)} </tspan>'
                   f'<tspan class="value">{escape(val)}</tspan>')


def render(theme, values):
    c = THEMES[theme]
    lh, art_lh = 20, 12  # info / art line heights (art uses a smaller font for detail)
    rows = list(info_lines(values))
    height = len(rows) * lh + 40
    lines = ASCII if theme == "dark" else [l.translate(INVERT) for l in ASCII]
    art_top = (height - len(lines) * art_lh) // 2 + art_lh
    art = "\n".join(f'<tspan x="20" y="{art_top + i * art_lh}">{escape(l)}</tspan>' for i, l in enumerate(lines))
    info = "\n".join(f'<tspan x="450" y="{30 + i * lh}">{r}</tspan>' for i, r in enumerate(rows))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="985" height="{height}" font-family="Consolas,'DejaVu Sans Mono','Courier New',monospace" font-size="15px">
<style>
.key {{fill: {c['key']};}} .value {{fill: {c['value']};}} .dots {{fill: {c['dots']};}}
text {{white-space: pre; font-variant-ligatures: none;}}
</style>
<rect width="985" height="{height}" fill="{c['bg']}" rx="15"/>
<text fill="{c['art']}" xml:space="preserve" font-size="9.5px">
{art}
</text>
<text fill="{c['text']}" xml:space="preserve">
{info}
</text>
</svg>
"""


if __name__ == "__main__":
    values = {"uptime": uptime(), **stats()}
    for theme in THEMES:
        with open(os.path.join(HERE, f"{theme}_mode.svg"), "w") as f:
            f.write(render(theme, values))
    print(values)
