from __future__ import annotations

from typing import ClassVar

AD_PHRASES = {
    "en": {
        "telegram_invite": [
            "join our channel",
            "join my channel",
            "subscribe now",
            "subscribe to",
            "join our group",
            "check out my channel",
            "use this bot",
            "subscribe for more",
            "join us",
            "join here",
        ],
        "commercial": [
            "buy now",
            "buy cheap",
            "limited offer",
            "special offer",
            "limited time",
            "check out",
            "contact me",
            "dm me",
            "message me",
            "cheap price",
            "discount",
            "promotion service",
            "advertising service",
            "earn money",
            "guaranteed profit",
            "investment opportunity",
            "referral link",
            "use my referral",
            "dm for price",
            "dm for details",
            "message for price",
            "contact for price",
            "price",
        ],
    },
    "uz": {},
    "ru": {},
}


class PhraseMatcher:
    _compiled: ClassVar[dict[str, list[tuple[str, str]]] | None] = None

    @classmethod
    def get_compiled(cls) -> dict[str, list[tuple[str, str]]]:
        if cls._compiled is not None:
            return cls._compiled

        compiled: dict[str, list[tuple[str, str]]] = {}
        for lang, categories in AD_PHRASES.items():
            compiled[lang] = []
            for category, phrases in categories.items():
                for phrase in phrases:
                    compiled[lang].append((phrase.lower(), category))
        cls._compiled = compiled
        return compiled

    @classmethod
    def find_matches(cls, text: str, languages: list[str] | None = None) -> list[tuple[str, str]]:
        text_lower = text.lower()
        all_phrases = cls.get_compiled()
        results: list[tuple[str, str]] = []

        langs = languages or ["en"]
        for lang in langs:
            if lang not in all_phrases:
                continue
            for phrase, category in all_phrases[lang]:
                if phrase in text_lower:
                    results.append((phrase, category))

        return results
