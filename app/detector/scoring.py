from __future__ import annotations

from typing import TYPE_CHECKING

from app.detector.models import DetectionResult
from app.detector.normalizer import (
    has_tracking_or_referral,
    normalize_domain,
    normalize_telegram_username,
)
from app.detector.phrases import SUPPORTED_LANGUAGES, PhraseMatcher

if TYPE_CHECKING:
    from app.database.repositories.allowlist import AllowlistRepository


STRONG_SIGNALS: dict[str, int] = {
    "external_telegram_invite": 6,
    "telegram_invite_with_action": 4,
    "referral_parameter": 4,
    "repeated_promotion": 5,
    "unauthorized_bot_promotion": 5,
    "strong_ad_phrase": 3,
    "offer_with_contact": 3,
}

MEDIUM_SIGNALS: dict[str, int] = {
    "external_url": 2,
    "multiple_links_or_mentions": 2,
    "price_or_discount": 2,
    "forwarded_unrelated_channel": 2,
}

NEGATIVE_SIGNALS: dict[str, int] = {
    "relevant_reply": -2,
}

THRESHOLDS: dict[str, int] = {
    "relaxed": 9,
    "normal": 6,
    "strict": 4,
}

TELEGRAM_DOMAINS = {"t.me", "telegram.me", "telegram.dog"}


def is_telegram_domain(domain: str) -> bool:
    return domain in TELEGRAM_DOMAINS


def scoring_pipeline(
    text: str,
    urls: list[str],
    mentions: list[str],
    telegram_usernames: list[str],
    has_forward: bool,
    forward_from_chat_id: int | None,
    linked_chat_id: int | None,
    mode: str,
    sender_is_bot: bool,
    allowlist_repo: AllowlistRepository,
    chat_uuid,
) -> DetectionResult:
    result = DetectionResult()
    matched_phrases = PhraseMatcher.find_matches(text, languages=SUPPORTED_LANGUAGES)

    all_urls = list(urls)

    detected_domains_set: set[str] = set()
    telegram_entities_set: set[str] = set()

    for url in all_urls:
        for domain in TELEGRAM_DOMAINS:
            if domain in url.lower():
                username = _extract_telegram_username_from_url(url)
                if username:
                    telegram_entities_set.add(username.lower())
                break
        else:
            dom = normalize_domain(url)
            if dom and dom not in TELEGRAM_DOMAINS:
                detected_domains_set.add(dom)

    for mention in mentions:
        username = normalize_telegram_username(mention)
        telegram_entities_set.add(username)

    for uname in telegram_usernames:
        telegram_entities_set.add(uname.lower())

    result.detected_domains = list(detected_domains_set)
    result.detected_telegram_entities = list(telegram_entities_set)

    has_url = len(all_urls) > 0
    has_mention = len(mentions) > 0
    has_telegram_links = len(telegram_usernames) > 0

    n_telegram_usernames = len(telegram_entities_set)
    n_external_domains = len(detected_domains_set)

    score = 0

    if (
        not has_url
        and not has_mention
        and not has_telegram_links
        and not matched_phrases
        and not has_forward
    ):
        return result

    if has_forward and forward_from_chat_id != linked_chat_id:
        score += MEDIUM_SIGNALS["forwarded_unrelated_channel"]
        result.reasons.append("forwarded_unrelated_channel")

    commercial_count = 0
    for _, category in matched_phrases:
        if category == "telegram_invite":
            if has_telegram_links:
                score += STRONG_SIGNALS["telegram_invite_with_action"]
                result.reasons.append("telegram_invite_with_action")
                break
            score += MEDIUM_SIGNALS["external_url"]
            result.reasons.append("telegram_invite")
        elif category == "commercial":
            score += MEDIUM_SIGNALS["price_or_discount"]
            result.reasons.append("price_or_discount")
            commercial_count += 1

    if commercial_count >= 3:
        score += STRONG_SIGNALS["strong_ad_phrase"]
        result.reasons.append("multiple_ad_phrases")

    for _, category in matched_phrases:
        if category == "telegram_invite" and not has_telegram_links and not has_url:
            continue

    if has_telegram_links:
        score += STRONG_SIGNALS["external_telegram_invite"]
        result.reasons.append("external_telegram_invite")

    if n_external_domains > 0:
        score += MEDIUM_SIGNALS["external_url"] * min(n_external_domains, 2)
        result.reasons.append("external_url")

    if n_telegram_usernames >= 2 or n_external_domains >= 2:
        score += MEDIUM_SIGNALS["multiple_links_or_mentions"]
        result.reasons.append("multiple_links_or_mentions")

    for url in all_urls:
        if has_tracking_or_referral(url):
            score += STRONG_SIGNALS["referral_parameter"]
            result.reasons.append("referral_parameter")
            break

    for _, category in matched_phrases:
        if category == "commercial":
            contact_phrases = [
                "contact me",
                "dm me",
                "message me",
                "dm for",
                "message for",
                "contact for",
            ]
            if any(cp in text.lower() for cp in contact_phrases):
                score += STRONG_SIGNALS["offer_with_contact"]
                result.reasons.append("offer_with_contact")
                break

    has_commercial_phrase = any(c == "commercial" for _, c in matched_phrases)
    if has_commercial_phrase and has_url:
        score += 2
        result.reasons.append("url_with_commercial")

    threshold = THRESHOLDS.get(mode, THRESHOLDS["normal"])

    result.score = score
    result.is_advertisement = score >= threshold

    return result


def _extract_telegram_username_from_url(url: str) -> str | None:
    url = url.strip().lower()
    for domain in ("t.me/", "telegram.me/", "telegram.dog/"):
        if domain in url:
            parts = url.split(domain)
            if len(parts) > 1:
                path = parts[1].split("?")[0].split("/")[0]
                if path:
                    return path.lstrip("@")
    return None
