"""Publish committed evidence inside the app, including for private repositories."""
from pathlib import Path
import re

import streamlit as st

from royale import config


def documents():
    """Only submission evidence is published; never arbitrary repository files."""
    findings = sorted(
        p.relative_to(config.REPO_ROOT).as_posix()
        for p in (config.REPO_ROOT / "findings").glob("[0-9]*.md")
    )
    return tuple(findings + ["docs/claims_evidence.md", "docs/ai_disclosure.md"])


def read_document(name):
    if name not in documents():
        raise ValueError("Choose a published evidence document")
    path = (config.REPO_ROOT / name).resolve()
    if path.parent not in {(config.REPO_ROOT / "findings").resolve(), (config.REPO_ROOT / "docs").resolve()}:
        raise ValueError("Evidence must stay inside its published directory")
    return path.read_text(encoding="utf-8")


def local_references_as_text(markdown):
    """Relative file URLs are not Streamlit routes; show their document names."""
    def replace(match):
        label, target = match.groups()
        if target.startswith(("https://", "http://", "mailto:", "#")):
            return match.group(0)
        return f"{label} (`{Path(target.split('#')[0]).name}`)"
    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", replace, markdown)


def render_evidence(preferred, key):
    choices = list(dict.fromkeys([*preferred, *documents()]))
    choices = [name for name in choices if name in documents()]
    st.caption("Read or download the committed evidence here; no GitHub login is needed. "
               "Documents retain their stated periods and review status when page filters change. "
               "File references in the text can be opened with this document picker.")
    name = st.selectbox("Evidence document", choices, key=f"{key}_document")
    text = read_document(name)
    st.download_button("Download evidence (Markdown)", text, file_name=Path(name).name,
                       mime="text/markdown", key=f"{key}_download")
    st.markdown(local_references_as_text(text))
