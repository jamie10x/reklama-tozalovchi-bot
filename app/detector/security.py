from __future__ import annotations

import logging

from app.detector.extractor import extract_security_indicators
from app.detector.models import SecurityResult
from app.detector.normalizer import normalize_uzbek_search_text

logger = logging.getLogger(__name__)

SUSPICIOUS_PHRASES: dict[str, dict[str, list[str]]] = {
    "uz": {
        "scam": [
            "pul ishlash", "tez pul", "oson pul", "kafolatlangan daromad",
            "investitsiya", "sarmoya kiriting", "foyda olasiz", "promokod",
            "bonus oling", "yutuq chiqdi", "sovrin yutdingiz", "plastik karta",
            "pul mukofot", "mukofot bor", "karta raqamingiz", "karta nomer",
            "kartangizni yuboring", "click orqali", "payme orqali", "ishonchli daromad",
            "kripto sarmoya", "pul tikib", "foyda kafolat",
        ],
        "phishing": [
            "kodni yuboring", "sms kod", "tasdiqlash kodi", "akkauntni tiklash",
            "parolni yuboring", "havolaga kiring", "linkka kiring", "kabinetga kiring",
            "parol kodini", "karta parol", "telegram kod", "login kod", "akkaunt tasdiqlash",
        ],
        "drug_medical": [
            "retseptsiz", "kuchli dori", "maxfiy dori", "garantiya natija",
            "ozdiruvchi", "oriqlash", "jinsiy quvvat", "potensiya",
            "narkotik", "giyohvand", "marixuana", "geroin", "tropikamid",
        ],
        "gambling": [
            "stavka", "tikish", "bukmeker", "kazino", "slot", "totalizator",
            "aniq prognoz", "express stavka", "1xbet", "mostbet", "melbet",
        ],
        "fake_job": [
            "uyda ish", "kunlik to'lov", "kunlik daromad", "tajriba shart emas",
            "pasport kerak", "karta ochish", "nomingizga karta", "operator kerak",
        ],
        "violence": [
            "qurol sotiladi", "portlovchi", "urishamiz", "o'ldirish", "qo'rqitish",
            "pichoq sotiladi", "travmatik", "patron",
        ],
    },
    "uz_cyrl": {
        "scam": [
            "пул ишлаш", "тез пул", "осон пул", "кафолатланган даромад",
            "инвестиция", "сармоя киритинг", "фойда оласиз", "ютуқ чиқди",
            "соврин ютдингиз", "пластик карта",
        ],
        "phishing": [
            "кодни юборинг", "смс код", "тасдиқлаш коди", "аккаунтни тиклаш",
            "паролни юборинг", "ҳаволага киринг", "линкка киринг",
        ],
        "drug_medical": [
            "рецептсиз", "кучли дори", "махфий дори", "гарантия натижа",
            "оздирувчи", "ориқлаш", "жинсий қувват", "потенция",
            "наркотик", "гиёҳванд",
        ],
        "gambling": [
            "ставка", "тикиш", "букмекер", "казино", "слот", "тотализатор",
            "аниқ прогноз",
        ],
        "fake_job": [
            "уйда иш", "кунлик тўлов", "кунлик даромад", "тажриба шарт эмас",
            "паспорт керак", "карта очиш", "номингизга карта",
        ],
        "violence": [
            "қурол сотилади", "портловчи", "ўлдириш", "қўрқитиш",
        ],
    },
    "en": {
        "scam": [
            "guaranteed profit", "double your money", "quick money", "investment opportunity",
            "claim prize", "you won", "send deposit", "risk free profit",
        ],
        "phishing": [
            "send code", "verification code", "login link", "recover account",
            "confirm your wallet", "seed phrase", "private key",
            "otp code",
        ],
        "drug_medical": [
            "no prescription", "miracle cure", "weight loss pills", "potency pills",
        ],
        "gambling": [
            "casino bonus", "sports betting", "bet now", "fixed match", "sure odds",
        ],
        "fake_job": [
            "work from home", "daily payout", "no experience needed", "open card",
        ],
        "violence": [
            "weapon for sale", "explosive", "kill threat", "shooting",
        ],
    },
    "ru": {
        "scam": [
            "быстрые деньги", "легкий заработок", "гарантированный доход",
            "инвестиция", "удвоим деньги", "вы выиграли", "получить приз",
        ],
        "phishing": [
            "отправьте код", "смс код", "код подтверждения", "восстановить аккаунт",
            "сид фраза", "приватный ключ", "перейдите по ссылке",
        ],
        "drug_medical": [
            "без рецепта", "чудо средство", "таблетки для похудения",
            "потенция", "секретный препарат", "наркотик",
        ],
        "gambling": [
            "ставки", "букмекер", "казино", "слоты", "договорной матч",
        ],
        "fake_job": [
            "работа на дому", "ежедневная оплата", "без опыта", "оформить карту",
        ],
        "violence": [
            "продам оружие", "взрывчатка", "угроза убийством",
        ],
    },
}

PHRASE_WEIGHTS: dict[str, int] = {
    "scam": 5,
    "phishing": 7,
    "drug_medical": 5,
    "gambling": 4,
    "fake_job": 5,
    "violence": 8,
}

SEVERITY_WEIGHTS: dict[str, int] = {
    "wallet": 8,
    "ip": 4,
    "phone": 5,
    "email": 3,
}

SEVERITY_MAP: dict[str, str] = {
    "wallet": "high",
    "ip": "medium",
    "phone": "high",
    "email": "low",
}

CRITICAL_THRESHOLD = 12
HIGH_THRESHOLD = 8
MEDIUM_THRESHOLD = 4


def _resolve_severity(score: int) -> str:
    if score >= CRITICAL_THRESHOLD:
        return "critical"
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def _extract_suspicious_phrases(text: str) -> dict[str, list[str]]:
    text_lower = text.lower()
    text_uz = normalize_uzbek_search_text(text)
    matched: dict[str, list[str]] = {}
    for lang, categories in SUSPICIOUS_PHRASES.items():
        haystack = text_uz if lang in {"uz", "uz_cyrl"} else text_lower
        for category, phrases in categories.items():
            for phrase in phrases:
                normalized_phrase = normalize_uzbek_search_text(phrase) if lang in {"uz", "uz_cyrl"} else phrase
                if normalized_phrase in haystack and phrase not in matched.get(category, []):
                    matched.setdefault(category, []).append(phrase)
    return matched


class SecurityDetector:
    def analyze(self, text: str) -> SecurityResult:
        if not text or not text.strip():
            return SecurityResult()

        indicators = extract_security_indicators(text)
        phrase_matches = _extract_suspicious_phrases(text)
        if not indicators and not phrase_matches:
            return SecurityResult()

        total_score = 0
        reasons: list[str] = []
        detected: dict[str, list[str]] = {}

        for indicator_type, values in indicators.items():
            weight = SEVERITY_WEIGHTS.get(indicator_type, 1)
            count = len(values)
            indicator_score = weight * count
            total_score += indicator_score
            reasons.append(
                f"{indicator_type}:{','.join(v for v in values[:3])}"
                f"({'x' + str(count) if count > 1 else ''})"
                f"={indicator_score}"
            )
            detected[indicator_type] = values

        for category, phrases in phrase_matches.items():
            score = PHRASE_WEIGHTS.get(category, 3) * len(phrases)
            total_score += score
            reasons.append(f"{category}:{','.join(phrases[:3])}={score}")
            detected[f"phrase_{category}"] = phrases

        severity = _resolve_severity(total_score)
        is_threat = total_score >= MEDIUM_THRESHOLD

        if is_threat:
            logger.info(
                "Security threat detected: score=%d severity=%s indicators=%s",
                total_score,
                severity,
                {k: len(v) for k, v in detected.items()},
            )

        return SecurityResult(
            is_threat=is_threat,
            score=total_score,
            severity=severity,
            reasons=reasons,
            detected_indicators=detected,
        )
