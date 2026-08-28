"""Newsletter draft generator built from selected curated news stories."""
from __future__ import annotations
from typing import Any


def generate_newsletter(stories: list[dict[str, Any]], title: str = "Daily Wonder") -> dict[str, Any]:
    if not stories:
        return {"title": title, "markdown": "", "stories": [], "count": 0}

    sections = [f"# {title}", "", "## Market Briefing", ""]
    for index, story in enumerate(stories, 1):
        source = story.get("source", "Source")
        url = story.get("sourceUrl", "")
        headline = story.get("headline", "Untitled")
        snapshot = story.get("snapshot", "")
        sections.extend([
            f"### {index}. {headline}",
            "",
            snapshot,
            "",
            f"**Source: {source}**" + (f" — [Read original]({url})" if url else ""),
            "",
        ])
    sections.extend(["---", "*Daily Wonder — a curated snapshot of what matters in markets.*"])
    return {"title": title, "markdown": "\n".join(sections), "stories": stories, "count": len(stories)}
