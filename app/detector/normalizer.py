from __future__ import annotations

import re
import unicodedata

TELEGRAM_URL_PATTERNS = {
    r"t\.me/([a-z][a-z0-9_]{4,31}[a-z0-9]|[a-z][a-z0-9_]{1,31})": r"t.me/\1",
    r"telegram\.me/([a-z][a-z0-9_]{4,31}[a-z0-9]|[a-z][a-z0-9_]{1,31})": r"telegram.me/\1",
    r"telegram\.dog/([a-z][a-z0-9_]{4,31}[a-z0-9]|[a-z][a-z0-9_]{1,31})": r"telegram.dog/\1",
}

SPACED_LINK_PATTERN = re.compile(
    r"(?:t\s*\.\s*me|telegram\s*\.\s*me|telegram\s*\.\s*dog)\s*/\s*@?([a-z0-9_]+)",
    re.IGNORECASE,
)

ZERO_WIDTH_CHARS = re.compile("[\u200b\u200c\u200d\u2060\u2061\u2062\u2063\u2064\ufeff]")

UZBEK_CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "j",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ц": "s",
    "ч": "ch",
    "ш": "sh",
    "ъ": "",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "ў": "o",
    "қ": "q",
    "ғ": "g",
    "ҳ": "h",
}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = ZERO_WIDTH_CHARS.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_uzbek_search_text(text: str) -> str:
    text = normalize_text(text).lower()
    transliterated = "".join(UZBEK_CYRILLIC_TO_LATIN.get(ch, ch) for ch in text)
    transliterated = transliterated.replace("o'", "o").replace("g'", "g")
    transliterated = transliterated.replace("o`", "o").replace("g`", "g")
    transliterated = transliterated.replace("ʻ", "'").replace("ʼ", "'")
    return re.sub(r"\s+", " ", transliterated).strip()


def normalize_telegram_username(username: str) -> str:
    return username.lstrip("@").lower().strip()


def normalize_domain(domain: str) -> str:
    domain = domain.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if domain.startswith(prefix):
            domain = domain[len(prefix) :]
    slash_pos = domain.find("/")
    if slash_pos != -1:
        domain = domain[:slash_pos]
    question_pos = domain.find("?")
    if question_pos != -1:
        domain = domain[:question_pos]
    return domain


def normalize_telegram_url(url: str) -> str | None:
    url = url.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if url.startswith(prefix):
            url = url[len(prefix) :]
    for pattern, template in TELEGRAM_URL_PATTERNS.items():
        match = re.match(pattern, url)
        if match:
            return template.replace(r"\1", match.group(1))
    return None


def extract_normalized_telegram_links(text: str) -> list[str]:
    text = normalize_text(text)
    results = []
    for match in SPACED_LINK_PATTERN.finditer(text):
        results.append(match.group(1).lower())
    return results


def has_tracking_or_referral(url: str) -> bool:
    url_lower = url.lower()
    referral_params = [
        "ref=",
        "referral=",
        "referrer=",
        "source=",
        "utm_source=",
        "utm_medium=",
        "utm_campaign=",
        "aff=",
        "affiliate=",
        "pid=",
        "clickid=",
    ]
    return any(param in url_lower for param in referral_params)
