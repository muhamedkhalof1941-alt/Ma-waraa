from flask import Flask, render_template_string, request, jsonify
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)

# ============ الإعدادات ============
TELEGRAM_BOT_TOKEN = "8240379609:AAFKeQ8hLv605TSD7AdG29vGTpZ4fPex62E"
CHANNEL_ID = "-1002560480003"
ADMIN_ID = "5365833232"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

# ============ البيانات ============
import re

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

def fetch_channel_messages(username):
    try:
        url = f"https://t.me/s/{username}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            messages = []
            pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
            matches = re.findall(pattern, response.text, re.DOTALL)
            for match in matches[:5]:
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                if clean_text and len(clean_text) > 20:
                    messages.append({'text': clean_text, 'source': username})
            return messages
    except:
        pass
    return []

SOURCES = load_data().get('sources', [])
NEWS = load_data().get('news', [])

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
    if not OPENAI_API_KEY:
        flags = get_flags(original_text)
        return f"عاجل\n\n{original_text}\n\n{flags}\n\nⓘ متابعة التطورات | ما وراء"
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""أنت محرر أخبار محترف ومحايد تماماً. أعد صياغة الخبر التالي بشكل:
1. محايد تماماً - بدون أي انحياز سياسي أو فكري
2. مهني وموضوعي - فقط الحقائق
3. بدون لغة عاطفية أو تحريضية
4. اجعل العنوان يبدأ بـ "عاجل" إذا كان خبراً عاجلاً
5. أضف أعلام الدول المتعلقة بالخبر

الخبر الأصلي:
{original_text}

أعد صياغته بالتنسيق التالي:
عاجل

[العنوان المعاد صياغته] [الأعلام]

[تفاصيل الخبر بشكل محايد]

ⓘ متابعة التطورات | ما وراء"""

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "أنت محرر أخبار محترف ومحايد. تعيد صياغة الأخبار بشكل موضوعي ومهني."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            flags = get_flags(original_text)
            return f"عاجل\n\n{original_text}\n\n{flags}\n\nⓘ متابعة التطورات | ما وراء"
            
    except Exception as e:
        flags = get_flags(original_text)
        return f"عاجل\n\n{original_text}\n\n{flags}\n\nⓘ متابعة التطورات | ما وراء"

def send_to_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False

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
            <div style="text-align: center; padding: 20px; background: #0f1419; border-radius: 10px; border: 1px solid #27ae60;">
                <h3 style="color: #27ae60; margin-bottom: 10px;">✅ نظام ما وراء يعمل بنجاح!</h3>
                <p style="color: #8899a6;">لوحة التحكم جاهزة للاستخدام.</p>
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
            <div style="margin-top: 20px;">
                <button class="btn" onclick="fetchNews()">🔄 جلب الأخبار من المصادر</button>
            </div>
            <div id="fetch-status" style="margin-top: 15px;"></div>
            <div id="fetched-news" style="margin-top: 20px;"></div>
        </div>
        
        <div id="news" class="section">
            <h2>📰 إضافة خبر جديد</h2>
            <textarea id="news-text" rows="5" placeholder="أدخل الخبر هنا..."></textarea>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn" onclick="addNews()">📤 إضافة الخبر</button>
                <button class="btn btn-success" onclick="addAndSend()">🚀 إضافة وإرسال للقناة</button>
            </div>
            <div class="loading" id="news-loading"><div class="spinner"></div><p>جاري المعالجة...</p></div>
            <div id="news-result" style="margin-top: 20px;"></div>
            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #e74c3c;">📋 الأخبار المضافة</h3>
            <div id="news-list"></div>
        </div>
        
        <div id="rewrite" class="section">
            <h2>✏️ إعادة صياغة الخبر</h2>
            <p style="color: #8899a6; margin-bottom: 20px;">أدخل الخبر وسيتم إعادة صياغته بشكل محايد وتام باستخدام الذكاء الاصطناعي:</p>
            <textarea id="rewrite-text" rows="6" placeholder="أدخل الخبر الأصلي هنا..."></textarea>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn" onclick="rewriteNews()">✨ إعادة الصياغة</button>
                <button class="btn btn-success" onclick="rewriteAndSend()">🚀 إعادة الصياغة وإرسال للقناة</button>
            </div>
            <div class="loading" id="rewrite-loading"><div class="spinner"></div><p>جاري إعادة الصياغة بالذكاء الاصطناعي...</p></div>
            <div id="rewrite-result"></div>
        </div>
        
        <div id="settings" class="section">
            <h2>⚙️ الإعدادات</h2>
            <div class="source-item"><div class="source-info"><h4>معرف القناة</h4><span>-1002560480003</span></div></div>
            <div class="source-item"><div class="source-info"><h4>معرف المسؤول</h4><span>5365833232</span></div></div>
            <div class="source-item"><div class="source-info"><h4>حالة OpenAI</h4><span id="openai-status">جاري التحقق...</span></div></div>
            <div class="source-item"><div class="source-info"><h4>عدد المصادر</h4><span>4 مصادر</span></div></div>
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
        
        function addNews() {
            const text = document.getElementById('news-text').value;
            if (!text) { alert('أدخل الخبر أولاً'); return; }
            document.getElementById('news-loading').classList.add('show');
            fetch('/api/news', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: text}) })
            .then(r => r.json())
            .then(data => {
                document.getElementById('news-loading').classList.remove('show');
                document.getElementById('news-result').innerHTML = '<div class="result-box" style="border-color: #27ae60;">✅ ' + data.message + '</div>';
                document.getElementById('news-text').value = '';
                loadNews();
            });
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
                    document.getElementById('news-result').innerHTML = '<div class="result-box" style="border-color: #27ae60;">✅ ' + data.message + '<br><br>' + data.result + '</div>';
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
                document.getElementById('rewrite-result').innerHTML = '<h3 style="margin: 20px 0 10px; color: #27ae60;">النتيجة:</h3><div class="result-box">' + data.result + '</div><button class="btn btn-success" style="margin-top: 15px;" onclick="sendRewritten()">🚀 إرسال للقناة</button>';
                window.lastRewritten = data.result;
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
                    document.getElementById('rewrite-result').innerHTML = '<h3 style="margin: 20px 0 10px; color: #27ae60;">✅ تم الإرسال بنجاح!</h3><div class="result-box">' + data.result + '</div>';
                    document.getElementById('rewrite-text').value = '';
                } else {
                    document.getElementById('rewrite-result').innerHTML = '<div class="result-box error">❌ ' + data.message + '</div>';
                }
            });
        }
        
        function sendRewritten() {
            if (!window.lastRewritten) { alert('لا يوجد خبر للإرسال'); return; }
            fetch('/api/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: window.lastRewritten}) })
            .then(r => r.json())
            .then(data => { alert(data.success ? '✅ تم الإرسال بنجاح!' : '❌ فشل الإرسال: ' + data.message); });
        }
        
        function loadNews() {
            fetch('/api/news').then(r => r.json()).then(data => {
                const html = data.map(n => '<div class="news-item"><div class="content">' + n + '</div></div>').join('');
                document.getElementById('news-list').innerHTML = html || '<p style="color: #8899a6;">لا توجد أخبار بعد</p>';
                document.getElementById('news-count').textContent = data.length;
            });
        }
        
        fetch('/api/status').then(r => r.json()).then(data => {
            document.getElementById('openai-status').textContent = data.openai ? '✅ متصل' : '⚠️ غير متصل';
        });
        
        loadNews();
        loadSources();
        
        function loadSources() {
            fetch('/api/sources').then(r => r.json()).then(sources => {
                const html = sources.map(s => `
                    <div class="source-item">
                        <div class="source-info"><h4>${s.name}</h4><span>@${s.username}</span></div>
                        <div>
                            <span class="status-badge ${s.active ? 'status-active' : ''}" style="${!s.active ? 'background:#e74c3c;' : ''}">${s.active ? '✓ نشط' : '✗ معطل'}</span>
                            <button class="btn" style="padding: 5px 10px; margin-right: 5px;" onclick="toggleSource(${s.id})">${s.active ? 'تعطيل' : 'تفعيل'}</button>
                            <button class="btn" style="padding: 5px 10px; background: #e74c3c;" onclick="deleteSource(${s.id})">حذف</button>
                        </div>
                    </div>
                `).join('');
                document.getElementById('sources-list').innerHTML = html || '<p style="color: #8899a6;">لا توجد مصادر</p>';
            });
        }
        
        function addSource() {
            const name = document.getElementById('new-source-name').value;
            const username = document.getElementById('new-source-username').value.replace('@', '');
            if (!name || !username) { alert('الرجاء إدخال اسم المصدر واليوزرنيم'); return; }
            fetch('/api/sources', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, username}) })
            .then(r => r.json()).then(() => {
                document.getElementById('new-source-name').value = '';
                document.getElementById('new-source-username').value = '';
                loadSources();
                alert('تم إضافة المصدر بنجاح!');
            });
        }
        
        function toggleSource(id) {
            fetch(`/api/sources/${id}/toggle`, { method: 'POST' }).then(() => loadSources());
        }
        
        function deleteSource(id) {
            if (confirm('هل أنت متأكد من حذف هذا المصدر؟')) {
                fetch(`/api/sources/${id}`, { method: 'DELETE' }).then(() => loadSources());
            }
        }
        
        function fetchNews() {
            document.getElementById('fetch-status').innerHTML = '<div class="loading show"><div class="spinner"></div><p>جاري جلب الأخبار...</p></div>';
            fetch('/api/fetch', { method: 'POST' }).then(r => r.json()).then(data => {
                document.getElementById('fetch-status').innerHTML = `<div style="background: #0f1419; padding: 15px; border-radius: 10px; border: 1px solid #27ae60;"><p style="color: #27ae60;">✅ تم جلب ${data.count} خبر</p></div>`;
                const html = data.news.map(n => `
                    <div class="news-item">
                        <p style="color: #e74c3c; font-size: 0.9em; margin-bottom: 5px;">📡 ${n.source_name || n.source}</p>
                        <p>${n.text}</p>
                        <div style="margin-top: 10px;">
                            <button class="btn" style="padding: 5px 15px;" onclick="useNews('${encodeURIComponent(n.text)}')">استخدام</button>
                            <button class="btn btn-success" style="padding: 5px 15px;" onclick="rewriteAndSendDirect('${encodeURIComponent(n.text)}')">صياغة ونشر</button>
                        </div>
                    </div>
                `).join('');
                document.getElementById('fetched-news').innerHTML = html;
            });
        }
        
        function useNews(text) {
            document.getElementById('rewrite-text').value = decodeURIComponent(text);
            showSection('rewrite');
            document.querySelectorAll('.nav-btn')[3].classList.add('active');
        }
        
        function rewriteAndSendDirect(encodedText) {
            const text = decodeURIComponent(encodedText);
            fetch('/api/rewrite/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text}) })
            .then(r => r.json()).then(data => { alert(data.success ? '✅ تم الصياغة والنشر بنجاح!' : '❌ فشل: ' + data.message); });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/news', methods=['GET', 'POST'])
def api_news():
    if request.method == 'POST':
        data = request.json
        text = data.get('text', '')
        NEWS.append(text)
        return jsonify({"success": True, "message": "تم إضافة الخبر بنجاح"})
    return jsonify(NEWS)

@app.route('/api/news/send', methods=['POST'])
def api_news_send():
    data = request.json
    text = data.get('text', '')
    rewritten = rewrite_with_ai(text)
    success = send_to_telegram(rewritten)
    if success:
        NEWS.append(rewritten)
        return jsonify({"success": True, "message": "تم إعادة الصياغة والإرسال للقناة بنجاح!", "result": rewritten})
    else:
        return jsonify({"success": False, "message": "فشل الإرسال للقناة"})

@app.route('/api/rewrite', methods=['POST'])
def api_rewrite():
    data = request.json
    text = data.get('text', '')
    rewritten = rewrite_with_ai(text)
    return jsonify({"success": True, "result": rewritten})

@app.route('/api/rewrite/send', methods=['POST'])
def api_rewrite_send():
    data = request.json
    text = data.get('text', '')
    rewritten = rewrite_with_ai(text)
    success = send_to_telegram(rewritten)
    if success:
        NEWS.append(rewritten)
        return jsonify({"success": True, "message": "تم الإرسال بنجاح!", "result": rewritten})
    else:
        return jsonify({"success": False, "message": "فشل الإرسال للقناة", "result": rewritten})

@app.route('/api/send', methods=['POST'])
def api_send():
    data = request.json
    text = data.get('text', '')
    success = send_to_telegram(text)
    return jsonify({"success": success, "message": "تم الإرسال بنجاح!" if success else "فشل الإرسال"})

@app.route('/api/status')
def api_status():
    return jsonify({"openai": bool(OPENAI_API_KEY)})

@app.route('/api/sources', methods=['GET', 'POST'])
def api_sources():
    data = load_data()
    if request.method == 'POST':
        req = request.json
        new_source = {
            'id': max([s['id'] for s in data['sources']] + [0]) + 1,
            'name': req['name'],
            'username': req['username'].replace('@', ''),
            'active': True
        }
        data['sources'].append(new_source)
        save_data(data)
        return jsonify({'success': True})
    return jsonify(data['sources'])

@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
def delete_source(source_id):
    data = load_data()
    data['sources'] = [s for s in data['sources'] if s['id'] != source_id]
    save_data(data)
    return jsonify({'success': True})

@app.route('/api/sources/<int:source_id>/toggle', methods=['POST'])
def toggle_source(source_id):
    data = load_data()
    for source in data['sources']:
        if source['id'] == source_id:
            source['active'] = not source.get('active', True)
            break
    save_data(data)
    return jsonify({'success': True})

@app.route('/api/fetch', methods=['POST'])
def api_fetch():
    data = load_data()
    all_news = []
    for source in data['sources']:
        if source.get('active', True):
            messages = fetch_channel_messages(source['username'])
            for msg in messages:
                msg['source_name'] = source['name']
                all_news.append(msg)
    data['fetched_news'] = all_news[:20]
    save_data(data)
    return jsonify({'success': True, 'count': len(all_news), 'news': all_news})

@app.route('/api/fetched')
def api_fetched():
    data = load_data()
    return jsonify(data.get('fetched_news', []))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
