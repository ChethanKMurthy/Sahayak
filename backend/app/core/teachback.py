"""Builds the voice teach-back script: the filled form read aloud in the user's
language before any PDF is produced. Nothing is output until the user confirms."""
from __future__ import annotations

from typing import Any

_INTRO = {
    "en": "Here is your filled form. Please listen and confirm it is correct.",
    "hi": "यह आपका भरा हुआ फ़ॉर्म है। कृपया सुनें और पुष्टि करें कि यह सही है।",
    "kn": "ಇದು ನಿಮ್ಮ ಭರ್ತಿ ಮಾಡಿದ ಫಾರ್ಮ್. ದಯವಿಟ್ಟು ಕೇಳಿ ಮತ್ತು ಸರಿ ಎಂದು ದೃಢೀಕರಿಸಿ.",
    "ta": "இது உங்கள் நிரப்பப்பட்ட படிவம். தயவுசெய்து கேட்டு உறுதிப்படுத்தவும்.",
    "te": "ఇది మీ నింపిన ఫారమ్. దయచేసి విని నిర్ధారించండి.",
    "mr": "हा तुमचा भरलेला फॉर्म आहे. कृपया ऐका आणि बरोबर असल्याची पुष्टी करा.",
    "bn": "এটি আপনার পূরণ করা ফর্ম। শুনে নিশ্চিত করুন এটি সঠিক।",
}
_OUTRO = {
    "en": "If everything is correct, please say yes to confirm.",
    "hi": "यदि सब कुछ सही है, तो पुष्टि के लिए हाँ कहें।",
    "kn": "ಎಲ್ಲವೂ ಸರಿಯಾಗಿದ್ದರೆ, ದೃಢೀಕರಿಸಲು ಹೌದು ಎಂದು ಹೇಳಿ.",
    "ta": "அனைத்தும் சரியாக இருந்தால், உறுதிப்படுத்த ஆம் என்று சொல்லுங்கள்.",
    "te": "అన్నీ సరిగ్గా ఉంటే, నిర్ధారించడానికి అవును అని చెప్పండి.",
    "mr": "सर्व बरोबर असल्यास, पुष्टीसाठी होय म्हणा.",
    "bn": "সব ঠিক থাকলে, নিশ্চিত করতে হ্যাঁ বলুন।",
}


def build_teachback(filled: list[dict[str, Any]], lang: str) -> dict[str, Any]:
    """Return {script, lines[]} — lines also carry tier so the UI highlights
    amber/red while the audio plays."""
    lines = []
    for f in filled:
        if f.get("missing") or f.get("value") in (None, ""):
            continue
        text = f"{f['label']}: {f['value']}"
        lines.append({"text": text, "tier": f.get("tier", "amber"), "key": f["key"]})
    intro = _INTRO.get(lang, _INTRO["en"])
    outro = _OUTRO.get(lang, _OUTRO["en"])
    script = intro + " " + ". ".join(l["text"] for l in lines) + ". " + outro
    return {"script": script, "intro": intro, "outro": outro, "lines": lines}
