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

# Data storage
NEWS = []
SOURCES = [
    {"id": 1, "name": "المستشار", "username": "Almustashaar", "active": True},
    {"id": 2, "name": "صوت الحرب", "username": "sawtl7arb", "active": True},
    {"id": 3, "name": "تسريبات الحرب", "username": "WarsLeaks", "active": True},
    {"id": 4, "name": "نايا للعراق", "username": "nayaforiraq", "active": True}
]

# Country flags mapping
COUNTRY_FLAGS = {
    'العراق': '🇮🇶', 'عراق': '🇮🇶', 'بغداد': '🇮🇶',
    'إيران': '🇮🇷', 'ايران': '🇮🇷', 'طهران': '🇮🇷',
    'إسرائيل': '🇮🇱', 'اسرائيل': '🇮🇱', 'تل أبيب': '🇮🇱', 'الإسرائيلي': '🇮🇱',
    'أمريكا': '🇺🇸', 'امريكا': '🇺🇸', 'الأمريكي': '🇺🇸', 'واشنطن': '🇺🇸',
    'سوريا': '🇸🇾', 'دمشق': '🇸🇾', 'السوري': '🇸🇾',
    'لبنان': '🇱🇧', 'بيروت': '🇱🇧', 'حزب الله': '🇱🇧',
    'السعودية': '🇸🇦', 'الرياض': '🇸🇦',
    'الإمارات': '🇦🇪', 'أبوظبي': '🇦🇪', 'دبي': '🇦🇪',
    'تركيا': '🇹🇷', 'أنقرة': '🇹🇷',
    'روسيا': '🇷🇺', 'موسكو': '🇷🇺',
    'الصين': '🇨🇳', 'بكين': '🇨🇳',
    'بريطانيا': '🇬🇧', 'لندن': '🇬🇧',
    'فرنسا': '🇫🇷', 'باريس': '🇫🇷',
    'اليمن': '🇾🇪', 'صنعاء': '🇾🇪', 'الحوثي': '🇾🇪',
    'فلسطين': '🇵🇸', 'غزة': '🇵🇸', 'حماس': '🇵🇸',
    'مصر': '🇪🇬', 'القاهرة': '🇪🇬',
    'الأردن': '🇯🇴', 'عمان': '🇯🇴',
    'الكويت': '🇰🇼',
    'قطر': '🇶🇦', 'الدوحة': '🇶🇦',
    'البحرين': '🇧🇭',
    'عمان': '🇴🇲',
    'باكستان': '🇵🇰',
    'أفغانستان': '🇦🇫',
    'الهند': '🇮🇳',
    'كوريا': '🇰🇷',
    'اليابان': '🇯🇵',
    'ألمانيا': '🇩🇪',
    'أوكرانيا': '🇺🇦',
}

# News type emojis
NEWS_EMOJIS = {
    'انفجار': '💥',
    'تفجير': '💥',
    'قصف': '💥',
    'غارة': '✈️',
    'غارات': '✈️',
    'طائرة': '✈️',
    'صاروخ': '🚀',
    'صواريخ': '🚀',
    'تصريح': '📢',
    'تصريحات': '📢',
    'قال': '📢',
    'أعلن': '📢',
    'اجتماع': '🤝',
    'مباحثات': '🤝',
    'عسكري': '🎖️',
    'جيش': '🎖️',
    'قوات': '🎖️',
    'مناورة': '🎖️',
    'اعتقال': '⚠️',
    'احتجاج': '📣',
    'احتجاجات': '📣',
    'مظاهرات': '📣',
    'حرب': '⚔️',
    'هجوم': '⚔️',
    'اشتباك': '⚔️',
    'سياسي': '🏛️',
    'رئيس': '🏛️',
    'وزير': '🏛️',
    'حكومة': '🏛️',
    'اقتصاد': '💰',
    'نفط': '🛢️',
    'طاقة': '⚡',
}

# Ad filter keywords
AD_KEYWORDS = ['إعلان', 'رابط', 'خصم', 'عرض', 'تخفيض', 'للتواصل', 'للحجز', 'اشترك', 'تابعنا', 'رابط القناة', 'انضم', 'اشتراك', 'مجاني', 'فرصة', 'حصري']

def is_ad(text):
    """Check if text is an advertisement"""
    text_lower = text.lower()
    return any(keyword in text for keyword in AD_KEYWORDS)

def get_flags(text):
    """Extract country flags from text"""
    flags = []
    for country, flag in COUNTRY_FLAGS.items():
        if country in text and flag not in flags:
            flags.append(flag)
    return flags[:3]  # Max 3 flags

def get_emoji(text):
    """Get appropriate emoji for news type"""
    for keyword, emoji in NEWS_EMOJIS.items():
        if keyword in text:
            return emoji
    return '📰'  # Default news emoji

def add_hidden_signature(text):
    """Add hidden signature using zero-width characters"""
    signature = "iraqiBoy"
    zwc = {
        'i': '\u200b',  # Zero-width space
        'r': '\u200c',  # Zero-width non-joiner
        'a': '\u200d',  # Zero-width joiner
        'q': '\ufeff',  # Zero-width no-break space
        'B': '\u200b\u200c',
        'o': '\u200c\u200d',
        'y': '\u200d\u200b'
    }
    hidden = ''.join(zwc.get(c, '') for c in signature)
    return text + hidden

def rewrite_with_ai(text):
    """Rewrite news using OpenAI with new format"""
    if not client:
        # Fallback without AI
        flags = get_flags(text)
        emoji = get_emoji(text)
        flags_str = '/'.join(flags) if flags else '🌍'
        return add_hidden_signature(f"{flags_str} {emoji} {text[:200]}")
    
    try:
        flags = get_flags(text)
        emoji = get_emoji(text)
        flags_str = '/'.join(flags) if flags else '🌍'
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """أنت محرر أخبار محترف. مهمتك إعادة صياغة الخبر بشكل:
1. محايد تماماً - بدون أي انحياز سياسي
2. مختصر جداً - جملة أو جملتين فقط
3. واضح ومباشر
4. بدون مقدمات أو خاتمات
5. بدون كلمة "عاجل" في البداية
6. بدون أي توقيع أو اسم قناة
7. فقط الخبر الصافي"""
                },
                {
                    "role": "user",
                    "content": f"أعد صياغة هذا الخبر بشكل مختصر ومحايد (جملة أو جملتين فقط):\n\n{text}"
                }
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        rewritten = response.choices[0].message.content.strip()
        # Remove any "عاجل" if AI added it
        rewritten = rewritten.replace('عاجل:', '').replace('عاجل -', '').replace('عاجل', '').strip()
        
        # Format: FLAGS EMOJI NEWS
        final = f"{flags_str} {emoji} {rewritten}"
        return add_hidden_signature(final)
        
    except Exception as e:
        flags = get_flags(text)
        emoji = get_emoji(text)
        flags_str = '/'.join(flags) if flags else '🌍'
        return add_hidden_signature(f"{flags_str} {emoji} {text[:200]}")

def send_to_telegram(text):
    """Send message to Telegram channel"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHANNEL_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        return response.json().get('ok', False)
    except:
        return False

# HTML Template
HTML = """
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
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
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
        @media (max-width: 768px) { .header h1 { font-size: 1.8em; } .nav-btn { padding: 10px 15px; font-size: 0.9em; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔴 ما وراء</h1>
            <p>نظام إدارة الأخبار والتحديثات المحايد</p>
        </div>
        
        <div class="nav">
            <button class="nav-btn active" onclick="showSection('dashboard')">📊 لوحة المعلومات</button>
            <button class="nav-btn" onclick="showSection('sources')">📡 المصادر</button>
            <button class="nav-btn" onclick="showSection('news')">📰 الأخبار</button>
            <button class="nav-btn" onclick="showSection('rewrite')">✏️ إعادة الصياغة</button>
            <button class="nav-btn" onclick="showSection('settings')">⚙️ الإعدادات</button>
        </div>
        
        <div id="dashboard" class="section active">
            <h2>📊 لوحة المعلومات</h2>
            <div class="stats">
                <div class="stat-card"><h3>الأخبار المنشورة</h3><div class="value" id="news-count">0</div></div>
                <div class="stat-card"><h3>المصادر النشطة</h3><div class="value">4</div></div>
                <div class="stat-card"><h3>حالة النظام</h3><div class="value" style="color: #27ae60;">✓</div></div>
            </div>
            
            <div style="background: #0f1419; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #e74c3c;">
                <h3 style="color: #e74c3c; margin-bottom: 15px;">🚀 النشر السريع</h3>
                <p style="color: #8899a6; margin-bottom: 15px;">صياغة ونشر الأخبار بضغطة واحدة</p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button class="btn btn-success" onclick="publishOne()">📰 نشر خبر واحد</button>
                </div>
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
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn btn-success" onclick="addAndSend()">🚀 صياغة وإرسال للقناة</button>
            </div>
            <div class="loading" id="news-loading"><div class="spinner"></div><p>جاري المعالجة...</p></div>
            <div id="news-result" style="margin-top: 20px;"></div>
            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #e74c3c;">📋 الأخبار المنشورة</h3>
            <div id="news-list"></div>
        </div>
        
        <div id="rewrite" class="section">
            <h2>✏️ إعادة صياغة الخبر</h2>
            <p style="color: #8899a6; margin-bottom: 20px;">أدخل الخبر وسيتم إعادة صياغته بشكل محايد ومختصر:</p>
            <textarea id="rewrite-text" rows="6" placeholder="أدخل الخبر الأصلي هنا..."></textarea>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn" onclick="rewriteNews()">✨ إعادة الصياغة</button>
                <button class="btn btn-success" onclick="rewriteAndSend()">🚀 صياغة وإرسال للقناة</button>
            </div>
            <div class="loading" id="rewrite-loading"><div class="spinner"></div><p>جاري إعادة الصياغة...</p></div>
            <div id="rewrite-result"></div>
        </div>
        
        <div id="settings" class="section">
            <h2>⚙️ الإعدادات</h2>
            <div class="source-item"><div class="source-info"><h4>معرف القناة</h4><span>-1002560480003</span></div></div>
            <div class="source-item"><div class="source-info"><h4>معرف المسؤول</h4><span>5365833232</span></div></div>
            <div class="source-item"><div class="source-info"><h4>حالة OpenAI</h4><span id="openai-status">جاري التحقق...</span></div></div>
        </div>
        
        <div class="footer"><p>© 2026 نظام ما وراء | جميع الحقوق محفوظة</p></div>
    </div>
    
    <script>
        function showSection(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
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
        
        function checkOpenAI() {
            fetch('/api/status')
            .then(r => r.json())
            .then(data => {
                document.getElementById('openai-status').innerHTML = data.openai ? '<span style="color: #27ae60;">✓ متصل</span>' : '<span style="color: #e74c3c;">✗ غير متصل</span>';
            });
        }
        
        // Load on start
        loadSources();
        loadNews();
        checkOpenAI();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/status')
def api_status():
    return jsonify({"openai": bool(OPENAI_API_KEY)})

@app.route('/api/sources', methods=['GET', 'POST'])
def api_sources():
    global SOURCES
    if request.method == 'POST':
        data = request.json
        new_source = {
            "id": len(SOURCES) + 1,
            "name": data.get('name', ''),
            "username": data.get('username', '').replace('@', ''),
            "active": True
        }
        SOURCES.append(new_source)
        return jsonify({"message": "تم إضافة المصدر بنجاح"})
    return jsonify(SOURCES)

@app.route('/api/news', methods=['GET', 'POST'])
def api_news():
    global NEWS
    if request.method == 'POST':
        data = request.json
        NEWS.append({"id": len(NEWS) + 1, "text": data.get('text', '')})
        return jsonify({"message": "تم إضافة الخبر"})
    return jsonify(NEWS)

@app.route('/api/news/send', methods=['POST'])
def api_news_send():
    data = request.json
    text = data.get('text', '')
    
    if is_ad(text):
        return jsonify({"success": False, "message": "تم تجاهل الخبر - يبدو أنه إعلان"})
    
    rewritten = rewrite_with_ai(text)
    
    if send_to_telegram(rewritten):
        NEWS.append({"id": len(NEWS) + 1, "text": rewritten})
        return jsonify({"success": True, "message": "تم إرسال الخبر للقناة", "result": rewritten})
    else:
        return jsonify({"success": False, "message": "فشل إرسال الخبر"})

@app.route('/api/rewrite', methods=['POST'])
def api_rewrite():
    data = request.json
    text = data.get('text', '')
    rewritten = rewrite_with_ai(text)
    return jsonify({"result": rewritten})

@app.route('/api/rewrite/send', methods=['POST'])
def api_rewrite_send():
    data = request.json
    text = data.get('text', '')
    
    if is_ad(text):
        return jsonify({"success": False, "message": "تم تجاهل الخبر - يبدو أنه إعلان"})
    
    rewritten = rewrite_with_ai(text)
    
    if send_to_telegram(rewritten):
        NEWS.append({"id": len(NEWS) + 1, "text": rewritten})
        return jsonify({"success": True, "message": "تم إرسال الخبر للقناة", "result": rewritten})
    else:
        return jsonify({"success": False, "message": "فشل إرسال الخبر"})

@app.route('/api/publish/one', methods=['POST'])
def api_publish_one():
    # Demo news for testing
    demo_news = "وزير الحرب الإسرائيلي يسرائيل كاتس ورئيس الأركان ايال زامير يجريان مناورة تحاكي اندلاع حرب مع إيران"
    
    if is_ad(demo_news):
        return jsonify({"success": False, "message": "تم تجاهل الخبر - يبدو أنه إعلان"})
    
    rewritten = rewrite_with_ai(demo_news)
    
    if send_to_telegram(rewritten):
        NEWS.append({"id": len(NEWS) + 1, "text": rewritten})
        return jsonify({"success": True, "message": "تم نشر الخبر!", "result": rewritten})
    else:
        return jsonify({"success": False, "message": "فشل إرسال الخبر"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
