"""
Multilingual early warnings for district, SDMA, and community channels.

SMS is logged here (Twilio / NDMA CAP would replace `dispatch`).
"""

from __future__ import annotations

from ner_landslide.store import add_notification, already_sent_today

LANGS = {
    "en": "English",
    "hi": "हिन्दी",
    "as": "অসমীয়া",
    "bn": "বাংলা",
}

LEVEL_WORDS = {
    "en": {"Low": "Low", "Moderate": "Moderate", "High": "High", "Severe": "Severe"},
    "hi": {"Low": "कम", "Moderate": "मध्यम", "High": "उच्च", "Severe": "गंभीर"},
    "as": {"Low": "কম", "Moderate": "মধ্যম", "High": "উচ্চ", "Severe": "গুৰুতৰ"},
    "bn": {"Low": "কম", "Moderate": "মাঝারি", "High": "উচ্চ", "Severe": "গুরুতর"},
}

ADVICE = {
    "en": {
        "Low": "Routine watch. Roads usually open.",
        "Moderate": "Avoid night travel on hill roads.",
        "High": "Restrict travel. Pre-position rescue teams.",
        "Severe": "Public warning. Close stretches. Prepare evacuation.",
    },
    "hi": {
        "Low": "नियमित निगरानी। सड़कें सामान्यतः खुली।",
        "Moderate": "पहाड़ी सड़कों पर रात की यात्रा न करें।",
        "High": "यात्रा सीमित करें। राहत दल तैयार रखें।",
        "Severe": "सार्वजनिक चेतावनी। सड़क बंद करें। निकासी तैयार करें।",
    },
    "as": {
        "Low": "নিয়মিত নিৰীক্ষণ। পথ সাধাৰণতে মুকলি।",
        "Moderate": "পাহাৰীয়া পথত ৰাতি যাত্ৰা নকৰিব।",
        "High": "যাত্ৰা সীমিত কৰক। উদ্ধাৰ দল সাজু ৰাখক।",
        "Severe": "ৰাজহুৱা সতৰ্কবাণী। পথ বন্ধ কৰক। খালীকৰণৰ বাবে সাজু।",
    },
    "bn": {
        "Low": "নিয়মিত নজরদারি। রাস্তা সাধারণত খোলা।",
        "Moderate": "পাহাড়ি রাস্তায় রাতে চলাচল এড়িয়ে চলুন।",
        "High": "ভ্রমণ সীমিত করুন। উদ্ধার দল প্রস্তুত রাখুন।",
        "Severe": "জনসতর্কতা। রাস্তা বন্ধ করুন। সরিয়ে নেওয়ার প্রস্তুতি।",
    },
}

HEAD = {
    "en": "NER LANDSLIDE ALERT",
    "hi": "उत्तर-पूर्व भूस्खलन चेतावनी",
    "as": "উত্তৰ-পূব ধস সতৰ্কবাণী",
    "bn": "উত্তর-পূর্ব ধস সতর্কতা",
}

AUDIENCES = (
    ("district", "sms"),
    ("sdma", "sms"),
    ("community", "app"),
)


def render_message(lang: str, station_name: str, state: str, level: str, probability: float) -> str:
    lang = lang if lang in LANGS else "en"
    pct = int(round(float(probability) * 100))
    word = LEVEL_WORDS[lang][level]
    advice = ADVICE[lang][level]
    return f"{HEAD[lang]} — {word} | {station_name}, {state} | {pct}% | {advice}"


def dispatch_for_station(station: dict, lang: str = "en") -> list[dict]:
    """Send (log) SMS/app alerts for High/Severe sites, once per day per audience."""
    level = station["level"]
    if level not in {"High", "Severe"}:
        return []
    sent = []
    for audience, channel in AUDIENCES:
        if already_sent_today(station["station_id"], level, audience, lang):
            continue
        body = render_message(
            lang,
            station["station_name"],
            station["state"],
            level,
            station.get("probability", station.get("risk_probability", 0)),
        )
        rec = add_notification(
            {
                "station_id": station["station_id"],
                "level": level,
                "channel": channel,
                "audience": audience,
                "lang": lang,
                "body": body,
            }
        )
        sent.append(rec)
    return sent
