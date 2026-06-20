from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock

from app.database.repositories.allowlist import AllowlistRepository
from app.detector.extractor import extract_from_entities, extract_text, extract_urls
from app.detector.models import DetectionResult
from app.detector.normalizer import (
    extract_normalized_telegram_links,
    normalize_domain,
    normalize_telegram_username,
    normalize_text,
)
from app.detector.scoring import scoring_pipeline

_REPEAT_CACHE: OrderedDict[str, float] = OrderedDict()
_REPEAT_CACHE_MAX = 500
_REPEAT_CACHE_TTL = 180.0
_repeat_cache_lock = Lock()


def _make_repeat_key(chat_id: int, user_id: int | None, normalized_text: str) -> str:
    return f"{chat_id}:{user_id or 0}:{normalized_text}"


def _is_repeated(chat_id: int, user_id: int | None, normalized_text: str) -> bool:
    key = _make_repeat_key(chat_id, user_id, normalized_text)
    now = time.time()
    with _repeat_cache_lock:
        if key in _REPEAT_CACHE:
            if now - _REPEAT_CACHE[key] < _REPEAT_CACHE_TTL:
                return True
            del _REPEAT_CACHE[key]
        _REPEAT_CACHE[key] = now
        while len(_REPEAT_CACHE) > _REPEAT_CACHE_MAX:
            _REPEAT_CACHE.popitem(last=False)
    return False


def _get_telegram_usernames_from_text(text: str) -> list[str]:
    return extract_normalized_telegram_links(text)


class DetectionService:
    async def analyze(
        self,
        text: str,
        entities: list | None = None,
        caption_entities: list | None = None,
        is_forwarded: bool = False,
        forward_from_chat_id: int | None = None,
        linked_chat_id: int | None = None,
        chat_telegram_id: int | None = None,
        allowlist_repo: AllowlistRepository | None = None,
        chat_uuid=None,
        sender_id: int | None = None,
        mode: str = "normal",
        sender_is_bot: bool = False,
    ) -> DetectionResult:
        raw_text = extract_text(text=text, entities=entities, caption_entities=caption_entities)

        if not raw_text and not is_forwarded:
            return DetectionResult()

        normalized = normalize_text(raw_text)

        entity_info = extract_from_entities(normalized, entities, caption_entities)

        extracted_urls = set(entity_info["urls"])
        for text_link in entity_info["text_links"]:
            extracted_urls.add(text_link)
        for url in extract_urls(normalized):
            extracted_urls.add(url)

        mentions = entity_info["mentions"]
        telegram_usernames = _get_telegram_usernames_from_text(normalized)

        for mention in mentions:
            username = normalize_telegram_username(mention)
            if username not in telegram_usernames:
                telegram_usernames.append(username)

        whitelisted_domains: set[str] = set()
        whitelisted_telegram: set[str] = set()

        if allowlist_repo is not None and chat_uuid is not None:
            domain_entries = await allowlist_repo.get_by_type(chat_uuid, "domain")
            for entry in domain_entries:
                whitelisted_domains.add(normalize_domain(entry.entity_value))

            tg_entries = await allowlist_repo.get_by_type(chat_uuid, "telegram_chat")
            for entry in tg_entries:
                whitelisted_telegram.add(normalize_telegram_username(entry.entity_value))

        filtered_urls = []
        for url in extracted_urls:
            domain = normalize_domain(url)
            if domain in whitelisted_domains:
                continue
            filtered_urls.append(url)

        filtered_telegram = []
        for uname in telegram_usernames:
            if uname.lower() in whitelisted_telegram:
                continue
            filtered_telegram.append(uname)

        if not filtered_urls and not filtered_telegram and not is_forwarded:
            from app.detector.phrases import PhraseMatcher

            matched_phrases = PhraseMatcher.find_matches(normalized, languages=["en"])
            if not matched_phrases:
                return DetectionResult()

        result = scoring_pipeline(
            text=normalized,
            urls=list(extracted_urls),
            mentions=mentions,
            telegram_usernames=telegram_usernames,
            has_forward=is_forwarded,
            forward_from_chat_id=forward_from_chat_id,
            linked_chat_id=linked_chat_id,
            mode=mode,
            sender_is_bot=sender_is_bot,
            allowlist_repo=allowlist_repo,
            chat_uuid=chat_uuid,
        )

        if (
            result.is_advertisement
            and sender_id is not None
            and chat_telegram_id is not None
            and _is_repeated(chat_telegram_id, sender_id, normalized)
        ):
            result.score += 5
            result.reasons.append("repeated_promotion")

        return result
