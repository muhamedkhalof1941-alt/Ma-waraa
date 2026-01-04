from flask import Flask, render_template_string, request, jsonify
import json
import os
import requests
from datetime import datetime
import re

app = Flask(__name__)

# ============ الإعدادات ============
TELEGRAM_BOT_TOKEN = "8240379609:AAFKeQ8hLv605TSD7AdG29vGTpZ4fPex62E"
CHANNEL_ID = "-1002560480003"
ADMIN_ID = "5365833232"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

# ============ البيانات ============
DATA_FILE = '/tmp/ma_waraa_data.json'

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        "sources": [
            {"id": 1, "name": "المستشار", "username": "Almustashaar", "active": True},
            {"id": 2, "name": "صوت الحرب", "username": "sawtl7arb", "active": True},
            {"id": 3, "name": "تسريبات الحروب", "username": "WarsLeaks", "active": True},
            {"id": 4, "name": "نايا للعراق", "username": "nayaforiraq", "active": True}
        ],
        "news": [],
        "fetched_news": []
    }

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

# ============ فلتر الإعلانات ============
AD_KEYWORDS = [
    "إعلان", "ممول", "رابط", "اشترك", "الرابط", "للتواصل", "للإعلان",
    "سعر", "خصم", "عرض", "مجاني", "اضغط هنا", "انضم", "قناتنا",
    "بوت", "bot", "@", "t.me/", "للحجز", "للشراء", "تواصل معنا",
    "رابط القناة", "رابط البوت", "البوت", "للتواصل"
]

def is_advertisement(text):
    text_lower = text.lower()
    ad_count = sum(1 for kw in AD_KEYWORDS if kw in text_lower)
    return ad_count >= 2

# ============ الإيموجيات حسب نوع الخبر ============
NEWS_EMOJIS = {
    "انفجار": {"emoji": "💥", "keywords": ["انفجار", "تفجير", "قنبلة", "عبوة", "انفجرت"]},
    "تصريح": {"emoji": "📢", "keywords": ["تصريح", "أعلن", "صرح", "أكد", "قال", "أشار"]},
    "عسكري": {"emoji": "🎖️", "keywords": ["جيش", "عسكري", "قوات", "مسلح", "صاروخ", "دبابة", "مناورة"]},
    "صحيفة": {"emoji": "📰", "keywords": ["صحيفة", "تقرير", "مصادر", "وثيقة", "كشف"]},
    "سياسي": {"emoji": "🏛️", "keywords": ["رئيس", "وزير", "برلمان", "حكومة", "انتخاب", "اجتماع"]},
    "أمني": {"emoji": "🚨", "keywords": ["أمن", "شرطة", "اعتقال", "مداهمة", "اشتباك"]},
    "حرب": {"emoji": "⚔️", "keywords": ["حرب", "قصف", "غارة", "هجوم", "معركة", "غارات"]},
    "طائرة": {"emoji": "✈️", "keywords": ["طائرة", "جوية", "طيران", "درون", "مسيرة"]},
    "بحري": {"emoji": "🚢", "keywords": ["سفينة", "بحري", "ميناء", "بحر"]},
    "اقتصاد": {"emoji": "💰", "keywords": ["دولار", "نفط", "اقتصاد", "سعر", "بورصة"]},
    "كارثة": {"emoji": "🔥", "keywords": ["زلزال", "فيضان", "حريق", "كارثة", "ضحايا"]},
}

def get_news_emoji(text):
    for category, data in NEWS_EMOJIS.items():
        for kw in data["keywords"]:
            if kw in text:
                return data["emoji"]
    return "📌"

# ============ حماية الحقوق بالحروف المخفية ============
def encode_watermark(text, watermark="iraqiBoy"):
    ZERO_WIDTH_SPACE = '\u200b'
    ZERO_WIDTH_NON_JOINER = '\u200c'
    binary = ''.join(format(ord(c), '08b') for c in watermark)
    hidden = ''
    for bit in binary:
        if bit == '0':
            hidden += ZERO_WIDTH_SPACE
        else:
            hidden += ZERO_WIDTH_NON_JOINER
    return hidden + text

def fetch_channel_messages(username):
    try:
        url = f"https://t.me/s/{username}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            messages = []
            pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
            matches = re.findall(pattern, response.text, re.DOTALL)
            for match in matches[:10]:
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                if clean_text and len(clean_text) > 20 and not is_advertisement(clean_text):
                    messages.append({'text': clean_text, 'source': username})
            return messages[:5]
    except:
        pass
    return []

# ============ قاموس الأعلام ============
FLAGS = {
    "العراق": "🇮🇶", "عراق": "🇮🇶", "بغداد": "🇮🇶", "البصرة": "🇮🇶", "أربيل": "🇮🇶", "الموصل": "🇮🇶",
    "سوريا": "🇸🇾", "سوري": "🇸🇾", "دمشق": "🇸🇾", "حلب": "🇸🇾",
    "إيران": "🇮🇷", "ايران": "🇮🇷", "طهران": "🇮🇷", "إيراني": "🇮🇷",
    "أمريكا": "🇺🇸", "امريكا": "🇺🇸", "أمريكي": "🇺🇸", "واشنطن": "🇺🇸", "الولايات المتحدة": "🇺🇸",
    "إسرائيل": "🇮🇱", "اسرائيل": "🇮🇱", "إسرائيلي": "🇮🇱", "تل أبيب": "🇮🇱", "الاحتلال": "🇮🇱",
    "فلسطين": "🇵🇸", "فلسطيني": "🇵🇸", "غزة": "🇵🇸", "الضفة": "🇵🇸",
    "لبنان": "🇱🇧", "لبناني": "🇱🇧", "بيروت": "🇱🇧", "حزب الله": "🇱🇧",
    "السعودية": "🇸🇦", "سعودي": "🇸🇦", "الرياض": "🇸🇦",
    "الإمارات": "🇦🇪", "إماراتي": "🇦🇪", "أبوظبي": "🇦🇪", "دبي": "🇦🇪",
    "تركيا": "🇹🇷", "تركي": "🇹🇷", "أنقرة": "🇹🇷", "إسطنبول": "🇹🇷",
    "روسيا": "🇷🇺", "روسي": "🇷🇺", "موسكو": "🇷🇺",
    "الصين": "🇨🇳", "صيني": "🇨🇳", "بكين": "🇨🇳",
    "مصر": "🇪🇬", "مصري": "🇪🇬", "القاهرة": "🇪🇬",
    "الأردن": "🇯🇴", "أردني": "🇯🇴", "عمان": "🇯🇴",
    "الكويت": "🇰🇼", "كويتي": "🇰🇼",
    "قطر": "🇶🇦", "قطري": "🇶🇦", "الدوحة": "🇶🇦",
    "البحرين": "🇧🇭", "بحريني": "🇧🇭",
    "اليمن": "🇾🇪", "يمني": "🇾🇪", "صنعاء": "🇾🇪", "الحوثي": "🇾🇪",
    "ليبيا": "🇱🇾", "ليبي": "🇱🇾", "طرابلس": "🇱🇾",
    "السودان": "🇸🇩", "سوداني": "🇸🇩", "الخرطوم": "🇸🇩",
    "الجزائر": "🇩🇿", "جزائري": "🇩🇿",
    "المغرب": "🇲🇦", "مغربي": "🇲🇦",
    "تونس": "🇹🇳", "تونسي": "🇹🇳",
    "أوكرانيا": "🇺🇦", "أوكراني": "🇺🇦", "كييف": "🇺🇦",
    "بريطانيا": "🇬🇧", "بريطاني": "🇬🇧", "لندن": "🇬🇧",
    "فرنسا": "🇫🇷", "فرنسي": "🇫🇷", "باريس": "🇫🇷",
    "ألمانيا": "🇩🇪", "ألماني": "🇩🇪", "برلين": "🇩🇪",
}

def get_flags(text):
    found_flags = []
    for keyword, flag in FLAGS.items():
        if keyword in text and flag not in found_flags:
            found_flags.append(flag)
    return "/".join(found_flags[:3]) if found_flags else "🌍"

def rewrite_with_ai(original_text):
    flags = get_flags(original_text)
    emoji = get_news_emoji(original_text)
    
    if not OPENAI_API_KEY:
        result = f"{flags} {emoji} {original_text}"
        return encode_watermark(result)
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""أنت محرر أخبار محترف ومحايد. أعد صياغة الخبر التالي بشكل:
1. محايد تماماً - بدون أي انحياز سياسي
2. مختصر وواضح - جملة أو جملتين فقط
3. بدون أي مقدمات أو كلمات مثل "عاجل" أو "خبر"
4. فقط الخبر نفسه بشكل مباشر

الخبر الأصلي:
{original_text}

أعد صياغته بجملة أو جملتين فقط (بدون أي إضافات):"""

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "أنت محرر أخبار. تعيد صياغة الأخبار بشكل مختصر ومحايد. جملة أو جملتين فقط."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.5
        }
        
        response = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_text = result["choices"][0]["message"]["content"].strip()
            final_text = f"{flags} {emoji} {ai_text}"
            return encode_watermark(final_text)
        else:
            result = f"{flags} {emoji} {original_text}"
            return encode_watermark(result)
            
    except Exception as e:
        result = f"{flags} {emoji} {original_text}"
        return encode_watermark(result)

def send_to_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHANNEL_ID, "text": text}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False
