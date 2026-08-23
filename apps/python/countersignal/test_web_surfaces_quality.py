from __future__ import annotations

import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
SURFACES = ("index.html", "judge-console.html", "audit-verifier.html")


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.local_hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        node_id = values.get("id")
        if node_id:
            self.ids.append(node_id)
        if tag == "a":
            href = values.get("href")
            if href and not href.startswith(("http://", "https://", "mailto:", "#")):
                self.local_hrefs.append(href.split("#", 1)[0])


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _scripts(html: str) -> list[str]:
    return re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE)


@pytest.mark.parametrize("name", SURFACES)
def test_judge_surface_has_unique_dom_ids_and_resolved_local_links(name: str):
    html = _read(name)
    parser = SurfaceParser()
    parser.feed(html)

    assert parser.ids, f"{name} should expose stable DOM ids for interaction"
    assert len(parser.ids) == len(set(parser.ids)), f"{name} contains duplicate DOM ids"

    for href in parser.local_hrefs:
        assert (ROOT / href).is_file(), f"{name} points to missing local surface {href}"


@pytest.mark.parametrize("name", SURFACES)
def test_inline_javascript_parses_with_node(name: str, tmp_path: Path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is unavailable")

    scripts = _scripts(_read(name))
    assert scripts, f"{name} should contain its local reviewer logic"

    for index, script in enumerate(scripts):
        path = tmp_path / f"{Path(name).stem}-{index}.js"
        path.write_text(script, encoding="utf-8")
        result = subprocess.run(
            [node, "--check", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert result.returncode == 0, (
            f"inline JavaScript syntax error in {name}:\n{result.stdout}\n{result.stderr}"
        )
