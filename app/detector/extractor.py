from __future__ import annotations

import logging
import re
from typing import Any

from aiogram.enums import MessageEntityType
from aiogram.types import MessageEntity

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(
    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
    r"(?::\d+)?"
    r"(?:/(?:[-\w./@%+~&=:;#]*))?"
    r"(?:\?[-\w./@%+&=:;#]*)?"
    r"(?:#[-\w./@%+&=:;#]*)?",
    re.IGNORECASE,
)

MENTION_PATTERN = re.compile(r"@[a-z][a-z0-9_]{4,31}", re.IGNORECASE)

IPV4_PATTERN = re.compile(
    r"(?<!\d)(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}(?!\d)"
)

BTC_PATTERN = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
ETH_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
TRX_PATTERN = re.compile(r"\bT[A-Za-z1-9]{33}\b")

PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{4,9}(?!\d)"
)

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def extract_text(
    text: str | None,
    caption: str | None = None,
    entities: list[MessageEntity] | None = None,
    caption_entities: list[MessageEntity] | None = None,
) -> str:
    result = text or caption or ""
    return result


def extract_urls(text: str) -> list[str]:
    return URL_PATTERN.findall(text)


def extract_mentions(text: str) -> list[str]:
    return MENTION_PATTERN.findall(text)


def extract_entity_urls(text: str, entities: list[MessageEntity] | None) -> list[str]:
    if not entities or not text:
        return []
    urls = []
    for entity in entities:
        if entity.type == MessageEntityType.URL:
            url = text[entity.offset : entity.offset + entity.length]
            urls.append(url)
        elif entity.type == MessageEntityType.TEXT_LINK:
            urls.append(entity.url or "")
    return urls


def extract_from_entities(
    text: str,
    entities: list[MessageEntity] | None,
    caption_entities: list[MessageEntity] | None,
) -> dict[str, Any]:
    all_entities = (entities or []) + (caption_entities or [])
    result = {
        "urls": [],
        "mentions": [],
        "text_links": [],
        "bot_commands": [],
        "hashtags": [],
        "emails": [],
        "bold_count": 0,
        "has_spoiler": False,
    }

    for entity in all_entities:
        entity_text = text[entity.offset : entity.offset + entity.length] if text else ""

        if entity.type == MessageEntityType.URL:
            result["urls"].append(entity_text)
        elif entity.type == MessageEntityType.TEXT_LINK:
            result["text_links"].append(entity.url or entity_text)
        elif entity.type in (
            MessageEntityType.MENTION,
            MessageEntityType.CASHTAG,
        ):
            result["mentions"].append(entity_text)
        elif entity.type == MessageEntityType.BOT_COMMAND:
            result["bot_commands"].append(entity_text)
        elif entity.type == MessageEntityType.HASHTAG:
            result["hashtags"].append(entity_text)
        elif entity.type == MessageEntityType.EMAIL:
            result["emails"].append(entity_text)
        elif entity.type == MessageEntityType.BOLD:
            result["bold_count"] += 1
        elif entity.type == MessageEntityType.SPOILER:
            result["has_spoiler"] = True

    return result


def extract_ip_addresses(text: str) -> list[str]:
    return IPV4_PATTERN.findall(text)


def extract_crypto_wallets(text: str) -> dict[str, list[str]]:
    wallets: dict[str, list[str]] = {}
    btc = BTC_PATTERN.findall(text)
    if btc:
        wallets["btc"] = btc
    eth = ETH_PATTERN.findall(text)
    if eth:
        wallets["eth"] = eth
    trx = TRX_PATTERN.findall(text)
    if trx:
        wallets["trx"] = trx
    return wallets


def extract_phone_numbers(text: str) -> list[str]:
    return list(set(PHONE_PATTERN.findall(text)))


def extract_emails_regex(text: str) -> list[str]:
    return list(set(EMAIL_PATTERN.findall(text)))


def extract_security_indicators(text: str) -> dict[str, list[str]]:
    indicators: dict[str, list[str]] = {}
    ips = extract_ip_addresses(text)
    if ips:
        indicators["ip"] = ips
    wallets = extract_crypto_wallets(text)
    if wallets:
        all_wallets: list[str] = []
        for vals in wallets.values():
            all_wallets.extend(vals)
        indicators["wallet"] = all_wallets
    phones = extract_phone_numbers(text)
    if phones:
        indicators["phone"] = phones
    emails = extract_emails_regex(text)
    if emails:
        indicators["email"] = emails
    return indicators


def extract_forward_info(
    forward_from_chat_id: int | None,
    forward_from_chat_username: str | None = None,
    linked_chat_id: int | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "is_forwarded": forward_from_chat_id is not None,
        "forward_from_chat_id": forward_from_chat_id,
        "is_from_linked_chat": (
            forward_from_chat_id == linked_chat_id
            if forward_from_chat_id and linked_chat_id
            else False
        ),
    }
    return result
