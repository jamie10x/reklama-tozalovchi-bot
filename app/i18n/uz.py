UZ = {
    "private": {
        "start": (
            "<b>Salom! Men {bot_name} — Telegram guruhlarida ruxsatsiz "
            "reklamalarni avtomatik aniqlab, o'chirib turadigan botman.</b>\n\n"
            "Qanday ishlaydi:\n"
            "1. Meni guruhingizga qo'shing.\n"
            "2. Menga <i>Xabarlarni o'chirish</i> huquqini bering.\n"
            "3. Men avtomatik ravishda reklama xabarlarini topib o'chiraman.\n\n"
            "Maxfiylik: Men faqat o'chirilgan xabarlar haqidagi metama'lumotlarni saqlayman. "
            "Oddiy xabarlar hech qachon saqlanmaydi.\n\n"
            "Mavjud buyruqlarni ko'rish uchun /help ni bosing."
        ),
        "help": (
            "<b>Mavjud buyruqlar:</b>\n\n"
            "/start — Botni ishga tushirish\n"
            "/help — Yordam\n"
            "/privacy — Maxfiylik haqida\n"
            "/status — Moderatsiya holatini ko'rish\n\n"
            "<b>Guruh buyruqlari (adminlar uchun):</b>\n"
            "/on — Himoyani yoqish\n"
            "/off — Himoyani o'chirish\n"
            "/mode — Himoya rejimini o'zgartirish\n"
            "/allow — Foydalanuvchi, bot, chat yoki domenga ruxsat berish\n"
            "/removeallow — Ruxsatni olib tashlash\n"
            "/allowlist — Ruxsat etilganlar ro'yxati\n"
            "/status — Moderatsiya holatini ko'rish\n"
            "/recent — Oxirgi o'chirilganlar\n"
            "/deletedata — Barcha ma'lumotlarni o'chirish\n"
            "/help — Yordam"
        ),
        "privacy": (
            "<b>Maxfiylik haqida ma'lumot:</b>\n\n"
            "Bot xabarlarni faqat reklama aniqlash uchun o'qiydi.\n"
            "Oddiy xabarlar hech qachon saqlanmaydi.\n"
            "Faqat o'chirilgan xabarlar metama'lumotlari saqlanadi.\n"
            "O'chirilgan xabarlar matni 250 belgi bilan cheklangan.\n"
            "O'chirish jurnallari 24 soatdan keyin avtomatik o'chadi.\n"
            "Xabarlar uchinchi tomon xizmatlariga yuborilmaydi.\n"
            "Foydalanuvchilar turli guruhlar bo'ylab kuzatilmaydi.\n"
            "Ma'lumotlar sotilmaydi yoki ulashilmaydi.\n"
            "Guruh egalari /deletedata orqali ma'lumotlarni o'chirishni so'rashi mumkin."
        ),
    },
    "commands": {
        "not_anonymous": (
            "Sizning kimligingizni aniqlab bo'lmadi. Anonim adminlar sozlamalarni "
            "o'zgartira olmaydi."
        ),
        "admin_required": "Siz guruh administratori bo'lishingiz kerak.",
        "group_start": (
            "AdCleaner bu guruhni himoya qilmoqda. "
            "Administrator /help buyrug'i orqali buyruqlarni ko'rishi mumkin."
        ),
        "chat_not_registered": (
            "Bu guruh ro'yxatdan o'tmagan. Botni olib tashlab, qayta qo'shing."
        ),
        "protection_enabled": "Reklama himoyasi yoqildi.",
        "protection_disabled": "Reklama himoyasi o'chirildi.",
        "mode_prompt": "Joriy rejim: <b>{mode}</b>\n\nHimoya darajasini tanlang:",
        "mode_changed": "Himoya rejimi <b>{mode}</b> ga o'zgartirildi.",
        "mode_denied": "Faqat administratorlar rejimni o'zgartira oladi.",
        "mode_chat_not_found": "Guruh topilmadi.",
        "mode_set": "Rejim {mode} qilib belgilandi",
        "allow_usage": (
            "Ishlatish: /allow @username\n"
            "       /allow example.com\n"
            "Yoki foydalanuvchi, bot yoki domenga ruxsat berish uchun "
            "xabariga reply qiling."
        ),
        "removeallow_usage": ("Ishlatish: /removeallow @username\n       /removeallow example.com"),
        "status_text": (
            "AdCleaner <b>{status}</b>.\n\n"
            "Rejim: <b>{mode}</b>\n"
            "Bugun o'chirilgan: <b>{deleted}</b>\n"
            "Ishonchli foydalanuvchi va botlar: <b>{users}</b>\n"
            "Ishonchli domenlar: <b>{domains}</b>"
        ),
        "status_active": "faol",
        "status_disabled": "o'chirilgan",
        "no_recent": "So'nggi o'chirilganlar mavjud emas.",
        "recent_title": "So'nggi o'chirilganlar:\n",
        "recent_item": "{i}. Ball: <b>{score}</b> | Sabab: {reasons}",
        "recent_excerpt": "   Matn: {excerpt}",
        "delete_owner_only": (
            "Faqat guruh egasi ma'lumotlarni o'chira oladi. "
            "Iltimos, guruh yaratuvchisiga murojaat qiling."
        ),
        "delete_confirm": (
            "⚠️ <b>Ishonchingiz komilmi?</b>\n\n"
            "Bu barcha sozlamalar va o'chirish jurnallarini butunlay o'chirib tashlaydi. "
            "Bot guruhni tark etadi.\n\n"
            "Bu amalni qaytarib bo'lmaydi."
        ),
        "delete_done": "Barcha ma'lumotlar o'chirildi. Bot guruhni tark etmoqda.",
        "delete_cancelled": "Ma'lumotlarni o'chirish bekor qilindi.",
        "help_group": (
            "<b>AdCleaner buyruqlari (adminlar uchun):</b>\n\n"
            "/on — Reklama himoyasini yoqish\n"
            "/off — Reklama himoyasini o'chirish\n"
            "/mode — Himoya rejimini o'zgartirish (Yumshoq / Oddiy / Qattiq)\n"
            "/allow @username — Foydalanuvchi yoki botga ruxsat berish\n"
            "/allow example.com — Domenga ruxsat berish\n"
            "/removeallow @username — Ruxsatni olib tashlash\n"
            "/removeallow example.com — Domen ruxsatini olib tashlash\n"
            "/allowlist — Ruxsat etilganlar ro'yxatini ko'rish\n"
            "/status — Moderatsiya holatini ko'rish\n"
            "/recent — So'nggi o'chirilganlarni ko'rish\n"
            "/deletedata — Barcha guruh ma'lumotlarini o'chirish (faqat egasi)\n"
            "/help — Yordam"
        ),
    },
    "membership": {
        "bot_added_can_delete": (
            "AdCleaner faol. Ruxsatsiz reklamalar avtomatik o'chiriladi.\n\n"
            "Administrator /mode buyrug'i bilan himoya darajasini o'zgartirishi "
            "yoki /off bilan himoyani o'chirishi mumkin."
        ),
        "bot_added_no_permission": (
            "AdCleaner reklamalarni o'chira olmaydi, chunki unda "
            "xabarlarni o'chirish huquqi yo'q.\n\n"
            "Botga <i>Xabarlarni o'chirish</i> huquqini bering."
        ),
        "permission_granted": (
            "O'chirish huquqi berildi. AdCleaner endi reklamalarni o'chira oladi."
        ),
        "permission_removed": "O'chirish huquqi olib tashlandi. Reklamalar o'chirilmaydi.",
    },
    "allowlist": {
        "chat_not_found": "Guruh topilmadi.",
        "already_exists": "{entity} allaqachon ruxsat etilgan.",
        "allowed": "{entity} ruxsat etildi.",
        "removed": "{entity} ruxsat etilganlar ro'yxatidan olib tashlandi.",
        "not_found": "{entity} ruxsat etilganlar ro'yxatida topilmadi.",
        "empty": "Hali ruxsat etilgan ob'ektlar yo'q.",
        "title": "Ruxsat etilgan ob'ektlar:\n",
        "item": "{icon} <b>{type}:</b> {name}",
        "types": {
            "user": "Foydalanuvchi",
            "bot": "Bot",
            "telegram_chat": "Chat",
            "domain": "Domen",
        },
    },
    "keyboards": {
        "mode": {
            "relaxed": "Yumshoq",
            "normal": "Oddiy",
            "strict": "Qattiq",
        },
        "confirm_delete": "Ha, barcha ma'lumotlarni o'chirish",
        "cancel_delete": "Bekor qilish",
        "trust_sender": "Yuboruvchiga ishonish",
        "allow_domain": "Domenga ruxsat berish",
        "allow_tg": "Telegram manzilga ruxsat berish",
        "add_to_group": "Guruhga qo'shish",
        "current_mode_prefix": "Joriy",
    },
    "commands_desc": {
        "private": {
            "start": "Botni ishga tushirish",
            "help": "Yordam",
            "privacy": "Maxfiylik haqida ma'lumot",
            "status": "Moderatsiya holatini ko'rish",
        },
        "group": {
            "on": "Reklama himoyasini yoqish",
            "off": "Reklama himoyasini o'chirish",
            "mode": "Himoya rejimini o'zgartirish",
            "allow": "Foydalanuvchi, bot, chat yoki domenga ruxsat berish",
            "removeallow": "Ruxsat etilgan ob'ektni olib tashlash",
            "allowlist": "Ruxsat etilganlar ro'yxatini ko'rish",
            "status": "Moderatsiya holatini ko'rish",
            "recent": "So'nggi o'chirilganlarni ko'rish",
            "deletedata": "Guruh ma'lumotlarini o'chirish",
            "help": "Yordam",
        },
    },
    "errors": {
        "delete_failed": "Xabarni o'chirishda xatolik yuz berdi.",
        "observation_failed": "Kuzatuvni yozishda xatolik.",
        "secadmin_unavailable": "SecAdmin ma'lumotlar bazasi mavjud emas, kuzatuvsiz ishlanmoqda.",
        "bot_not_admin": "Bot administrator emas, xabarlar o'chirilmaydi.",
    },
    "moderation": {
        "deleted_log": "O'chirildi: msg_id={msg_id} chat_id={chat_id} ball={score} sabab={reasons}",
        "delete_failed": "O'chirishda xatolik: msg_id={msg_id} chat_id={chat_id} xato={error}",
        "permission_regranted": (
            "Huquq qayta tekshirildi: bot endi chat_id={chat_id} da o'chira oladi"
        ),
        "no_permission": "Bot xabarlarni o'chira olmaydi: chat_id={chat_id}",
    },
}
