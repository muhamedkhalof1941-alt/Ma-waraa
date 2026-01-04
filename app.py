from flask import Flask, render_template_string, request, jsonify
import os
import json
import requests
from openai import OpenAI

app = Flask(__name__)

# Configuration
BOT_TOKEN = "8240379609:AAFKeQ8hLv605TSD7AdG29vGTpZ4fPex62E"
CHANNEL_ID = "-1002560480003"
ADMIN_ID = "5365833232"
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Initialize OpenAI
client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

# Data storage file
DATA_FILE = '/tmp/ma_waraa_data.json'

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return get_default_data()

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def get_default_data():
    return {
        "news": [],
        "sources": [
            {"id": 1, "name": "المستشار", "username": "Almustashaar", "active": True},
            {"id": 2, "name": "صوت الحرب", "username": "sawtl7arb", "active": True},
            {"id": 3, "name": "تسريبات الحرب", "username": "WarsLeaks", "active": True},
            {"id": 4, "name": "نايا للعراق", "username": "nayaforiraq", "active": True}
        ],
        "settings": {
            "news_length": "medium",
            "rewrite_intensity": "medium",
            "style": "neutral",
            "creativity": 0.5,
            "sarcasm_enabled": False,
            "country_sarcasm": {
                "israel": {"enabled": False, "style": "ساخر لاذع"},
                "usa": {"enabled": False, "style": "ساخر خفيف"},
                "iran": {"enabled": False, "style": "ساخر متوسط"},
                "turkey": {"enabled": False, "style": "ساخر خفيف"},
                "russia": {"enabled": False, "style": "ساخر متوسط"},
                "saudi": {"enabled": False, "style": "ساخر خفيف"}
            }
        }
    }

# Country flags mapping
COUNTRY_FLAGS = {
    'العراق': '🇮🇶', 'عراق': '🇮🇶', 'بغداد': '🇮🇶', 'العراقي': '🇮🇶',
    'إيران': '🇮🇷', 'ايران': '🇮🇷', 'طهران': '🇮🇷', 'إيراني': '🇮🇷', 'الإيراني': '🇮🇷',
    'إسرائيل': '🇮🇱', 'اسرائيل': '🇮🇱', 'تل أبيب': '🇮🇱', 'الإسرائيلي': '🇮🇱', 'الاحتلال': '🇮🇱', 'الصهيوني': '🇮🇱',
    'أمريكا': '🇺🇸', 'امريكا': '🇺🇸', 'الأمريكي': '🇺🇸', 'واشنطن': '🇺🇸', 'الولايات المتحدة': '🇺🇸',
    'سوريا': '🇸🇾', 'دمشق': '🇸🇾', 'السوري': '🇸🇾', 'سوري': '🇸🇾',
    'لبنان': '🇱🇧', 'بيروت': '🇱🇧', 'حزب الله': '🇱🇧', 'اللبناني': '🇱🇧',
    'السعودية': '🇸🇦', 'الرياض': '🇸🇦', 'السعودي': '🇸🇦',
    'الإمارات': '🇦🇪', 'أبوظبي': '🇦🇪', 'دبي': '🇦🇪', 'الإماراتي': '🇦🇪',
    'تركيا': '🇹🇷', 'أنقرة': '🇹🇷', 'التركي': '🇹🇷', 'تركي': '🇹🇷',
    'روسيا': '🇷🇺', 'موسكو': '🇷🇺', 'الروسي': '🇷🇺', 'روسي': '🇷🇺',
    'الصين': '🇨🇳', 'بكين': '🇨🇳', 'الصيني': '🇨🇳',
    'بريطانيا': '🇬🇧', 'لندن': '🇬🇧', 'البريطاني': '🇬🇧',
    'فرنسا': '🇫🇷', 'باريس': '🇫🇷', 'الفرنسي': '🇫🇷',
    'اليمن': '🇾🇪', 'صنعاء': '🇾🇪', 'الحوثي': '🇾🇪', 'اليمني': '🇾🇪',
    'فلسطين': '🇵🇸', 'غزة': '🇵🇸', 'حماس': '🇵🇸', 'الفلسطيني': '🇵🇸',
    'مصر': '🇪🇬', 'القاهرة': '🇪🇬', 'المصري': '🇪🇬',
    'الأردن': '🇯🇴', 'عمان': '🇯🇴', 'الأردني': '🇯🇴',
    'الكويت': '🇰🇼', 'الكويتي': '🇰🇼',
    'قطر': '🇶🇦', 'الدوحة': '🇶🇦', 'القطري': '🇶🇦',
    'البحرين': '🇧🇭', 'البحريني': '🇧🇭',
    'ألمانيا': '🇩🇪', 'برلين': '🇩🇪', 'الألماني': '🇩🇪',
    'أوكرانيا': '🇺🇦', 'كييف': '🇺🇦', 'الأوكراني': '🇺🇦',
}

# Country detection for sarcasm
COUNTRY_KEYWORDS = {
    'israel': ['إسرائيل', 'اسرائيل', 'الإسرائيلي', 'تل أبيب', 'الاحتلال', 'الصهيوني', 'نتنياهو'],
    'usa': ['أمريكا', 'امريكا', 'الأمريكي', 'واشنطن', 'البيت الأبيض', 'البنتاغون'],
    'iran': ['إيران', 'ايران', 'الإيراني', 'طهران', 'الحرس الثوري'],
    'turkey': ['تركيا', 'التركي', 'أنقرة', 'أردوغان'],
    'russia': ['روسيا', 'الروسي', 'موسكو', 'بوتين', 'الكرملين'],
    'saudi': ['السعودية', 'السعودي', 'الرياض', 'ابن سلمان']
}

# News type emojis
NEWS_EMOJIS = {
    'انفجار': '💥', 'تفجير': '💥', 'قصف': '💥',
    'غارة': '✈️', 'غارات': '✈️', 'طائرة': '✈️',
    'صاروخ': '🚀', 'صواريخ': '🚀',
    'تصريح': '📢', 'تصريحات': '📢', 'قال': '📢', 'أعلن': '📢', 'صرح': '📢',
    'اجتماع': '🤝', 'مباحثات': '🤝', 'قمة': '🤝',
    'عسكري': '🎖️', 'جيش': '🎖️', 'قوات': '🎖️', 'مناورة': '🎖️',
    'اعتقال': '⚠️', 'احتجاز': '⚠️',
    'احتجاج': '📣', 'احتجاجات': '📣', 'مظاهرات': '📣', 'تظاهرات': '📣',
    'حرب': '⚔️', 'هجوم': '⚔️', 'اشتباك': '⚔️', 'معركة': '⚔️',
    'سياسي': '🏛️', 'رئيس': '🏛️', 'وزير': '🏛️', 'حكومة': '🏛️',
    'اقتصاد': '💰', 'دولار': '💰', 'اقتصادي': '💰',
    'نفط': '🛢️', 'بترول': '🛢️',
    'طاقة': '⚡', 'كهرباء': '⚡',
    'زلزال': '🌋', 'فيضان': '🌊', 'كارثة': '🔥',
}

# Ad filter keywords
AD_KEYWORDS = ['إعلان', 'رابط', 'خصم', 'عرض', 'تخفيض', 'للتواصل', 'للحجز', 'اشترك', 'تابعنا', 'رابط القناة', 'انضم', 'اشتراك', 'مجاني', 'فرصة', 'حصري', 't.me/', '@']

def is_ad(text):
    return sum(1 for kw in AD_KEYWORDS if kw in text) >= 2

def get_flags(text):
    flags = []
    for country, flag in COUNTRY_FLAGS.items():
        if country in text and flag not in flags:
            flags.append(flag)
    return flags[:3]

def get_emoji(text):
    for keyword, emoji in NEWS_EMOJIS.items():
        if keyword in text:
            return emoji
    return '📰'

def detect_country(text):
    for country, keywords in COUNTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return country
    return None

def add_hidden_signature(text):
    signature = "iraqiBoy"
    zwc = {
        'i': '\u200b', 'r': '\u200c', 'a': '\u200d', 'q': '\ufeff',
        'B': '\u200b\u200c', 'o': '\u200c\u200d', 'y': '\u200d\u200b'
    }
    hidden = ''.join(zwc.get(c, '') for c in signature)
    return text + hidden

def get_length_instruction(length):
    if length == 'short':
        return "جملة واحدة فقط (15-25 كلمة)"
    elif length == 'long':
        return "3-4 جمل مفصلة (50-80 كلمة)"
    else:
        return "جملتين (25-40 كلمة)"

def get_intensity_instruction(intensity):
    if intensity == 'light':
        return "إعادة صياغة خفيفة مع الحفاظ على معظم الكلمات الأصلية"
    elif intensity == 'strong':
        return "إعادة صياغة كاملة بأسلوب مختلف تماماً"
    else:
        return "إعادة صياغة متوسطة مع تغيير الأسلوب"

def get_sarcasm_prompt(country, settings):
    country_sarcasm = settings.get('country_sarcasm', {})
    
    if country and country in country_sarcasm:
        cs = country_sarcasm[country]
        if cs.get('enabled', False):
            style = cs.get('style', 'ساخر')
            
            sarcasm_templates = {
                'israel': f"""
استخدم أسلوب {style} عند الحديث عن إسرائيل:
- استخدم مصطلحات مثل "الكيان" أو "دولة الاحتلال"
- أضف تعليقات ساخرة خفية
- استخدم علامات تعجب للسخرية
- مثال: "أعلن جيش الاحتلال عن 'إنجازاته' المزعومة..."
""",
                'usa': f"""
استخدم أسلوب {style} عند الحديث عن أمريكا:
- استخدم مصطلحات مثل "شرطي العالم" أو "راعي الديمقراطية"
- أضف تعليقات ساخرة عن التدخلات
- مثال: "واشنطن تواصل 'نشر الديمقراطية' بطريقتها المعتادة..."
""",
                'iran': f"""
استخدم أسلوب {style} عند الحديث عن إيران:
- استخدم تعليقات ساخرة عن التصريحات الرسمية
- مثال: "طهران تؤكد مجدداً على 'سلمية' برنامجها..."
""",
                'turkey': f"""
استخدم أسلوب {style} عند الحديث عن تركيا:
- أضف تعليقات ساخرة عن السياسات
- مثال: "أنقرة تواصل 'دبلوماسيتها' الفريدة..."
""",
                'russia': f"""
استخدم أسلوب {style} عند الحديث عن روسيا:
- استخدم تعليقات ساخرة عن التصريحات
- مثال: "الكرملين يؤكد 'حرصه' على السلام..."
""",
                'saudi': f"""
استخدم أسلوب {style} عند الحديث عن السعودية:
- أضف تعليقات ساخرة خفيفة
- مثال: "الرياض تعلن عن 'رؤيتها' الجديدة..."
"""
            }
            return sarcasm_templates.get(country, "")
    return ""

def rewrite_with_ai(text, settings=None):
    if settings is None:
        data = load_data()
        settings = data.get('settings', get_default_data()['settings'])
    
    flags = get_flags(text)
    emoji = get_emoji(text)
    flags_str = '/'.join(flags) if flags else '🌍'
    
    if not client:
        result = f"{flags_str} {emoji} {text[:200]}"
        return add_hidden_signature(result)
    
    try:
        news_length = settings.get('news_length', 'medium')
        intensity = settings.get('rewrite_intensity', 'medium')
        style = settings.get('style', 'neutral')
        creativity = settings.get('creativity', 0.5)
        
        country = detect_country(text)
        sarcasm_prompt = ""
        
        if settings.get('sarcasm_enabled', False):
            sarcasm_prompt = get_sarcasm_prompt(country, settings)
        
        length_inst = get_length_instruction(news_length)
        intensity_inst = get_intensity_instruction(intensity)
        
        style_inst = ""
        if style == 'sarcastic':
            style_inst = "استخدم أسلوب ساخر وتهكمي في الصياغة"
        elif style == 'formal':
            style_inst = "استخدم أسلوب رسمي وجاد جداً"
        else:
            style_inst = "استخدم أسلوب محايد ومهني"
        
        system_prompt = f"""أنت محرر أخبار محترف. مهمتك إعادة صياغة الأخبار.

قواعد الصياغة:
1. {length_inst}
2. {intensity_inst}
3. {style_inst}
4. بدون مقدمات أو كلمة "عاجل"
5. بدون توقيع أو اسم قناة
6. فقط الخبر الصافي

{sarcasm_prompt}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"أعد صياغة هذا الخبر:\n\n{text}"}
            ],
            max_tokens=300,
            temperature=creativity
        )
        
        rewritten = response.choices[0].message.content.strip()
        rewritten = rewritten.replace('عاجل:', '').replace('عاجل -', '').replace('عاجل', '').strip()
        
        final = f"{flags_str} {emoji} {rewritten}"
        return add_hidden_signature(final)
        
    except Exception as e:
        result = f"{flags_str} {emoji} {text[:200]}"
        return add_hidden_signature(result)

def send_to_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHANNEL_ID, "text": text}
        response = requests.post(url, data=data)
        return response.json().get('ok', False)
    except:
        return False

# HTML Template
HTML = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ما وراء - لوحة التحكم</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Cairo', Arial; background: linear-gradient(135deg, #0f1419 0%, #1a252f 50%, #0f1419 100%); color: #fff; min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 30px 0; border-bottom: 2px solid #e74c3c; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; color: #e74c3c; margin-bottom: 10px; }
        .header p { color: #8899a6; font-size: 1.1em; }
        .nav { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 30px; }
        .nav-btn { background: linear-gradient(145deg, #1e2d3d, #152028); color: #fff; border: 1px solid #2d4a5e; padding: 12px 25px; border-radius: 10px; cursor: pointer; font-size: 1em; font-family: 'Cairo'; transition: all 0.3s; }
        .nav-btn:hover, .nav-btn.active { background: linear-gradient(145deg, #e74c3c, #c0392b); border-color: #e74c3c; transform: translateY(-2px); }
        .section { display: none; background: linear-gradient(145deg, #192734, #15202b); border-radius: 15px; padding: 25px; margin-bottom: 20px; border: 1px solid #2d4a5e; }
        .section.active { display: block; }
        .section h2 { color: #e74c3c; margin-bottom: 20px; font-size: 1.5em; border-bottom: 2px solid #2d4a5e; padding-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(145deg, #1e2d3d, #152028); padding: 25px; border-radius: 15px; text-align: center; border: 1px solid #2d4a5e; }
        .stat-card h3 { color: #8899a6; font-size: 0.9em; margin-bottom: 10px; }
        .stat-card .value { font-size: 2.5em; color: #e74c3c; font-weight: bold; }
        textarea, input[type="text"] { width: 100%; padding: 15px; background: #0f1419; border: 2px solid #2d4a5e; border-radius: 10px; color: #fff; font-size: 1em; font-family: 'Cairo'; margin-bottom: 15px; resize: vertical; }
        textarea:focus, input:focus { outline: none; border-color: #e74c3c; }
        select { width: 100%; padding: 12px; background: #0f1419; border: 2px solid #2d4a5e; border-radius: 10px; color: #fff; font-size: 1em; font-family: 'Cairo'; margin-bottom: 15px; cursor: pointer; }
        select:focus { outline: none; border-color: #e74c3c; }
        .btn { background: linear-gradient(145deg, #e74c3c, #c0392b); color: white; border: none; padding: 15px 30px; border-radius: 10px; cursor: pointer; font-size: 1.1em; font-family: 'Cairo'; font-weight: 600; transition: all 0.3s; display: inline-flex; align-items: center; gap: 10px; margin: 5px; }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(231, 76, 60, 0.3); }
        .btn-success { background: linear-gradient(145deg, #27ae60, #1e8449); }
        .source-item { display: flex; justify-content: space-between; align-items: center; padding: 15px; background: #0f1419; border-radius: 10px; margin-bottom: 10px; border: 1px solid #2d4a5e; }
        .source-info h4 { color: #fff; margin-bottom: 5px; }
        .source-info span { color: #8899a6; font-size: 0.9em; }
        .status-badge { padding: 5px 15px; border-radius: 20px; font-size: 0.85em; font-weight: 600; }
        .status-active { background: #27ae60; color: white; }
        .news-item { background: #0f1419; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-right: 4px solid #e74c3c; }
        .result-box { background: #0f1419; border: 2px solid #27ae60; border-radius: 10px; padding: 20px; margin-top: 20px; white-space: pre-wrap; line-height: 1.8; }
        .result-box.error { border-color: #e74c3c; }
        .loading { display: none; text-align: center; padding: 20px; }
        .loading.show { display: block; }
        .spinner { border: 4px solid #2d4a5e; border-top: 4px solid #e74c3c; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .footer { text-align: center; padding: 20px; color: #8899a6; border-top: 1px solid #2d4a5e; margin-top: 30px; }
        .settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .settings-card { background: #0f1419; padding: 20px; border-radius: 10px; border: 1px solid #2d4a5e; }
        .settings-card h3 { color: #e74c3c; margin-bottom: 15px; font-size: 1.1em; }
        .settings-card label { display: block; color: #8899a6; margin-bottom: 8px; font-size: 0.95em; }
        .slider-container { margin-bottom: 20px; }
        .slider { width: 100%; height: 8px; border-radius: 5px; background: #2d4a5e; outline: none; -webkit-appearance: none; }
        .slider::-webkit-slider-thumb { -webkit-appearance: none; width: 20px; height: 20px; border-radius: 50%; background: #e74c3c; cursor: pointer; }
        .slider-value { text-align: center; color: #e74c3c; font-weight: bold; margin-top: 5px; }
        .toggle-container { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #2d4a5e; }
        .toggle-label { color: #fff; }
        .toggle { position: relative; width: 50px; height: 26px; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #2d4a5e; transition: .4s; border-radius: 26px; }
        .toggle-slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        .toggle input:checked + .toggle-slider { background-color: #e74c3c; }
        .toggle input:checked + .toggle-slider:before { transform: translateX(24px); }
        .country-card { background: #152028; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #2d4a5e; }
        .country-card.enabled { border-color: #e74c3c; }
        .country-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
        .country-flag { font-size: 1.5em; }
        .country-name { color: #fff; font-weight: 600; }
        @media (max-width: 768px) { .header h1 { font-size: 1.8em; } .nav-btn { padding: 10px 15px; font-size: 0.9em; } .settings-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔴 ما وراء</h1>
            <p>نظام إدارة الأخبار الاحترافي - النسخة المتقدمة</p>
        </div>
        
        <div class="nav">
            <button class="nav-btn active" onclick="showSection('dashboard')">📊 لوحة المعلومات</button>
            <button class="nav-btn" onclick="showSection('sources')">📡 المصادر</button>
            <button class="nav-btn" onclick="showSection('news')">📰 الأخبار</button>
            <button class="nav-btn" onclick="showSection('rewrite')">✏️ إعادة الصياغة</button>
            <button class="nav-btn" onclick="showSection('settings')">⚙️ الإعدادات</button>
            <button class="nav-btn" onclick="showSection('sarcasm')">😏 السخرية</button>
        </div>
        
        <div id="dashboard" class="section active">
            <h2>📊 لوحة المعلومات</h2>
            <div class="stats">
                <div class="stat-card"><h3>الأخبار المنشورة</h3><div class="value" id="news-count">0</div></div>
                <div class="stat-card"><h3>المصادر النشطة</h3><div class="value" id="sources-count">4</div></div>
                <div class="stat-card"><h3>حالة النظام</h3><div class="value" style="color: #27ae60;">✓</div></div>
                <div class="stat-card"><h3>وضع السخرية</h3><div class="value" id="sarcasm-status" style="font-size: 1.5em;">❌</div></div>
            </div>
            
            <div style="background: #0f1419; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #e74c3c;">
                <h3 style="color: #e74c3c; margin-bottom: 15px;">🚀 النشر السريع</h3>
                <p style="color: #8899a6; margin-bottom: 15px;">صياغة ونشر الأخبار بضغطة واحدة</p>
                <button class="btn btn-success" onclick="publishOne()">📰 نشر خبر تجريبي</button>
                <div id="auto-publish-status" style="margin-top: 15px;"></div>
            </div>
            
            <div style="text-align: center; padding: 20px; background: #0f1419; border-radius: 10px; border: 1px solid #27ae60;">
                <h3 style="color: #27ae60; margin-bottom: 10px;">✅ نظام ما وراء يعمل بنجاح!</h3>
                <p style="color: #8899a6;">لوحة التحكم جاهزة للاستخدام.</p>
                <p style="color: #f39c12; font-size: 0.9em; margin-top: 10px;">🔒 حماية الحقوق: كل خبر يحتوي على توقيع مخفي (iraqiBoy)</p>
            </div>
        </div>
        
        <div id="sources" class="section">
            <h2>📡 إدارة المصادر</h2>
            <div style="background: #0f1419; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #2d4a5e;">
                <h3 style="color: #27ae60; margin-bottom: 15px;">➕ إضافة مصدر جديد</h3>
                <input type="text" id="new-source-name" placeholder="اسم المصدر (مثال: قناة الأخبار)">
                <input type="text" id="new-source-username" placeholder="يوزرنيم القناة (مثال: news_channel)">
                <button class="btn btn-success" onclick="addSource()">➕ إضافة المصدر</button>
            </div>
            <h3 style="margin-bottom: 15px; color: #e74c3c;">📡 المصادر الحالية:</h3>
            <div id="sources-list"></div>
        </div>
        
        <div id="news" class="section">
            <h2>📰 إضافة خبر جديد</h2>
            <textarea id="news-text" rows="5" placeholder="أدخل الخبر هنا..."></textarea>
            <button class="btn btn-success" onclick="addAndSend()">🚀 صياغة وإرسال للقناة</button>
            <div class="loading" id="news-loading"><div class="spinner"></div><p>جاري المعالجة...</p></div>
            <div id="news-result" style="margin-top: 20px;"></div>
            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #e74c3c;">📋 الأخبار المنشورة</h3>
            <div id="news-list"></div>
        </div>
        
        <div id="rewrite" class="section">
            <h2>✏️ إعادة صياغة الخبر</h2>
            <p style="color: #8899a6; margin-bottom: 20px;">أدخل الخبر وسيتم إعادة صياغته حسب الإعدادات المحددة:</p>
            <textarea id="rewrite-text" rows="6" placeholder="أدخل الخبر الأصلي هنا..."></textarea>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn" onclick="rewriteNews()">✨ إعادة الصياغة</button>
                <button class="btn btn-success" onclick="rewriteAndSend()">🚀 صياغة وإرسال للقناة</button>
            </div>
            <div class="loading" id="rewrite-loading"><div class="spinner"></div><p>جاري إعادة الصياغة...</p></div>
            <div id="rewrite-result"></div>
        </div>
        
        <div id="settings" class="section">
            <h2>⚙️ إعدادات الصياغة</h2>
            <div class="settings-grid">
                <div class="settings-card">
                    <h3>📏 طول الخبر</h3>
                    <label>اختر طول الخبر المطلوب:</label>
                    <select id="news-length" onchange="updateSettings()">
                        <option value="short">قصير (جملة واحدة)</option>
                        <option value="medium" selected>متوسط (جملتين)</option>
                        <option value="long">طويل (3-4 جمل)</option>
                    </select>
                </div>
                
                <div class="settings-card">
                    <h3>✍️ شدة الصياغة</h3>
                    <label>مستوى إعادة الصياغة:</label>
                    <select id="rewrite-intensity" onchange="updateSettings()">
                        <option value="light">خفيفة (تغييرات بسيطة)</option>
                        <option value="medium" selected>متوسطة (تغيير الأسلوب)</option>
                        <option value="strong">قوية (إعادة كاملة)</option>
                    </select>
                </div>
                
                <div class="settings-card">
                    <h3>🎨 نمط الصياغة</h3>
                    <label>أسلوب كتابة الخبر:</label>
                    <select id="news-style" onchange="updateSettings()">
                        <option value="neutral" selected>محايد ومهني</option>
                        <option value="formal">رسمي وجاد</option>
                        <option value="sarcastic">ساخر وتهكمي</option>
                    </select>
                </div>
                
                <div class="settings-card">
                    <h3>🌡️ درجة الإبداع</h3>
                    <label>مستوى إبداع الذكاء الاصطناعي:</label>
                    <div class="slider-container">
                        <input type="range" min="0" max="100" value="50" class="slider" id="creativity-slider" onchange="updateSettings()">
                        <div class="slider-value" id="creativity-value">50%</div>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 20px; background: #0f1419; border-radius: 10px; border: 1px solid #27ae60;">
                <h3 style="color: #27ae60; margin-bottom: 15px;">📊 الإعدادات الحالية</h3>
                <div id="current-settings"></div>
            </div>
        </div>
        
        <div id="sarcasm" class="section">
            <h2>😏 إعدادات السخرية حسب الدولة</h2>
            <p style="color: #8899a6; margin-bottom: 20px;">فعّل السخرية لكل دولة بشكل منفصل مع تخصيص أسلوب السخرية:</p>
            
            <div class="settings-card" style="margin-bottom: 20px;">
                <div class="toggle-container">
                    <span class="toggle-label" style="font-size: 1.2em; font-weight: bold;">🎭 تفعيل نظام السخرية العام</span>
                    <label class="toggle">
                        <input type="checkbox" id="sarcasm-enabled" onchange="updateSarcasm()">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            </div>
            
            <div id="country-sarcasm-list">
                <div class="country-card" id="card-israel">
                    <div class="country-header">
                        <span class="country-flag">🇮🇱</span>
                        <span class="country-name">إسرائيل</span>
                        <label class="toggle" style="margin-right: auto;">
                            <input type="checkbox" id="sarcasm-israel" onchange="updateCountrySarcasm('israel')">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <select id="style-israel" onchange="updateCountrySarcasm('israel')">
                        <option value="ساخر لاذع">ساخر لاذع 🔥</option>
                        <option value="ساخر متوسط">ساخر متوسط 😏</option>
                        <option value="ساخر خفيف">ساخر خفيف 🙂</option>
                    </select>
                </div>
                
                <div class="country-card" id="card-usa">
                    <div class="country-header">
                        <span class="country-flag">🇺🇸</span>
                        <span class="country-name">أمريكا</span>
                        <label class="toggle" style="margin-right: auto;">
                            <input type="checkbox" id="sarcasm-usa" onchange="updateCountrySarcasm('usa')">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <select id="style-usa" onchange="updateCountrySarcasm('usa')">
                        <option value="ساخر خفيف">ساخر خفيف 🙂</option>
                        <option value="ساخر متوسط">ساخر متوسط 😏</option>
                        <option value="ساخر لاذع">ساخر لاذع 🔥</option>
                    </select>
                </div>
                
                <div class="country-card" id="card-iran">
                    <div class="country-header">
                        <span class="country-flag">🇮🇷</span>
                        <span class="country-name">إيران</span>
                        <label class="toggle" style="margin-right: auto;">
                            <input type="checkbox" id="sarcasm-iran" onchange="updateCountrySarcasm('iran')">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <select id="style-iran" onchange="updateCountrySarcasm('iran')">
                        <option value="ساخر متوسط">ساخر متوسط 😏</option>
                        <option value="ساخر خفيف">ساخر خفيف 🙂</option>
                        <option value="ساخر لاذع">ساخر لاذع 🔥</option>
                    </select>
                </div>
                
                <div class="country-card" id="card-turkey">
                    <div class="country-header">
                        <span class="country-flag">🇹🇷</span>
                        <span class="country-name">تركيا</span>
                        <label class="toggle" style="margin-right: auto;">
                            <input type="checkbox" id="sarcasm-turkey" onchange="updateCountrySarcasm('turkey')">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <select id="style-turkey" onchange="updateCountrySarcasm('turkey')">
                        <option value="ساخر خفيف">ساخر خفيف 🙂</option>
                        <option value="ساخر متوسط">ساخر متوسط 😏</option>
                        <option value="ساخر لاذع">ساخر لاذع 🔥</option>
                    </select>
                </div>
                
                <div class="country-card" id="card-russia">
                    <div class="country-header">
                        <span class="country-flag">🇷🇺</span>
                        <span class="country-name">روسيا</span>
                        <label class="toggle" style="margin-right: auto;">
                            <input type="checkbox" id="sarcasm-russia" onchange="updateCountrySarcasm('russia')">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <select id="style-russia" onchange="updateCountrySarcasm('russia')">
                        <option value="ساخر متوسط">ساخر متوسط 😏</option>
                        <option value="ساخر خفيف">ساخر خفيف 🙂</option>
                        <option value="ساخر لاذع">ساخر لاذع 🔥</option>
                    </select>
                </div>
                
                <div class="country-card" id="card-saudi">
                    <div class="country-header">
                        <span class="country-flag">🇸🇦</span>
                        <span class="country-name">السعودية</span>
                        <label class="toggle" style="margin-right: auto;">
                            <input type="checkbox" id="sarcasm-saudi" onchange="updateCountrySarcasm('saudi')">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <select id="style-saudi" onchange="updateCountrySarcasm('saudi')">
                        <option value="ساخر خفيف">ساخر خفيف 🙂</option>
                        <option value="ساخر متوسط">ساخر متوسط 😏</option>
                        <option value="ساخر لاذع">ساخر لاذع 🔥</option>
                    </select>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <button class="btn btn-success" onclick="saveSarcasmSettings()">💾 حفظ إعدادات السخرية</button>
            </div>
        </div>
        
        <div class="footer"><p>© 2026 نظام ما وراء | النسخة المتقدمة | جميع الحقوق محفوظة</p></div>
    </div>
    
    <script>
        let currentSettings = {};
        
        function showSection(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
        }
        
        function loadSettings() {
            fetch('/api/settings')
            .then(r => r.json())
            .then(data => {
                currentSettings = data;
                document.getElementById('news-length').value = data.news_length || 'medium';
                document.getElementById('rewrite-intensity').value = data.rewrite_intensity || 'medium';
                document.getElementById('news-style').value = data.style || 'neutral';
                document.getElementById('creativity-slider').value = (data.creativity || 0.5) * 100;
                document.getElementById('creativity-value').textContent = Math.round((data.creativity || 0.5) * 100) + '%';
                document.getElementById('sarcasm-enabled').checked = data.sarcasm_enabled || false;
                document.getElementById('sarcasm-status').textContent = data.sarcasm_enabled ? '✅' : '❌';
                
                const cs = data.country_sarcasm || {};
                ['israel', 'usa', 'iran', 'turkey', 'russia', 'saudi'].forEach(country => {
                    const countryData = cs[country] || {};
                    document.getElementById('sarcasm-' + country).checked = countryData.enabled || false;
                    document.getElementById('style-' + country).value = countryData.style || 'ساخر متوسط';
                    document.getElementById('card-' + country).classList.toggle('enabled', countryData.enabled || false);
                });
                
                updateCurrentSettingsDisplay();
            });
        }
        
        function updateSettings() {
            const settings = {
                news_length: document.getElementById('news-length').value,
                rewrite_intensity: document.getElementById('rewrite-intensity').value,
                style: document.getElementById('news-style').value,
                creativity: document.getElementById('creativity-slider').value / 100
            };
            
            document.getElementById('creativity-value').textContent = document.getElementById('creativity-slider').value + '%';
            
            fetch('/api/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            }).then(() => loadSettings());
        }
        
        function updateSarcasm() {
            const enabled = document.getElementById('sarcasm-enabled').checked;
            fetch('/api/settings/sarcasm', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({sarcasm_enabled: enabled})
            }).then(() => {
                document.getElementById('sarcasm-status').textContent = enabled ? '✅' : '❌';
            });
        }
        
        function updateCountrySarcasm(country) {
            const enabled = document.getElementById('sarcasm-' + country).checked;
            const style = document.getElementById('style-' + country).value;
            
            document.getElementById('card-' + country).classList.toggle('enabled', enabled);
            
            fetch('/api/settings/country-sarcasm', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({country: country, enabled: enabled, style: style})
            });
        }
        
        function saveSarcasmSettings() {
            alert('✅ تم حفظ إعدادات السخرية بنجاح!');
        }
        
        function updateCurrentSettingsDisplay() {
            const lengthMap = {'short': 'قصير', 'medium': 'متوسط', 'long': 'طويل'};
            const intensityMap = {'light': 'خفيفة', 'medium': 'متوسطة', 'strong': 'قوية'};
            const styleMap = {'neutral': 'محايد', 'formal': 'رسمي', 'sarcastic': 'ساخر'};
            
            document.getElementById('current-settings').innerHTML = 
                '<p>📏 طول الخبر: <strong>' + (lengthMap[currentSettings.news_length] || 'متوسط') + '</strong></p>' +
                '<p>✍️ شدة الصياغة: <strong>' + (intensityMap[currentSettings.rewrite_intensity] || 'متوسطة') + '</strong></p>' +
                '<p>🎨 نمط الصياغة: <strong>' + (styleMap[currentSettings.style] || 'محايد') + '</strong></p>' +
                '<p>🌡️ درجة الإبداع: <strong>' + Math.round((currentSettings.creativity || 0.5) * 100) + '%</strong></p>' +
                '<p>😏 السخرية: <strong>' + (currentSettings.sarcasm_enabled ? 'مفعّلة' : 'معطّلة') + '</strong></p>';
        }
        
        function addAndSend() {
            const text = document.getElementById('news-text').value;
            if (!text) { alert('أدخل الخبر أولاً'); return; }
            document.getElementById('news-loading').classList.add('show');
            fetch('/api/news/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: text}) })
            .then(r => r.json())
            .then(data => {
                document.getElementById('news-loading').classList.remove('show');
                if (data.success) {
                    document.getElementById('news-result').innerHTML = '<div class="result-box" style="border-color: #27ae60;">✅ ' + data.message + '<br><br><strong>الخبر المنشور:</strong><br>' + data.result + '</div>';
                    document.getElementById('news-text').value = '';
                } else {
                    document.getElementById('news-result').innerHTML = '<div class="result-box error">❌ ' + data.message + '</div>';
                }
                loadNews();
            });
        }
        
        function rewriteNews() {
            const text = document.getElementById('rewrite-text').value;
            if (!text) { alert('أدخل الخبر أولاً'); return; }
            document.getElementById('rewrite-loading').classList.add('show');
            document.getElementById('rewrite-result').innerHTML = '';
            fetch('/api/rewrite', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: text}) })
            .then(r => r.json())
            .then(data => {
                document.getElementById('rewrite-loading').classList.remove('show');
                document.getElementById('rewrite-result').innerHTML = '<div class="result-box"><strong>النتيجة:</strong><br><br>' + data.result + '</div>';
            });
        }
        
        function rewriteAndSend() {
            const text = document.getElementById('rewrite-text').value;
            if (!text) { alert('أدخل الخبر أولاً'); return; }
            document.getElementById('rewrite-loading').classList.add('show');
            document.getElementById('rewrite-result').innerHTML = '';
            fetch('/api/rewrite/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: text}) })
            .then(r => r.json())
            .then(data => {
                document.getElementById('rewrite-loading').classList.remove('show');
                if (data.success) {
                    document.getElementById('rewrite-result').innerHTML = '<div class="result-box" style="border-color: #27ae60;">✅ تم الإرسال للقناة!<br><br><strong>الخبر:</strong><br>' + data.result + '</div>';
                    document.getElementById('rewrite-text').value = '';
                } else {
                    document.getElementById('rewrite-result').innerHTML = '<div class="result-box error">❌ ' + data.message + '</div>';
                }
            });
        }
        
        function publishOne() {
            const status = document.getElementById('auto-publish-status');
            status.innerHTML = '<div class="loading show"><div class="spinner"></div><p>جاري النشر...</p></div>';
            fetch('/api/publish/one', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    status.innerHTML = '<div class="result-box" style="border-color: #27ae60;">✅ ' + data.message + '<br><br>' + data.result + '</div>';
                } else {
                    status.innerHTML = '<div class="result-box error">❌ ' + data.message + '</div>';
                }
            });
        }
        
        function loadSources() {
            fetch('/api/sources')
            .then(r => r.json())
            .then(data => {
                document.getElementById('sources-count').textContent = data.length;
                const html = data.map(s => 
                    '<div class="source-item"><div class="source-info"><h4>' + s.name + '</h4><span>@' + s.username + '</span></div><span class="status-badge status-active">نشط</span></div>'
                ).join('');
                document.getElementById('sources-list').innerHTML = html;
            });
        }
        
        function addSource() {
            const name = document.getElementById('new-source-name').value;
            const username = document.getElementById('new-source-username').value;
            if (!name || !username) { alert('أدخل اسم المصدر واليوزرنيم'); return; }
            fetch('/api/sources', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: name, username: username}) })
            .then(r => r.json())
            .then(data => {
                alert(data.message);
                document.getElementById('new-source-name').value = '';
                document.getElementById('new-source-username').value = '';
                loadSources();
            });
        }
        
        function loadNews() {
            fetch('/api/news')
            .then(r => r.json())
            .then(data => {
                document.getElementById('news-count').textContent = data.length;
                const html = data.slice(-10).reverse().map(n => '<div class="news-item">' + n.text + '</div>').join('');
                document.getElementById('news-list').innerHTML = html || '<p style="color: #8899a6;">لا توجد أخبار بعد</p>';
            });
        }
        
        loadSources();
        loadNews();
        loadSettings();
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/status')
def api_status():
    return jsonify({"openai": bool(OPENAI_API_KEY)})

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    data = load_data()
    if request.method == 'POST':
        new_settings = request.json
        data['settings'].update(new_settings)
        save_data(data)
        return jsonify({"message": "تم حفظ الإعدادات"})
    return jsonify(data.get('settings', get_default_data()['settings']))

@app.route('/api/settings/sarcasm', methods=['POST'])
def api_sarcasm():
    data = load_data()
    new_data = request.json
    data['settings']['sarcasm_enabled'] = new_data.get('sarcasm_enabled', False)
    save_data(data)
    return jsonify({"message": "تم تحديث إعدادات السخرية"})

@app.route('/api/settings/country-sarcasm', methods=['POST'])
def api_country_sarcasm():
    data = load_data()
    req = request.json
    country = req.get('country')
    if country:
        if 'country_sarcasm' not in data['settings']:
            data['settings']['country_sarcasm'] = {}
        data['settings']['country_sarcasm'][country] = {
            'enabled': req.get('enabled', False),
            'style': req.get('style', 'ساخر متوسط')
        }
        save_data(data)
    return jsonify({"message": "تم تحديث إعدادات السخرية للدولة"})

@app.route('/api/sources', methods=['GET', 'POST'])
def api_sources():
    data = load_data()
    if request.method == 'POST':
        req = request.json
        new_source = {
            "id": len(data['sources']) + 1,
            "name": req.get('name', ''),
            "username": req.get('username', '').replace('@', ''),
            "active": True
        }
        data['sources'].append(new_source)
        save_data(data)
        return jsonify({"message": "تم إضافة المصدر بنجاح"})
    return jsonify(data.get('sources', []))

@app.route('/api/news', methods=['GET', 'POST'])
def api_news():
    data = load_data()
    if request.method == 'POST':
        req = request.json
        data['news'].append({"id": len(data['news']) + 1, "text": req.get('text', '')})
        save_data(data)
        return jsonify({"message": "تم إضافة الخبر"})
    return jsonify(data.get('news', []))

@app.route('/api/news/send', methods=['POST'])
def api_news_send():
    data = load_data()
    req = request.json
    text = req.get('text', '')
    
    if is_ad(text):
        return jsonify({"success": False, "message": "تم تجاهل الخبر - يبدو أنه إعلان"})
    
    settings = data.get('settings', get_default_data()['settings'])
    rewritten = rewrite_with_ai(text, settings)
    
    if send_to_telegram(rewritten):
        data['news'].append({"id": len(data['news']) + 1, "text": rewritten})
        save_data(data)
        return jsonify({"success": True, "message": "تم إرسال الخبر للقناة", "result": rewritten})
    else:
        return jsonify({"success": False, "message": "فشل إرسال الخبر"})

@app.route('/api/rewrite', methods=['POST'])
def api_rewrite():
    data = load_data()
    req = request.json
    text = req.get('text', '')
    settings = data.get('settings', get_default_data()['settings'])
    rewritten = rewrite_with_ai(text, settings)
    return jsonify({"result": rewritten})

@app.route('/api/rewrite/send', methods=['POST'])
def api_rewrite_send():
    data = load_data()
    req = request.json
    text = req.get('text', '')
    
    if is_ad(text):
        return jsonify({"success": False, "message": "تم تجاهل الخبر - يبدو أنه إعلان"})
    
    settings = data.get('settings', get_default_data()['settings'])
    rewritten = rewrite_with_ai(text, settings)
    
    if send_to_telegram(rewritten):
        data['news'].append({"id": len(data['news']) + 1, "text": rewritten})
        save_data(data)
        return jsonify({"success": True, "message": "تم إرسال الخبر للقناة", "result": rewritten})
    else:
        return jsonify({"success": False, "message": "فشل إرسال الخبر"})

@app.route('/api/publish/one', methods=['POST'])
def api_publish_one():
    data = load_data()
    demo_news = "وزير الحرب الإسرائيلي يسرائيل كاتس ورئيس الأركان ايال زامير يجريان مناورة تحاكي اندلاع حرب مع إيران"
    
    settings = data.get('settings', get_default_data()['settings'])
    rewritten = rewrite_with_ai(demo_news, settings)
    
    if send_to_telegram(rewritten):
        data['news'].append({"id": len(data['news']) + 1, "text": rewritten})
        save_data(data)
        return jsonify({"success": True, "message": "تم نشر الخبر!", "result": rewritten})
    else:
        return jsonify({"success": False, "message": "فشل إرسال الخبر"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
