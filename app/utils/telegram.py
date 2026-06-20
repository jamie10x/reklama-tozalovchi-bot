from __future__ import annotations

from html import escape


def escape_html(text: str | None) -> str:
    if text is None:
        return ""
    return escape(text, quote=True)


def extract_username_from_mention(text: str) -> str | None:
    if text.startswith("@"):
        return text[1:].lower()
    return None


def extract_domain_from_url(url: str) -> str | None:
    url = url.strip().lower()
    for prefix in ("https://", "http://", "ftp://"):
        if url.startswith(prefix):
            url = url[len(prefix) :]
            break
    slash_pos = url.find("/")
    if slash_pos != -1:
        url = url[:slash_pos]
    question_pos = url.find("?")
    if question_pos != -1:
        url = url[:question_pos]
    colon_pos = url.find(":")
    if colon_pos != -1:
        url = url[:colon_pos]
    if url.startswith("www."):
        url = url[4:]
    return url if url else None
