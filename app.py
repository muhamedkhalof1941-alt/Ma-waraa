from flask import Flask, render_template_string, request, jsonify
import os
import json
import requests
import random
import threading
import time
from datetime import datetime
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

# Auto-publish control
auto_publish_active = False
sarcasm_auto_active = {}

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
        "sarcasm_stats": {
            "israel": 0, "usa": 0, "iran": 0, "turkey": 0, "russia": 0, "saudi": 0
        },
        "custom_sarcasm": {},
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
            "beautify_text": True,
            "auto_publish": False,
            "publish_interval": 30,
            "sarcasm_enabled": False,
            "sarcasm_auto": {},
            "country_sarcasm": {
                "israel": {"enabled": False, "style": "ساخر لاذع", "auto_interval": 60, "auto_enabled": False},
                "usa": {"enabled": False, "style": "ساخر خفيف", "auto_interval": 60, "auto_enabled": False},
                "iran": {"enabled": False, "style": "ساخر متوسط", "auto_interval": 60, "auto_enabled": False},
                "turkey": {"enabled": False, "style": "ساخر خفيف", "auto_interval": 60, "auto_enabled": False},
                "russia": {"enabled": False, "style": "ساخر متوسط", "auto_interval": 60, "auto_enabled": False},
                "saudi": {"enabled": False, "style": "ساخر خفيف", "auto_interval": 60, "auto_enabled": False}
            }
        }
    }

# Text beautification function
def beautify_text(text):
    beautify_words = {
        'العراق': 'العـراق', 'عراق': 'عـراق', 'العراقي': 'العـراقي',
        'إسرائيل': 'إسـرائيل', 'اسرائيل': 'اسـرائيل', 'الإسرائيلي': 'الإسـرائيلي',
        'إيران': 'إيـران', 'ايران': 'ايـران', 'الإيراني': 'الإيـراني',
        'أمريكا': 'أمـريكا', 'امريكا': 'امـريكا', 'الأمريكي': 'الأمـريكي',
        'سوريا': 'سـوريا', 'السوري': 'السـوري',
        'لبنان': 'لبـنان', 'اللبناني': 'اللبـناني',
        'فلسطين': 'فلسـطين', 'الفلسطيني': 'الفلسـطيني',
        'السعودية': 'السعـودية', 'السعودي': 'السعـودي',
        'تركيا': 'تـركيا', 'التركي': 'التـركي',
        'روسيا': 'روسـيا', 'الروسي': 'الروسـي',
        'الصين': 'الصـين', 'الصيني': 'الصـيني',
        'اليمن': 'اليـمن', 'اليمني': 'اليـمني',
        'الحوثي': 'الحـوثي', 'حماس': 'حمـاس',
        'حزب الله': 'حـزب الله', 'الاحتلال': 'الاحـتلال',
        'الكيان': 'الكـيان', 'الصهيوني': 'الصهيـوني',
        'عسكري': 'عسـكري', 'صاروخ': 'صـاروخ', 'صواريخ': 'صـواريخ',
        'غارة': 'غـارة', 'غارات': 'غـارات',
        'انفجار': 'انفـجار', 'تفجير': 'تفـجير',
        'هجوم': 'هجـوم', 'حرب': 'حـرب', 'معركة': 'معـركة', 'اشتباك': 'اشتـباك',
    }
    for word, beautified in beautify_words.items():
        text = text.replace(word, beautified)
    return text

# Country flags and info
COUNTRY_INFO = {
    'israel': {
        'flag': '🇮🇱',
        'name': 'إسـرائيل',
        'alt_names': ['الكـيان', 'الاحـتلال', 'الصهاينة', 'دولة الاحـتلال'],
        'leaders': ['نتنياهو', 'غالانت', 'بن غفير', 'سموتريتش'],
        'institutions': ['الموساد', 'جيش الاحـتلال', 'الكنيست', 'الشاباك'],
    },
    'usa': {
        'flag': '🇺🇸',
        'name': 'أمـريكا',
        'alt_names': ['شرطي العالم', 'راعية الديمقراطية', 'الإمبراطورية'],
        'leaders': ['البيت الأبيض', 'البنتاغون', 'وزارة الخارجية'],
        'institutions': ['CIA', 'FBI', 'البنتاغون', 'الكونغرس'],
    },
    'iran': {
        'flag': '🇮🇷',
        'name': 'إيـران',
        'alt_names': ['الجمهورية الإسلامية', 'طهران'],
        'leaders': ['المرشد', 'الحرس الثوري', 'روحاني', 'رئيسي'],
        'institutions': ['الحرس الثوري', 'فيلق القدس', 'البرلمان'],
    },
    'turkey': {
        'flag': '🇹🇷',
        'name': 'تـركيا',
        'alt_names': ['أنقرة', 'الباب العالي'],
        'leaders': ['أردوغان', 'حزب العدالة والتنمية'],
        'institutions': ['الجيش التركي', 'MIT'],
    },
    'russia': {
        'flag': '🇷🇺',
        'name': 'روسـيا',
        'alt_names': ['الكرملين', 'موسكو', 'الدب الروسي'],
        'leaders': ['بوتين', 'لافروف', 'شويغو'],
        'institutions': ['FSB', 'الكرملين', 'الدوما'],
    },
    'saudi': {
        'flag': '🇸🇦',
        'name': 'السعـودية',
        'alt_names': ['المملكة', 'الرياض'],
        'leaders': ['ابن سلمان', 'الديوان الملكي'],
        'institutions': ['أرامكو', 'رؤية 2030'],
    }
}

# Massive sarcasm library - 20+ entries per country
SARCASM_LIBRARY = {
    'israel': {
        'historical': [
            "🇮🇱 في مثل هذا اليوم، أعلن الكـيان عن 'اكتشافه' لأرض كانت مسكونة منذ آلاف السنين! 🎭",
            "🇮🇱 ذكرى تأسيس 'جيش الدفاع' الذي لم يدافع يوماً إلا عن المستوطنات المسروقة! ⚔️",
            "🇮🇱 اليوم ذكرى وعد بلفور ـ حين وعد من لا يملك من لا يستحق! 📜",
            "🇮🇱 في مثل هذا اليوم، ادعت إسـرائيل أنها 'واحة الديمقراطية' بينما تحاصر مليوني إنسان! 🏜️",
            "🇮🇱 ذكرى إعلان الكـيان أنه يريد 'السلام' للمرة الألف... ولا زلنا ننتظر! 🕊️",
            "🇮🇱 في مثل هذا اليوم، قال الموساد إنه 'أذكى جهاز مخابرات'... ثم فشل في كل شيء! 🕵️",
            "🇮🇱 ذكرى بناء أول مستوطنة 'مؤقتة'... لا زالت موجودة بعد 50 سنة! 🏗️",
        ],
        'political': [
            "🇮🇱 نتنياهو يؤكد أن إسـرائيل 'دولة قانون'... بينما يُحاكم بتهم الفساد! ⚖️",
            "🇮🇱 الكنيست يصوت على قانون جديد لـ'حماية الديمقراطية'... بإلغاء الديمقراطية! 🗳️",
            "🇮🇱 وزير الأمن القومي يدعو للسلام... بعد أن أحرق نصف المنطقة! 🔥",
            "🇮🇱 الحكومة الإسـرائيلية تعلن 'انتصاراً ساحقاً'... للمرة المليون هذا الأسبوع! 🏆",
            "🇮🇱 بن غفير يزور الأقصى 'بسلام'... محاطاً بألف جندي مدجج بالسلاح! 🕌",
        ],
        'military': [
            "🇮🇱 جيش الاحـتلال يعلن 'تدمير حماس بالكامل'... للمرة العاشرة هذا الشهر! 💥",
            "🇮🇱 القبة الحديدية تعترض 'كل الصواريخ'... ما عدا تلك التي لم تعترضها! 🚀",
            "🇮🇱 الجيش الإسـرائيلي يؤكد أنه 'الأقوى في المنطقة'... ثم يطلب مساعدة أمريكية! 💪",
            "🇮🇱 سلاح الجو يقصف 'أهدافاً عسكرية فقط'... مثل المستشفيات والمدارس! ✈️",
            "🇮🇱 الموساد ينفذ عملية 'نوعية'... انتهت بفضيحة دولية كالعادة! 🎭",
        ],
        'economic': [
            "🇮🇱 الاقتصاد الإسـرائيلي 'الأقوى في المنطقة'... بفضل المساعدات الأمريكية فقط! 💰",
            "🇮🇱 تل أبيب تعلن عن 'ازدهار اقتصادي'... بينما نصف السكان تحت خط الفقر! 📉",
            "🇮🇱 الشيكل 'أقوى عملة'... حين تحسبها بالدولارات الأمريكية المُهداة! 💵",
        ],
        'ironic': [
            "🇮🇱 إسـرائيل تتهم الآخرين بـ'الإرهاب'... وهي التي اخترعته في المنطقة! 🎪",
            "🇮🇱 الكـيان يطالب بـ'حق الدفاع عن النفس'... أثناء احتلاله لأرض الغير! 🤡",
            "🇮🇱 'الدولة اليهودية الديمقراطية'... حيث 20% من السكان مواطنون درجة ثانية! 🎭",
            "🇮🇱 إسـرائيل تشتكي من 'معاداة السامية'... بينما تمارس الأبارتهايد! 😏",
            "🇮🇱 الكـيان يدعي أنه 'جزيرة استقرار'... محاطة بالفوضى التي صنعها! 🏝️",
        ]
    },
    'usa': {
        'historical': [
            "🇺🇸 في مثل هذا اليوم، أعلنت أمـريكا أنها ستنشر 'الديمقراطية'... بالقنابل! 💣",
            "🇺🇸 ذكرى غزو العـراق بحثاً عن أسلحة دمار شامل... لم تُوجد أبداً! 🔍",
            "🇺🇸 اليوم ذكرى تأسيس CIA ـ وكالة نشر الفوضى حول العالم! 🕵️",
            "🇺🇸 في مثل هذا اليوم، قالت واشنطن إنها 'شرطي العالم'... والعالم لم يطلب شرطياً! 👮",
            "🇺🇸 ذكرى إعلان أمـريكا عن 'حقوق الإنسان' بينما تدعم الديكتاتوريات! 📋",
            "🇺🇸 في مثل هذا اليوم، انسحبت أمـريكا من فيتنام 'منتصرة'... بعد هزيمة ساحقة! 🚁",
        ],
        'political': [
            "🇺🇸 البيت الأبيض يدعو للسلام... بينما يبيع الأسلحة لكل أطراف النزاع! 🕊️",
            "🇺🇸 الكونغرس يصوت على 'مساعدات إنسانية'... 90% منها أسلحة! 💰",
            "🇺🇸 وزير الخارجية يزور المنطقة لـ'تهدئة التوتر'... فيزيد التوتر! ✈️",
            "🇺🇸 واشنطن تفرض عقوبات على 'انتهاكات حقوق الإنسان'... ما عدا حلفاءها! ⚖️",
            "🇺🇸 أمـريكا تدعم 'حق تقرير المصير'... فقط حين يناسب مصالحها! 🗳️",
        ],
        'military': [
            "🇺🇸 البنتاغون يعلن عن 'ضربة دقيقة'... أصابت حفل زفاف بالخطأ! 🎯",
            "🇺🇸 الجيش الأمـريكي 'الأقوى في العالم'... لم يربح حرباً منذ 1945! 💪",
            "🇺🇸 قاعدة عسكرية أمـريكية جديدة لـ'حماية السلام'... في بلد لم يطلب الحماية! 🏰",
            "🇺🇸 طائرة بدون طيار أمـريكية تقتل 'إرهابياً'... تبين أنه مزارع! 🤖",
        ],
        'economic': [
            "🇺🇸 الدولار 'أقوى عملة'... مطبوع من الهواء! 💵",
            "🇺🇸 أمـريكا تحذر من 'الديون الصينية'... بينما ديونها 30 تريليون! 📊",
            "🇺🇸 وول ستريت يحتفل بـ'انتعاش الاقتصاد'... بينما الشعب يعاني! 📈",
        ],
        'ironic': [
            "🇺🇸 أمـريكا تتهم روسيا بـ'التدخل في الانتخابات'... وهي خبيرة التدخل! 🗳️",
            "🇺🇸 واشنطن تدافع عن 'حرية الصحافة'... بينما تلاحق أسانج! 📰",
            "🇺🇸 'أرض الأحرار'... حيث أكبر عدد سجناء في العالم! 🗽",
        ]
    },
    'iran': {
        'historical': [
            "🇮🇷 في مثل هذا اليوم، أكدت إيـران أن برنامجها النووي 'سلمي تماماً'... للمرة المليون! ☢️",
            "🇮🇷 ذكرى إعلان طهران عن 'انتصار وشيك'... منذ 40 عاماً! 🏆",
            "🇮🇷 اليوم ذكرى تصريح إيـراني بأن 'إسـرائيل ستزول'... والتصريح أقدم من بعض الدول! 📢",
            "🇮🇷 في مثل هذا اليوم، قال مسؤول إيـراني إن الاقتصاد 'ممتاز'... والريال يبكي! 💰",
            "🇮🇷 ذكرى وعد إيـراني بـ'رد ساحق'... لا زلنا ننتظر منذ سنوات! ⚡",
        ],
        'political': [
            "🇮🇷 المرشد يؤكد أن 'الشعب موحد'... بينما المظاهرات في كل مكان! 🗣️",
            "🇮🇷 طهران تتهم الغرب بـ'التدخل'... بينما تتدخل في كل دول الجوار! 🌍",
            "🇮🇷 الحكومة تعلن 'نجاح الانتخابات'... بنسبة مشاركة 10%! 🗳️",
            "🇮🇷 إيـران تدعم 'المقاومة'... من فنادق خمس نجوم في بيروت! ⭐",
        ],
        'military': [
            "🇮🇷 الحرس الثوري يكشف عن سلاح 'لا مثيل له'... كل أسبوع سلاح جديد! 🚀",
            "🇮🇷 إيـران تعلن 'السيطرة على الخليج'... من شاطئ بندر عباس فقط! 🌊",
            "🇮🇷 صاروخ إيـراني 'يصل تل أبيب'... نظرياً على الورق! 📝",
            "🇮🇷 مناورة عسكرية إيـرانية 'ضخمة'... بثلاث دبابات وقارب! 🎖️",
        ],
        'economic': [
            "🇮🇷 الريال الإيـراني 'مستقر'... عند أدنى مستوى تاريخي! 📉",
            "🇮🇷 طهران تعلن 'كسر العقوبات'... بينما الشعب يبحث عن الخبز! 🍞",
            "🇮🇷 الاقتصاد الإيـراني 'ينمو'... بالاتجاه المعاكس! 📊",
        ],
        'ironic': [
            "🇮🇷 إيـران تدافع عن 'حقوق المرأة'... بإجبارها على الحجاب! 👩",
            "🇮🇷 طهران تنتقد 'القمع الغربي'... بينما تقمع شعبها! 🎭",
            "🇮🇷 'الجمهورية الإسلامية' تحتفل بـ'الحرية'... في أكبر سجن مفتوح! 🔒",
        ]
    },
    'turkey': {
        'historical': [
            "🇹🇷 في مثل هذا اليوم، أعلنت تـركيا أنها 'حامية المسلمين'... بينما تتاجر مع إسـرائيل! 🤝",
            "🇹🇷 ذكرى تصريح أردوغان بأن الليرة 'قوية'... والليرة: لا تعليق! 💸",
            "🇹🇷 اليوم ذكرى إعلان أنقرة عن 'عملية عسكرية أخيرة' في سـوريا... للمرة العاشرة! ⚔️",
            "🇹🇷 في مثل هذا اليوم، قالت تـركيا إنها 'محايدة'... بينما تبيع المسيّرات للجميع! 🛩️",
            "🇹🇷 ذكرى وعد تـركي بـ'حل الأزمة'... وخلق ثلاث أزمات جديدة! 🎪",
        ],
        'political': [
            "🇹🇷 أردوغان يتحدث عن 'الديمقراطية'... بعد سجن كل المعارضين! 🗳️",
            "🇹🇷 أنقرة تنتقد 'الإسلاموفوبيا'... بينما تقصف المسلمين الأكراد! 🕌",
            "🇹🇷 تـركيا 'جسر بين الشرق والغرب'... لا أحد يريد عبوره! 🌉",
            "🇹🇷 الحكومة التـركية تعلن 'الاستقرار'... والليرة تنهار يومياً! 📉",
        ],
        'military': [
            "🇹🇷 الجيش التـركي يعلن 'تحرير' منطقة... كانت محررة أصلاً! 🎖️",
            "🇹🇷 مسيّرة تـركية 'الأفضل في العالم'... حسب تـركيا فقط! 🤖",
            "🇹🇷 عملية عسكرية تـركية 'ناجحة'... أسفرت عن صفر نتائج! 💥",
        ],
        'economic': [
            "🇹🇷 الليرة التـركية 'تتعافى'... من 8 إلى 30 مقابل الدولار! 💰",
            "🇹🇷 أردوغان: 'الفائدة حرام'... والتضخم 80% حلال! 📊",
            "🇹🇷 الاقتصاد التـركي 'ينمو'... نحو الهاوية! 📉",
        ],
        'ironic': [
            "🇹🇷 تـركيا في الناتو لـ'حماية الغرب'... بينما تشتري S-400 من روسيا! 🛡️",
            "🇹🇷 أنقرة تريد الانضمام للاتحاد الأوروبي... منذ 60 سنة والباب مغلق! 🚪",
            "🇹🇷 'الديمقراطية التـركية'... حيث الفائز معروف مسبقاً! 🎭",
        ]
    },
    'russia': {
        'historical': [
            "🇷🇺 في مثل هذا اليوم، أعلنت روسـيا عن 'عملية عسكرية خاصة'... مستمرة منذ سنوات! ⚔️",
            "🇷🇺 ذكرى تصريح الكرملين بأن 'كل شيء يسير حسب الخطة'... أي خطة؟! 📋",
            "🇷🇺 اليوم ذكرى إعلان موسكو أنها 'لا تتدخل' في شؤون الدول... 😂",
            "🇷🇺 في مثل هذا اليوم، قال بوتين إن العقوبات 'لا تؤثر'... والروبل يرتجف! 💰",
            "🇷🇺 ذكرى وعد روسـي بـ'انتصار سريع'... منذ ثلاث سنوات! 🏆",
        ],
        'political': [
            "🇷🇺 بوتين يفوز بالانتخابات بـ'نزاهة'... بنسبة 146%! 🗳️",
            "🇷🇺 الكرملين يدافع عن 'حرية التعبير'... بسجن كل من يعبّر! 🗣️",
            "🇷🇺 روسـيا 'ديمقراطية'... بمرشح واحد فقط! 🎭",
            "🇷🇺 لافروف يتحدث عن 'السلام'... بينما الصواريخ تنطلق! 🕊️",
        ],
        'military': [
            "🇷🇺 الجيش الروسـي 'ثاني أقوى جيش'... في أوكرانيا! 💪",
            "🇷🇺 موسكو تعلن 'تدمير 500 دبابة'... أوكرانيا لديها 200 فقط! 🎯",
            "🇷🇺 سلاح روسـي 'لا يُهزم'... تم تدميره في اليوم الأول! 🚀",
            "🇷🇺 'العملية الخاصة' ستنتهي في 3 أيام... مر 1000 يوم! ⏰",
        ],
        'economic': [
            "🇷🇺 الروبل 'أقوى من أي وقت'... بعد منع تداوله دولياً! 💵",
            "🇷🇺 الاقتصاد الروسـي 'ينمو'... بفضل بيع النفط للصين بخصم 50%! 📊",
            "🇷🇺 موسكو: 'العقوبات فشلت'... بينما ماكدونالدز يغادر! 🍔",
        ],
        'ironic': [
            "🇷🇺 روسـيا تحارب 'النازية' في أوكرانيا... برئيس يهودي! 🤔",
            "🇷🇺 الكرملين يتهم الغرب بـ'الكذب'... ثم يكذب! 🎪",
            "🇷🇺 'القوة العظمى' تحتاج مساعدة كوريا الشمالية! 🆘",
        ]
    },
    'saudi': {
        'historical': [
            "🇸🇦 في مثل هذا اليوم، أعلنت السعـودية عن 'رؤية 2030'... ولا زلنا في 2026! 👀",
            "🇸🇦 ذكرى تصريح سعـودي بأن النفط 'سيبقى للأبد'... والعالم يتحول للطاقة النظيفة! ⛽",
            "🇸🇦 اليوم ذكرى إعلان الرياض عن 'إصلاحات جذرية'... جذرية جداً! 🌱",
            "🇸🇦 في مثل هذا اليوم، قالت السعـودية إنها 'قائدة العالم العربي'... والعرب: من قال؟! 👑",
            "🇸🇦 ذكرى مشروع سعـودي ضخم آخر... بميزانية أضخم وتنفيذ أبطأ! 🏗️",
        ],
        'political': [
            "🇸🇦 ابن سلمان يتحدث عن 'الانفتاح'... بعد إغلاق كل الأصوات المعارضة! 🗣️",
            "🇸🇦 السعـودية 'تدعم فلسطين'... بالتصريحات فقط! 🇵🇸",
            "🇸🇦 الرياض تنتقد 'التطرف'... بينما تصدّر الوهابية! 📚",
            "🇸🇦 'الإصلاح' السعـودي: حفلات موسيقية نعم، حرية تعبير لا! 🎵",
        ],
        'military': [
            "🇸🇦 الجيش السعـودي 'من الأقوى'... بالميزانية فقط! 💰",
            "🇸🇦 حرب اليـمن 'ستنتهي قريباً'... منذ 9 سنوات! ⚔️",
            "🇸🇦 أسلحة أمـريكية بالمليارات... لا أحد يعرف استخدامها! 🎖️",
        ],
        'economic': [
            "🇸🇦 'نيوم' ستكون جاهزة قريباً... في عام 2100 ربما! 🏙️",
            "🇸🇦 السعـودية تستثمر في 'المستقبل'... بشراء أندية كرة قدم! ⚽",
            "🇸🇦 'تنويع الاقتصاد'... 90% لا زال من النفط! 🛢️",
        ],
        'ironic': [
            "🇸🇦 السعـودية تستضيف 'قمة حقوق الإنسان'... بدون تعليق! 😶",
            "🇸🇦 'رؤية 2030' للمرأة... قيادة السيارة بعد 70 سنة انتظار! 🚗",
            "🇸🇦 الرياض 'مركز السياحة'... في صحراء 50 درجة! 🏜️",
        ]
    }
}

# Sarcasm styles
SARCASM_STYLES = {
    'لاذع': {'emoji': '🔥', 'intensity': 'high', 'desc': 'سخرية حادة ولاذعة'},
    'تهكمي': {'emoji': '😈', 'intensity': 'high', 'desc': 'تهكم وسخرية مريرة'},
    'ساخر': {'emoji': '😏', 'intensity': 'medium', 'desc': 'سخرية متوسطة'},
    'فكاهي': {'emoji': '😂', 'intensity': 'low', 'desc': 'سخرية خفيفة وفكاهية'},
    'خفيف': {'emoji': '🙂', 'intensity': 'low', 'desc': 'تعليق ساخر خفيف'},
}

def add_hidden_signature(text):
    signature = "iraqiBoy"
    zwc = {'i': '\u200b', 'r': '\u200c', 'a': '\u200d', 'q': '\ufeff',
           'B': '\u200b\u200c', 'o': '\u200c\u200d', 'y': '\u200d\u200b'}
    hidden = ''.join(zwc.get(c, '') for c in signature)
    return text + hidden

def get_sarcasm_news(country, category=None, style=None):
    """Get a sarcasm news from the library"""
    if country not in SARCASM_LIBRARY:
        return None
    
    library = SARCASM_LIBRARY[country]
    
    if category and category in library:
        news_list = library[category]
    else:
        # Combine all categories
        news_list = []
        for cat_news in library.values():
            news_list.extend(cat_news)
    
    if not news_list:
        return None
    
    news = random.choice(news_list)
    news = beautify_text(news)
    return add_hidden_signature(news)

def generate_ai_sarcasm(country, style='ساخر'):
    """Generate AI-powered sarcasm"""
    if not client or country not in COUNTRY_INFO:
        return get_sarcasm_news(country)
    
    info = COUNTRY_INFO[country]
    style_info = SARCASM_STYLES.get(style, SARCASM_STYLES['ساخر'])
    
    try:
        prompt = f"""أنت كاتب ساخر محترف. اكتب خبراً ساخراً عن {info['name']}.

معلومات للاستخدام:
- أسماء بديلة: {', '.join(info['alt_names'])}
- قادة/مؤسسات: {', '.join(info['leaders'])}
- مؤسسات: {', '.join(info['institutions'])}

أسلوب السخرية: {style} ({style_info['desc']})

قواعد:
1. جملة أو جملتين فقط
2. استخدم علامات تنصيص للسخرية
3. أضف إيموجي مناسب في النهاية
4. لا تستخدم كلمة "عاجل"
5. كن ساخراً بذكاء
6. استخدم ـ لتجميل الكلمات (مثل: العـراق، إسـرائيل)"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"اكتب خبراً ساخراً جديداً عن {info['name']}"}
            ],
            max_tokens=200,
            temperature=0.9
        )
        
        news = response.choices[0].message.content.strip()
        news = beautify_text(news)
        news = f"{info['flag']} {style_info['emoji']} {news}"
        return add_hidden_signature(news)
        
    except Exception as e:
        return get_sarcasm_news(country)

def send_to_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHANNEL_ID, "text": text}
        response = requests.post(url, data=data)
        return response.json().get('ok', False)
    except:
        return False

# Auto sarcasm workers
def sarcasm_auto_worker(country):
    """Worker for auto-publishing sarcasm for a specific country"""
    global sarcasm_auto_active
    
    while sarcasm_auto_active.get(country, False):
        try:
            data = load_data()
            settings = data.get('settings', {})
            country_settings = settings.get('country_sarcasm', {}).get(country, {})
            
            if not country_settings.get('auto_enabled', False):
                time.sleep(60)
                continue
            
            interval = country_settings.get('auto_interval', 60) * 60
            style = country_settings.get('style', 'ساخر')
            
            # Alternate between library and AI
            if random.random() > 0.5 and client:
                news = generate_ai_sarcasm(country, style)
            else:
                news = get_sarcasm_news(country)
            
            if news and send_to_telegram(news):
                data['news'].append({
                    "id": len(data['news']) + 1,
                    "text": news,
                    "sarcasm": True,
                    "country": country,
                    "auto": True,
                    "time": datetime.now().isoformat()
                })
                if 'sarcasm_stats' not in data:
                    data['sarcasm_stats'] = {}
                data['sarcasm_stats'][country] = data['sarcasm_stats'].get(country, 0) + 1
                save_data(data)
            
            time.sleep(interval)
            
        except Exception as e:
            time.sleep(60)

def start_sarcasm_auto(country):
    global sarcasm_auto_active
    if not sarcasm_auto_active.get(country, False):
        sarcasm_auto_active[country] = True
        thread = threading.Thread(target=sarcasm_auto_worker, args=(country,), daemon=True)
        thread.start()

def stop_sarcasm_auto(country):
    global sarcasm_auto_active
    sarcasm_auto_active[country] = False

# Standard functions
COUNTRY_FLAGS = {
    'العراق': '🇮🇶', 'عراق': '🇮🇶', 'العـراق': '🇮🇶',
    'إيران': '🇮🇷', 'ايران': '🇮🇷', 'إيـران': '🇮🇷',
    'إسرائيل': '🇮🇱', 'اسرائيل': '🇮🇱', 'إسـرائيل': '🇮🇱', 'الكيان': '🇮🇱', 'الاحتلال': '🇮🇱',
    'أمريكا': '🇺🇸', 'امريكا': '🇺🇸', 'أمـريكا': '🇺🇸',
    'سوريا': '🇸🇾', 'سـوريا': '🇸🇾',
    'لبنان': '🇱🇧', 'لبـنان': '🇱🇧',
    'السعودية': '🇸🇦', 'السعـودية': '🇸🇦',
    'تركيا': '🇹🇷', 'تـركيا': '🇹🇷',
    'روسيا': '🇷🇺', 'روسـيا': '🇷🇺',
    'اليمن': '🇾🇪', 'اليـمن': '🇾🇪',
    'فلسطين': '🇵🇸', 'فلسـطين': '🇵🇸', 'غزة': '🇵🇸',
}

NEWS_EMOJIS = {
    'انفجار': '💥', 'تفجير': '💥', 'قصف': '💥',
    'غارة': '✈️', 'غارات': '✈️',
    'صاروخ': '🚀', 'صواريخ': '🚀',
    'تصريح': '📢', 'أعلن': '📢', 'صرح': '📢',
    'عسكري': '🎖️', 'جيش': '🎖️', 'مناورة': '🎖️',
    'حرب': '⚔️', 'هجوم': '⚔️', 'اشتباك': '⚔️',
    'اقتصاد': '💰', 'دولار': '💰',
}

AD_KEYWORDS = ['إعلان', 'رابط', 'خصم', 'عرض', 'للتواصل', 'اشترك', 'تابعنا', 't.me/', '@']

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

def rewrite_with_ai(text, settings=None):
    if settings is None:
        data = load_data()
        settings = data.get('settings', get_default_data()['settings'])
    
    if settings.get('beautify_text', True):
        text = beautify_text(text)
    
    flags = get_flags(text)
    emoji = get_emoji(text)
    flags_str = '/'.join(flags) if flags else '🌍'
    
    if not client:
        result = f"ـ {flags_str} {emoji} {text[:200]}"
        return add_hidden_signature(result)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أعد صياغة الخبر بإيجاز. جملتين فقط. بدون عاجل أو توقيع. استخدم ـ لتجميل الكلمات."},
                {"role": "user", "content": text}
            ],
            max_tokens=200,
            temperature=settings.get('creativity', 0.5)
        )
        
        rewritten = response.choices[0].message.content.strip()
        rewritten = beautify_text(rewritten)
        final = f"ـ {flags_str} {emoji} {rewritten}"
        return add_hidden_signature(final)
        
    except:
        result = f"ـ {flags_str} {emoji} {text[:200]}"
        return add_hidden_signature(result)

# HTML Template - Professional Sarcasm System
HTML = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ما وراء - لوحة التحكم الاحترافية</title>
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
        .nav-btn:hover, .nav-btn.active { background: linear-gradient(145deg, #e74c3c, #c0392b); border-color: #e74c3c; }
        .section { display: none; background: linear-gradient(145deg, #192734, #15202b); border-radius: 15px; padding: 25px; margin-bottom: 20px; border: 1px solid #2d4a5e; }
        .section.active { display: block; }
        .section h2 { color: #e74c3c; margin-bottom: 20px; font-size: 1.5em; border-bottom: 2px solid #2d4a5e; padding-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(145deg, #1e2d3d, #152028); padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #2d4a5e; }
        .stat-card h3 { color: #8899a6; font-size: 0.85em; margin-bottom: 8px; }
        .stat-card .value { font-size: 1.8em; color: #e74c3c; font-weight: bold; }
        textarea, input[type="text"], input[type="number"] { width: 100%; padding: 15px; background: #0f1419; border: 2px solid #2d4a5e; border-radius: 10px; color: #fff; font-size: 1em; font-family: 'Cairo'; margin-bottom: 15px; }
        select { width: 100%; padding: 12px; background: #0f1419; border: 2px solid #2d4a5e; border-radius: 10px; color: #fff; font-size: 1em; font-family: 'Cairo'; margin-bottom: 15px; }
        .btn { background: linear-gradient(145deg, #e74c3c, #c0392b); color: white; border: none; padding: 12px 20px; border-radius: 10px; cursor: pointer; font-size: 1em; font-family: 'Cairo'; font-weight: 600; transition: all 0.3s; display: inline-flex; align-items: center; gap: 8px; margin: 3px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(231, 76, 60, 0.3); }
        .btn-success { background: linear-gradient(145deg, #27ae60, #1e8449); }
        .btn-warning { background: linear-gradient(145deg, #f39c12, #d68910); }
        .btn-info { background: linear-gradient(145deg, #3498db, #2980b9); }
        .btn-purple { background: linear-gradient(145deg, #9b59b6, #8e44ad); }
        .btn-dark { background: linear-gradient(145deg, #34495e, #2c3e50); }
        .btn-small { padding: 8px 12px; font-size: 0.85em; }
        .btn-tiny { padding: 5px 10px; font-size: 0.8em; }
        .toggle-container { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; }
        .toggle { position: relative; width: 50px; height: 26px; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #2d4a5e; transition: .4s; border-radius: 26px; }
        .toggle-slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        .toggle input:checked + .toggle-slider { background-color: #e74c3c; }
        .toggle input:checked + .toggle-slider:before { transform: translateX(24px); }
        .country-card { background: linear-gradient(145deg, #152028, #0f1419); padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #2d4a5e; transition: all 0.3s; }
        .country-card.enabled { border-color: #e74c3c; box-shadow: 0 0 20px rgba(231, 76, 60, 0.2); }
        .country-card.auto-active { border-color: #27ae60; box-shadow: 0 0 20px rgba(39, 174, 96, 0.3); animation: pulse-green 2s infinite; }
        @keyframes pulse-green { 0%, 100% { box-shadow: 0 0 20px rgba(39, 174, 96, 0.3); } 50% { box-shadow: 0 0 30px rgba(39, 174, 96, 0.5); } }
        .country-header { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #2d4a5e; }
        .country-flag { font-size: 2.5em; }
        .country-info { flex: 1; }
        .country-name { color: #fff; font-size: 1.3em; font-weight: bold; }
        .country-stats { color: #8899a6; font-size: 0.9em; margin-top: 5px; }
        .country-controls { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
        .control-group { background: #0f1419; padding: 15px; border-radius: 10px; }
        .control-group label { display: block; color: #8899a6; margin-bottom: 8px; font-size: 0.9em; }
        .category-buttons { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; }
        .auto-section { background: linear-gradient(145deg, #1a3a1a, #0f2a0f); padding: 15px; border-radius: 10px; border: 1px solid #27ae60; margin-top: 15px; }
        .auto-section h4 { color: #27ae60; margin-bottom: 10px; }
        .auto-status { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; }
        .status-dot.active { background: #27ae60; animation: blink 1s infinite; }
        .status-dot.inactive { background: #e74c3c; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .result-box { background: #0f1419; border: 2px solid #27ae60; border-radius: 10px; padding: 20px; margin-top: 20px; white-space: pre-wrap; line-height: 1.8; }
        .result-box.error { border-color: #e74c3c; }
        .loading { display: none; text-align: center; padding: 20px; }
        .loading.show { display: block; }
        .spinner { border: 4px solid #2d4a5e; border-top: 4px solid #e74c3c; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .footer { text-align: center; padding: 20px; color: #8899a6; border-top: 1px solid #2d4a5e; margin-top: 30px; }
        .quick-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .quick-action { background: linear-gradient(145deg, #1e2d3d, #152028); padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #2d4a5e; cursor: pointer; transition: all 0.3s; }
        .quick-action:hover { transform: translateY(-5px); border-color: #e74c3c; }
        .quick-action .icon { font-size: 2em; margin-bottom: 10px; }
        .quick-action .title { color: #fff; font-weight: bold; }
        .quick-action .desc { color: #8899a6; font-size: 0.85em; margin-top: 5px; }
        @media (max-width: 768px) { .country-controls { grid-template-columns: 1fr; } .quick-actions { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔴 ما وراء</h1>
            <p>نظام إدارة الأخـبار الاحـترافي ـ نظام السخـرية المتقدم</p>
        </div>
        
        <div class="nav">
            <button class="nav-btn active" onclick="showSection('dashboard')">📊 الرئيسية</button>
            <button class="nav-btn" onclick="showSection('sarcasm')">😏 السخـرية المتقدمة</button>
            <button class="nav-btn" onclick="showSection('news')">📰 الأخـبار</button>
            <button class="nav-btn" onclick="showSection('settings')">⚙️ الإعدادات</button>
        </div>
        
        <div id="dashboard" class="section active">
            <h2>📊 لوحة المعلومات</h2>
            <div class="stats">
                <div class="stat-card"><h3>إجمالي الأخـبار</h3><div class="value" id="total-news">0</div></div>
                <div class="stat-card"><h3>أخـبار ساخرة</h3><div class="value" id="sarcasm-news">0</div></div>
                <div class="stat-card"><h3>🇮🇱 إسـرائيل</h3><div class="value" id="stat-israel">0</div></div>
                <div class="stat-card"><h3>🇺🇸 أمـريكا</h3><div class="value" id="stat-usa">0</div></div>
                <div class="stat-card"><h3>🇮🇷 إيـران</h3><div class="value" id="stat-iran">0</div></div>
                <div class="stat-card"><h3>🇹🇷 تـركيا</h3><div class="value" id="stat-turkey">0</div></div>
                <div class="stat-card"><h3>🇷🇺 روسـيا</h3><div class="value" id="stat-russia">0</div></div>
                <div class="stat-card"><h3>🇸🇦 السعـودية</h3><div class="value" id="stat-saudi">0</div></div>
            </div>
            
            <h3 style="color: #e74c3c; margin-bottom: 15px;">⚡ إجراءات سريعة</h3>
            <div class="quick-actions">
                <div class="quick-action" onclick="quickSarcasm('israel')">
                    <div class="icon">🇮🇱</div>
                    <div class="title">سخرية إسـرائيل</div>
                    <div class="desc">إرسال خبر ساخر فوري</div>
                </div>
                <div class="quick-action" onclick="quickSarcasm('usa')">
                    <div class="icon">🇺🇸</div>
                    <div class="title">سخرية أمـريكا</div>
                    <div class="desc">إرسال خبر ساخر فوري</div>
                </div>
                <div class="quick-action" onclick="quickSarcasm('iran')">
                    <div class="icon">🇮🇷</div>
                    <div class="title">سخرية إيـران</div>
                    <div class="desc">إرسال خبر ساخر فوري</div>
                </div>
                <div class="quick-action" onclick="startAllAuto()">
                    <div class="icon">🤖</div>
                    <div class="title">تشغيل الكل</div>
                    <div class="desc">تفعيل النشر التلقائي للجميع</div>
                </div>
            </div>
            
            <div id="quick-result" style="margin-top: 20px;"></div>
        </div>
        
        <div id="sarcasm" class="section">
            <h2>😏 نظام السخـرية المتقدم</h2>
            <p style="color: #8899a6; margin-bottom: 20px;">نظام سخرية احترافي مع مكتبة ضخمة وتكرار تلقائي وأنماط متعددة!</p>
            
            <div id="countries-list"></div>
            
            <div id="sarcasm-result" style="margin-top: 20px;"></div>
        </div>
        
        <div id="news" class="section">
            <h2>📰 إضافة خبر</h2>
            <textarea id="news-text" rows="4" placeholder="أدخل الخبر هنا..."></textarea>
            <button class="btn btn-success" onclick="sendNews()">🚀 صياغة وإرسال</button>
            <div class="loading" id="news-loading"><div class="spinner"></div><p>جاري المعالجة...</p></div>
            <div id="news-result"></div>
        </div>
        
        <div id="settings" class="section">
            <h2>⚙️ الإعدادات</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                <div class="control-group">
                    <label>📏 طول الخبر</label>
                    <select id="news-length" onchange="saveSettings()">
                        <option value="short">قصير</option>
                        <option value="medium" selected>متوسط</option>
                        <option value="long">طويل</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>✨ تجميل الخطوط</label>
                    <div class="toggle-container">
                        <span>إضافة ـ للكلمات</span>
                        <label class="toggle">
                            <input type="checkbox" id="beautify-toggle" checked onchange="saveSettings()">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2026 نظام ما وراء | النسخة الاحترافية المتقدمة</p>
        </div>
    </div>
    
    <script>
        const countries = ['israel', 'usa', 'iran', 'turkey', 'russia', 'saudi'];
        const countryNames = {
            israel: 'إسـرائيل', usa: 'أمـريكا', iran: 'إيـران',
            turkey: 'تـركيا', russia: 'روسـيا', saudi: 'السعـودية'
        };
        const countryFlags = {
            israel: '🇮🇱', usa: '🇺🇸', iran: '🇮🇷',
            turkey: '🇹🇷', russia: '🇷🇺', saudi: '🇸🇦'
        };
        const categories = ['historical', 'political', 'military', 'economic', 'ironic'];
        const categoryNames = {
            historical: '📜 تاريخي', political: '🏛️ سياسي', military: '⚔️ عسكري',
            economic: '💰 اقتصادي', ironic: '🎭 ساخر'
        };
        const styles = ['لاذع', 'تهكمي', 'ساخر', 'فكاهي', 'خفيف'];
        
        let currentSettings = {};
        let autoStatus = {};
        
        function showSection(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
        }
        
        function renderCountries() {
            const container = document.getElementById('countries-list');
            let html = '';
            
            countries.forEach(country => {
                const isAuto = autoStatus[country] || false;
                html += `
                <div class="country-card ${isAuto ? 'auto-active' : ''}" id="card-${country}">
                    <div class="country-header">
                        <span class="country-flag">${countryFlags[country]}</span>
                        <div class="country-info">
                            <div class="country-name">${countryNames[country]}</div>
                            <div class="country-stats">أخبار منشورة: <span id="count-${country}">0</span></div>
                        </div>
                        <label class="toggle">
                            <input type="checkbox" id="enabled-${country}" onchange="toggleCountry('${country}')">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    
                    <div class="country-controls">
                        <div class="control-group">
                            <label>🎨 أسلوب السخرية</label>
                            <select id="style-${country}" onchange="updateCountrySettings('${country}')">
                                ${styles.map(s => `<option value="${s}">${s}</option>`).join('')}
                            </select>
                        </div>
                        <div class="control-group">
                            <label>⏰ فاصل التكرار (دقيقة)</label>
                            <input type="number" id="interval-${country}" value="60" min="5" max="180" onchange="updateCountrySettings('${country}')">
                        </div>
                    </div>
                    
                    <div class="category-buttons">
                        ${categories.map(cat => `
                            <button class="btn btn-small btn-dark" onclick="sendCategory('${country}', '${cat}')">${categoryNames[cat]}</button>
                        `).join('')}
                    </div>
                    
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px;">
                        <button class="btn btn-small btn-info" onclick="sendLibrary('${country}')">📚 من المكتبة</button>
                        <button class="btn btn-small btn-purple" onclick="sendAI('${country}')">🤖 ذكاء اصطناعي</button>
                        <button class="btn btn-small btn-warning" onclick="sendRandom('${country}')">🎲 عشوائي</button>
                        <button class="btn btn-small" onclick="sendMultiple('${country}', 3)">📤 إرسال 3</button>
                        <button class="btn btn-small" onclick="sendMultiple('${country}', 5)">📤 إرسال 5</button>
                    </div>
                    
                    <div class="auto-section">
                        <h4>🤖 النشر التلقائي المتكرر</h4>
                        <div class="auto-status">
                            <div class="status-dot ${isAuto ? 'active' : 'inactive'}" id="dot-${country}"></div>
                            <span id="auto-text-${country}">${isAuto ? 'يعمل الآن...' : 'متوقف'}</span>
                        </div>
                        <div class="toggle-container">
                            <span>تفعيل التكرار التلقائي</span>
                            <label class="toggle">
                                <input type="checkbox" id="auto-${country}" ${isAuto ? 'checked' : ''} onchange="toggleAuto('${country}')">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function loadStats() {
            fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('total-news').textContent = data.total || 0;
                document.getElementById('sarcasm-news').textContent = data.sarcasm || 0;
                countries.forEach(c => {
                    document.getElementById('stat-' + c).textContent = data.countries[c] || 0;
                    const countEl = document.getElementById('count-' + c);
                    if (countEl) countEl.textContent = data.countries[c] || 0;
                });
            });
        }
        
        function loadSettings() {
            fetch('/api/settings')
            .then(r => r.json())
            .then(data => {
                currentSettings = data;
                document.getElementById('news-length').value = data.news_length || 'medium';
                document.getElementById('beautify-toggle').checked = data.beautify_text !== false;
                
                const cs = data.country_sarcasm || {};
                countries.forEach(c => {
                    const settings = cs[c] || {};
                    const enabledEl = document.getElementById('enabled-' + c);
                    const styleEl = document.getElementById('style-' + c);
                    const intervalEl = document.getElementById('interval-' + c);
                    const autoEl = document.getElementById('auto-' + c);
                    
                    if (enabledEl) enabledEl.checked = settings.enabled || false;
                    if (styleEl) styleEl.value = settings.style || 'ساخر';
                    if (intervalEl) intervalEl.value = settings.auto_interval || 60;
                    if (autoEl) {
                        autoEl.checked = settings.auto_enabled || false;
                        autoStatus[c] = settings.auto_enabled || false;
                        updateAutoUI(c, settings.auto_enabled);
                    }
                });
            });
        }
        
        function saveSettings() {
            const settings = {
                news_length: document.getElementById('news-length').value,
                beautify_text: document.getElementById('beautify-toggle').checked
            };
            fetch('/api/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            });
        }
        
        function toggleCountry(country) {
            const enabled = document.getElementById('enabled-' + country).checked;
            updateCountrySettings(country);
            document.getElementById('card-' + country).classList.toggle('enabled', enabled);
        }
        
        function updateCountrySettings(country) {
            const enabled = document.getElementById('enabled-' + country).checked;
            const style = document.getElementById('style-' + country).value;
            const interval = document.getElementById('interval-' + country).value;
            const autoEnabled = document.getElementById('auto-' + country).checked;
            
            fetch('/api/settings/country', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    country: country,
                    enabled: enabled,
                    style: style,
                    auto_interval: parseInt(interval),
                    auto_enabled: autoEnabled
                })
            });
        }
        
        function updateAutoUI(country, active) {
            const dot = document.getElementById('dot-' + country);
            const text = document.getElementById('auto-text-' + country);
            const card = document.getElementById('card-' + country);
            
            if (dot) dot.className = 'status-dot ' + (active ? 'active' : 'inactive');
            if (text) text.textContent = active ? 'يعمل الآن... 🟢' : 'متوقف 🔴';
            if (card) card.classList.toggle('auto-active', active);
        }
        
        function toggleAuto(country) {
            const enabled = document.getElementById('auto-' + country).checked;
            autoStatus[country] = enabled;
            updateAutoUI(country, enabled);
            updateCountrySettings(country);
            
            fetch('/api/sarcasm/auto', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({country: country, enabled: enabled})
            });
        }
        
        function showResult(message, success = true) {
            const resultDiv = document.getElementById('sarcasm-result');
            resultDiv.innerHTML = `<div class="result-box ${success ? '' : 'error'}">${message}</div>`;
            resultDiv.scrollIntoView({behavior: 'smooth'});
        }
        
        function sendCategory(country, category) {
            showResult('<div class="loading show"><div class="spinner"></div><p>جاري الإرسال...</p></div>');
            fetch('/api/sarcasm/category', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({country: country, category: category})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('✅ تم الإرسال!<br><br>' + data.news);
                    loadStats();
                } else {
                    showResult('❌ ' + data.message, false);
                }
            });
        }
        
        function sendLibrary(country) {
            showResult('<div class="loading show"><div class="spinner"></div><p>جاري الإرسال...</p></div>');
            fetch('/api/sarcasm/library', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({country: country})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('✅ تم الإرسال من المكتبة!<br><br>' + data.news);
                    loadStats();
                } else {
                    showResult('❌ ' + data.message, false);
                }
            });
        }
        
        function sendAI(country) {
            const style = document.getElementById('style-' + country).value;
            showResult('<div class="loading show"><div class="spinner"></div><p>الذكاء الاصطناعي يكتب...</p></div>');
            fetch('/api/sarcasm/ai', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({country: country, style: style})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('✅ تم الإرسال (AI)!<br><br>' + data.news);
                    loadStats();
                } else {
                    showResult('❌ ' + data.message, false);
                }
            });
        }
        
        function sendRandom(country) {
            showResult('<div class="loading show"><div class="spinner"></div><p>جاري الإرسال...</p></div>');
            fetch('/api/sarcasm/random', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({country: country})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('✅ تم الإرسال!<br><br>' + data.news);
                    loadStats();
                } else {
                    showResult('❌ ' + data.message, false);
                }
            });
        }
        
        function sendMultiple(country, count) {
            showResult('<div class="loading show"><div class="spinner"></div><p>جاري إرسال ' + count + ' أخبار...</p></div>');
            fetch('/api/sarcasm/multiple', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({country: country, count: count})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('✅ تم إرسال ' + data.sent + ' أخبار!<br><br>' + data.news.join('<br><br>'));
                    loadStats();
                } else {
                    showResult('❌ ' + data.message, false);
                }
            });
        }
        
        function quickSarcasm(country) {
            const resultDiv = document.getElementById('quick-result');
            resultDiv.innerHTML = '<div class="loading show"><div class="spinner"></div><p>جاري الإرسال...</p></div>';
            fetch('/api/sarcasm/random', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({country: country})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    resultDiv.innerHTML = '<div class="result-box">✅ تم الإرسال!<br><br>' + data.news + '</div>';
                    loadStats();
                } else {
                    resultDiv.innerHTML = '<div class="result-box error">❌ ' + data.message + '</div>';
                }
            });
        }
        
        function startAllAuto() {
            countries.forEach(c => {
                document.getElementById('auto-' + c).checked = true;
                toggleAuto(c);
            });
            alert('✅ تم تفعيل النشر التلقائي لجميع الدول!');
        }
        
        function sendNews() {
            const text = document.getElementById('news-text').value;
            if (!text) { alert('أدخل الخبر'); return; }
            document.getElementById('news-loading').classList.add('show');
            fetch('/api/news/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('news-loading').classList.remove('show');
                document.getElementById('news-result').innerHTML = data.success 
                    ? '<div class="result-box">✅ تم الإرسال!<br><br>' + data.result + '</div>'
                    : '<div class="result-box error">❌ ' + data.message + '</div>';
                if (data.success) document.getElementById('news-text').value = '';
            });
        }
        
        renderCountries();
        loadStats();
        loadSettings();
        setInterval(loadStats, 30000);
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/stats')
def api_stats():
    data = load_data()
    news = data.get('news', [])
    stats = data.get('sarcasm_stats', {})
    
    sarcasm_count = sum(1 for n in news if n.get('sarcasm'))
    
    return jsonify({
        "total": len(news),
        "sarcasm": sarcasm_count,
        "countries": stats
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    data = load_data()
    if request.method == 'POST':
        new_settings = request.json
        data['settings'].update(new_settings)
        save_data(data)
        return jsonify({"message": "تم الحفظ"})
    return jsonify(data.get('settings', get_default_data()['settings']))

@app.route('/api/settings/country', methods=['POST'])
def api_country_settings():
    data = load_data()
    req = request.json
    country = req.get('country')
    
    if country:
        if 'country_sarcasm' not in data['settings']:
            data['settings']['country_sarcasm'] = {}
        
        data['settings']['country_sarcasm'][country] = {
            'enabled': req.get('enabled', False),
            'style': req.get('style', 'ساخر'),
            'auto_interval': req.get('auto_interval', 60),
            'auto_enabled': req.get('auto_enabled', False)
        }
        save_data(data)
        
        # Start/stop auto worker
        if req.get('auto_enabled'):
            start_sarcasm_auto(country)
        else:
            stop_sarcasm_auto(country)
    
    return jsonify({"message": "تم التحديث"})

@app.route('/api/sarcasm/auto', methods=['POST'])
def api_sarcasm_auto():
    req = request.json
    country = req.get('country')
    enabled = req.get('enabled', False)
    
    if enabled:
        start_sarcasm_auto(country)
    else:
        stop_sarcasm_auto(country)
    
    return jsonify({"message": "تم التحديث", "status": enabled})

@app.route('/api/sarcasm/category', methods=['POST'])
def api_sarcasm_category():
    req = request.json
    country = req.get('country')
    category = req.get('category')
    
    news = get_sarcasm_news(country, category)
    if news and send_to_telegram(news):
        data = load_data()
        data['news'].append({"id": len(data['news']) + 1, "text": news, "sarcasm": True, "country": country})
        data['sarcasm_stats'][country] = data['sarcasm_stats'].get(country, 0) + 1
        save_data(data)
        return jsonify({"success": True, "news": news})
    
    return jsonify({"success": False, "message": "فشل الإرسال"})

@app.route('/api/sarcasm/library', methods=['POST'])
def api_sarcasm_library():
    req = request.json
    country = req.get('country')
    
    news = get_sarcasm_news(country)
    if news and send_to_telegram(news):
        data = load_data()
        data['news'].append({"id": len(data['news']) + 1, "text": news, "sarcasm": True, "country": country})
        data['sarcasm_stats'][country] = data['sarcasm_stats'].get(country, 0) + 1
        save_data(data)
        return jsonify({"success": True, "news": news})
    
    return jsonify({"success": False, "message": "فشل الإرسال"})

@app.route('/api/sarcasm/ai', methods=['POST'])
def api_sarcasm_ai():
    req = request.json
    country = req.get('country')
    style = req.get('style', 'ساخر')
    
    news = generate_ai_sarcasm(country, style)
    if news and send_to_telegram(news):
        data = load_data()
        data['news'].append({"id": len(data['news']) + 1, "text": news, "sarcasm": True, "country": country, "ai": True})
        data['sarcasm_stats'][country] = data['sarcasm_stats'].get(country, 0) + 1
        save_data(data)
        return jsonify({"success": True, "news": news})
    
    return jsonify({"success": False, "message": "فشل الإرسال"})

@app.route('/api/sarcasm/random', methods=['POST'])
def api_sarcasm_random():
    req = request.json
    country = req.get('country')
    
    # 50% chance for AI, 50% for library
    if random.random() > 0.5 and client:
        news = generate_ai_sarcasm(country)
    else:
        news = get_sarcasm_news(country)
    
    if news and send_to_telegram(news):
        data = load_data()
        data['news'].append({"id": len(data['news']) + 1, "text": news, "sarcasm": True, "country": country})
        data['sarcasm_stats'][country] = data['sarcasm_stats'].get(country, 0) + 1
        save_data(data)
        return jsonify({"success": True, "news": news})
    
    return jsonify({"success": False, "message": "فشل الإرسال"})

@app.route('/api/sarcasm/multiple', methods=['POST'])
def api_sarcasm_multiple():
    req = request.json
    country = req.get('country')
    count = min(req.get('count', 3), 10)
    
    sent_news = []
    data = load_data()
    
    for i in range(count):
        if random.random() > 0.5 and client:
            news = generate_ai_sarcasm(country)
        else:
            news = get_sarcasm_news(country)
        
        if news and send_to_telegram(news):
            sent_news.append(news)
            data['news'].append({"id": len(data['news']) + 1, "text": news, "sarcasm": True, "country": country})
            data['sarcasm_stats'][country] = data['sarcasm_stats'].get(country, 0) + 1
            time.sleep(2)  # Delay between messages
    
    save_data(data)
    
    if sent_news:
        return jsonify({"success": True, "sent": len(sent_news), "news": sent_news})
    return jsonify({"success": False, "message": "فشل الإرسال"})

@app.route('/api/news/send', methods=['POST'])
def api_news_send():
    data = load_data()
    req = request.json
    text = req.get('text', '')
    
    if is_ad(text):
        return jsonify({"success": False, "message": "يبدو أنه إعلان"})
    
    settings = data.get('settings', {})
    rewritten = rewrite_with_ai(text, settings)
    
    if send_to_telegram(rewritten):
        data['news'].append({"id": len(data['news']) + 1, "text": rewritten})
        save_data(data)
        return jsonify({"success": True, "result": rewritten})
    
    return jsonify({"success": False, "message": "فشل الإرسال"})

@app.route('/api/sources', methods=['GET'])
def api_sources():
    data = load_data()
    return jsonify(data.get('sources', []))

@app.route('/api/news', methods=['GET'])
def api_news():
    data = load_data()
    return jsonify(data.get('news', []))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
