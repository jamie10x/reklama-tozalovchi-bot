from __future__ import annotations

from typing import ClassVar

from app.detector.normalizer import normalize_uzbek_search_text

SUPPORTED_LANGUAGES = ["en", "uz", "ru"]

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
    "uz": {
        "commercial": [
            "ёғ",
            "ёғлар",
            "ёғдан",
            "ёғни",
            "қорин",
            "вазн",
            "ортиқча вазн",
            "вазн йўқотиш",
            "ариқлаш",
            "кет",
            "кетказиш",
            "кетказин",
            "минус",
            "кило",
            "капсула",
            "таблетка",
            "препарат",
            "дори",
            "восита",
            "мўъжиза",
            "мўъжизавий",
            "тезкор",
            "тез натижа",
            "осон",
            "осон йўл",
            "кафолат",
            "100% кафолат",
            "натижа",
            "алоҳида таклиф",
            "таклиф",
            "акция",
            "чегирма",
            "арзон",
            "нарх",
            "доставка",
            "буюртма",
            "буюртма беринг",
            "ёзинг",
            "мурожаат",
            "мурожаат қилинг",
            "телефон",
            "сайт",
            "ссылк",
            "силка",
            "берди",
            "кун",
            "кунда",
            "хабар",
            "хабар беринг",
            "sotuv",
            "sotib olish",
            "chegirma",
            "yetkazib berish",
            "buyurtma",
        ],
    },
    "ru": {
        "commercial": [
            "жир",
            "похуд",
            "вес",
            "лишний вес",
            "капсул",
            "таблетк",
            "препарат",
            "средств",
            "чудо",
            "чудодейственн",
            "быстр",
            "моментальн",
            "результат",
            "гаранти",
            "100% гарантия",
            "скидк",
            "акци",
            "цена",
            "дешев",
            "доставк",
            "заказ",
            "купить",
            "заказать",
            "предложени",
            "специальное предложени",
            "успей",
            "ограниченно",
            "бесплат",
            "оплата",
            "переход",
            "ссылк",
            "перейди",
            "подпишись",
            "напиши",
            "свяжись",
            "контакт",
            "телефон",
            "сайт",
            "промокод",
            "секрет",
            "уникальн",
        ],
    },
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
                    if lang == "uz":
                        normalized = normalize_uzbek_search_text(phrase)
                        if normalized != phrase.lower():
                            compiled[lang].append((normalized, category))
        cls._compiled = compiled
        return compiled

    @classmethod
    def find_matches(cls, text: str, languages: list[str] | None = None) -> list[tuple[str, str]]:
        text_lower = text.lower()
        text_uz = normalize_uzbek_search_text(text)
        all_phrases = cls.get_compiled()
        results: list[tuple[str, str]] = []

        langs = languages or ["en"]
        for lang in langs:
            if lang not in all_phrases:
                continue
            for phrase, category in all_phrases[lang]:
                haystack = text_uz if lang == "uz" else text_lower
                if phrase in haystack:
                    results.append((phrase, category))

        return results
