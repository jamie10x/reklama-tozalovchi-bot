import React, { createContext, useContext, useMemo, useState } from "react";

type Lang = "en" | "uz";
type Dict = Record<string, string>;

const LANG_KEY = "secadmin_lang";

const dictionaries: Record<Lang, Dict> = {
  en: {
    language: "Language",
    english: "English",
    uzbek: "Uzbek",
    telegram_soc: "Telegram SOC",
    header_title: "Telegram Security Operations",
    header_subtitle: "Authorized group monitoring and bot response console",
    api_online: "API online",
    api_checking: "API checking",
    logout: "Logout",
    operations: "Operations",
    investigation: "Investigation",
    response: "Response",
    administration: "Administration",
    command_center: "Command Center",
    live_triage: "Live Triage",
    group_health: "Group Health",
    activity_store: "Activity Store",
    events: "Events",
    cases: "Cases",
    member_intel: "Member Intel",
    indicators: "Indicators",
    users: "Users",
    bot_commands: "Bot Commands",
    reports: "Reports",
    system_health: "System Health",
    audit_log: "Audit Log",
    officers: "Officers",
    queue_command: "Queue command",
    command: "Command",
    group: "Group",
    recent_commands: "Recent commands",
    result_window: "Result window",
    no_commands: "No commands queued yet",
    required: "Required",
    manual_chat_id: "Manual Chat ID",
    chat_id: "Chat ID",
    message_id: "Message ID",
    user_id: "User ID",
    summary: "Summary",
    raw_json: "Raw JSON",
    copy_json: "Copy JSON",
    copied: "Copied",
    response_metadata: "Response metadata",
    select_command_result: "Select a command to inspect the full result.",
    member_profile: "Member profile",
    aliases: "Aliases",
    group_profiles: "Group profiles",
    risk_signals: "Risk signals",
    recent_observed_messages: "Recent observed messages",
    telegram_user_id: "Telegram user ID",
    fetch_profile_photos: "Fetch profile photos",
    refresh_member: "Refresh member",
    no_data_yet: "No data yet",
    message_info: "Message info",
    detection: "Detection",
    sender: "Sender",
    text: "Text",
    capture_policy_hidden: "Text hidden by capture policy",
    old_history_limit: "The bot cannot import old Telegram history. Data appears only after future updates are received.",
  },
  uz: {
    language: "Til",
    english: "Inglizcha",
    uzbek: "O'zbekcha",
    telegram_soc: "Telegram SOC",
    header_title: "Telegram Xavfsizlik Operatsiyalari",
    header_subtitle: "Ruxsatli guruh monitoringi va bot javob konsoli",
    api_online: "API ishlayapti",
    api_checking: "API tekshirilmoqda",
    logout: "Chiqish",
    operations: "Operatsiyalar",
    investigation: "Tahlil",
    response: "Javob",
    administration: "Boshqaruv",
    command_center: "Boshqaruv markazi",
    live_triage: "Jonli saralash",
    group_health: "Guruh holati",
    activity_store: "Faollik ombori",
    events: "Voqealar",
    cases: "Ishlar",
    member_intel: "A'zo ma'lumoti",
    indicators: "Indikatorlar",
    users: "Foydalanuvchilar",
    bot_commands: "Bot buyruqlari",
    reports: "Hisobotlar",
    system_health: "Tizim holati",
    audit_log: "Audit jurnali",
    officers: "Officerlar",
    queue_command: "Buyruqni navbatga qo'yish",
    command: "Buyruq",
    group: "Guruh",
    recent_commands: "So'nggi buyruqlar",
    result_window: "Natija oynasi",
    no_commands: "Hali buyruqlar navbatga qo'yilmagan",
    required: "Kerak",
    manual_chat_id: "Chat ID qo'lda",
    chat_id: "Chat ID",
    message_id: "Xabar ID",
    user_id: "User ID",
    summary: "Qisqa ma'lumot",
    raw_json: "To'liq JSON",
    copy_json: "JSON nusxalash",
    copied: "Nusxalandi",
    response_metadata: "Javob metadatasi",
    select_command_result: "To'liq natijani ko'rish uchun buyruqni tanlang.",
    member_profile: "A'zo profili",
    aliases: "Taxalluslar",
    group_profiles: "Guruh profillari",
    risk_signals: "Risk signallari",
    recent_observed_messages: "So'nggi kuzatilgan xabarlar",
    telegram_user_id: "Telegram user ID",
    fetch_profile_photos: "Profil rasmlari metadata",
    refresh_member: "A'zoni tekshirish",
    no_data_yet: "Hozircha ma'lumot yo'q",
    message_info: "Xabar ma'lumoti",
    detection: "Aniqlash",
    sender: "Yuboruvchi",
    text: "Matn",
    capture_policy_hidden: "Matn capture siyosati sabab yashirilgan",
    old_history_limit: "Bot eski Telegram tarixini import qila olmaydi. Ma'lumot faqat kelajakdagi update'lardan keyin paydo bo'ladi.",
  },
};

const I18nContext = createContext<{
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string) => string;
} | null>(null);

function loadLang(): Lang {
  return localStorage.getItem(LANG_KEY) === "uz" ? "uz" : "en";
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(loadLang);
  const value = useMemo(() => {
    const setLang = (next: Lang) => {
      localStorage.setItem(LANG_KEY, next);
      setLangState(next);
    };
    const t = (key: string) => dictionaries[lang][key] ?? dictionaries.en[key] ?? key;
    return { lang, setLang, t };
  }, [lang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used within I18nProvider");
  return value;
}
