#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ما وراء - نظام إدارة الأخبار والتحديثات
Ma Waraa - News Management System
"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# البيانات
CHANNEL_ID = 2560480003
BOT_TOKEN = "8240379609:AAFKeQ8hLv605TSD7AdG29vGTpZ4fPex62E"
ADMIN_ID = 5365833232

SOURCES = [
    {"id": 1, "name": "Almustashaar", "url": "https://t.me/Almustashaar", "active": True},
    {"id": 2, "name": "sawtl7arb", "url": "https://t.me/sawtl7arb", "active": True},
    {"id": 3, "name": "WarsLeaks", "url": "https://t.me/WarsLeaks", "active": True},
    {"id": 4, "name": "nayaforiraq", "url": "https://t.me/nayaforiraq", "active": True}
]

NEWS = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ما وراء - لوحة التحكم</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin: 40px 0;
            border-bottom: 3px solid #ff4444;
            padding-bottom: 30px;
        }
        
        .header h1 {
            font-size: 3em;
            color: #ff4444;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .header p {
            font-size: 1.2em;
            color: #aaa;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .tab-btn {
            background: #333;
            color: #fff;
            border: 2px solid #ff4444;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        .tab-btn:hover {
            background: #ff4444;
            transform: translateY(-2px);
        }
        
        .tab-btn.active {
            background: #ff4444;
            color: #fff;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .box {
            background: rgba(42, 42, 42, 0.8);
            padding: 30px;
            margin: 20px 0;
            border-radius: 10px;
            border-right: 4px solid #ff4444;
            backdrop-filter: blur(10px);
        }
        
        .box h2 {
            color: #ff4444;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .box h3 {
            color: #ff4444;
            margin: 20px 0 10px 0;
        }
        
        input, textarea {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: #333;
            color: #fff;
            border: 1px solid #ff4444;
            border-radius: 5px;
            font-family: Arial;
            font-size: 1em;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: #ff7777;
            box-shadow: 0 0 10px rgba(255, 68, 68, 0.3);
        }
        
        button {
            background: #ff4444;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px 5px 10px 0;
            transition: all 0.3s;
        }
        
        button:hover {
            background: #cc0000;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 68, 68, 0.3);
        }
        
        .source-item, .news-item {
            background: #333;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-right: 3px solid #ff4444;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .source-item strong, .news-item strong {
            color: #ff4444;
        }
        
        .status {
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        
        .status.active {
            background: #44ff44;
            color: #000;
        }
        
        .status.inactive {
            background: #ff4444;
            color: #fff;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-box {
            background: #333;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            border-top: 3px solid #ff4444;
        }
        
        .stat-box h4 {
            color: #aaa;
            margin-bottom: 10px;
        }
        
        .stat-box .number {
            font-size: 2.5em;
            color: #ff4444;
            font-weight: bold;
        }
        
        .alert {
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        
        .alert.success {
            background: rgba(68, 255, 68, 0.1);
            border-left-color: #44ff44;
            color: #44ff44;
        }
        
        .alert.error {
            background: rgba(255, 68, 68, 0.1);
            border-left-color: #ff4444;
            color: #ff4444;
        }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #444;
            color: #aaa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔴 ما وراء</h1>
            <p>نظام إدارة الأخبار والتحديثات المحايد</p>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('dashboard')">📊 لوحة المعلومات</button>
            <button class="tab-btn" onclick="switchTab('sources')">📡 المصادر</button>
            <button class="tab-btn" onclick="switchTab('news')">📰 الأخبار</button>
            <button class="tab-btn" onclick="switchTab('rewrite')">✏️ إعادة الصياغة</button>
            <button class="tab-btn" onclick="switchTab('settings')">⚙️ الإعدادات</button>
        </div>
        
        <!-- لوحة المعلومات -->
        <div id="dashboard" class="tab-content active">
            <div class="box">
                <h2>✅ نظام ما وراء يعمل بنجاح!</h2>
                <p>لوحة التحكم جاهزة للاستخدام. يمكنك إدارة المصادر والأخبار وإعادة الصياغة من هنا.</p>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <h4>الأخبار المضافة</h4>
                    <div class="number" id="news-count">0</div>
                </div>
                <div class="stat-box">
                    <h4>المصادر النشطة</h4>
                    <div class="number" id="sources-count">4</div>
                </div>
                <div class="stat-box">
                    <h4>حالة النظام</h4>
                    <div class="number" style="color: #44ff44;">✓</div>
                </div>
            </div>
        </div>
        
        <!-- المصادر -->
        <div id="sources" class="tab-content">
            <div class="box">
                <h2>📡 إدارة المصادر</h2>
                <p>المصادر التي يجلب منها النظام الأخبار:</p>
                <div id="sources-list"></div>
            </div>
        </div>
        
        <!-- الأخبار -->
        <div id="news" class="tab-content">
            <div class="box">
                <h2>📰 إضافة خبر جديد</h2>
                <textarea id="news-input" placeholder="أدخل الخبر هنا..." rows="5"></textarea>
                <button onclick="addNews()">إضافة الخبر</button>
                <div id="alert"></div>
            </div>
            
            <div class="box">
                <h2>📋 الأخبار المضافة</h2>
                <div id="news-list"></div>
            </div>
        </div>
        
        <!-- إعادة الصياغة -->
        <div id="rewrite" class="tab-content">
            <div class="box">
                <h2>✏️ إعادة صياغة الخبر</h2>
                <p>أدخل الخبر وسيتم إعادة صياغته بشكل محايد وتام:</p>
                <textarea id="rewrite-input" placeholder="أدخل الخبر المراد إعادة صياغته..." rows="5"></textarea>
                <button onclick="rewriteNews()">إعادة الصياغة</button>
            </div>
            
            <div id="rewrite-result"></div>
        </div>
        
        <!-- الإعدادات -->
        <div id="settings" class="tab-content">
            <div class="box">
                <h2>⚙️ الإعدادات</h2>
                
                <h3>معلومات القناة</h3>
                <label>معرف القناة:</label>
                <input type="text" value="2560480003" readonly>
                
                <label>معرف المسؤول:</label>
                <input type="text" value="5365833232" readonly>
                
                <h3>المصادر</h3>
                <p>عدد المصادر المتابعة: 4</p>
                <button onclick="alert('سيتم تحديث المصادر قريباً')">تحديث المصادر</button>
                
                <h3>حول النظام</h3>
                <p>نظام ما وراء - نظام إدارة الأخبار والتحديثات</p>
                <p>الإصدار: 1.0</p>
                <p>آخر تحديث: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2026 نظام ما وراء | جميع الحقوق محفوظة</p>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            // إخفاء جميع التابات
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // إزالة الـ active من جميع الأزرار
            const buttons = document.querySelectorAll('.tab-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            
            // إظهار التاب المختار
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // تحديث البيانات
            if (tabName === 'sources') loadSources();
            if (tabName === 'news') loadNews();
            if (tabName === 'dashboard') loadStats();
        }
        
        function addNews() {
            const text = document.getElementById('news-input').value;
            if (!text.trim()) {
                showAlert('يرجى إدخال خبر!', 'error');
                return;
            }
            
            fetch('/api/news', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            })
            .then(r => r.json())
            .then(data => {
                showAlert('✓ تم إضافة الخبر بنجاح!', 'success');
                document.getElementById('news-input').value = '';
                loadNews();
                loadStats();
            })
            .catch(e => showAlert('خطأ: ' + e, 'error'));
        }
        
        function rewriteNews() {
            const text = document.getElementById('rewrite-input').value;
            if (!text.trim()) {
                alert('يرجى إدخال خبر!');
                return;
            }
            
            fetch('/api/rewrite', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            })
            .then(r => r.json())
            .then(data => {
                const html = `
                    <div class="box">
                        <h3>النتيجة:</h3>
                        <div class="news-item">
                            <div>${data.rewritten}</div>
                        </div>
                    </div>
                `;
                document.getElementById('rewrite-result').innerHTML = html;
            })
            .catch(e => alert('خطأ: ' + e));
        }
        
        function loadSources() {
            fetch('/api/sources')
            .then(r => r.json())
            .then(data => {
                const html = data.map(s => `
                    <div class="source-item">
                        <strong>${s.name}</strong>
                        <span class="status ${s.active ? 'active' : 'inactive'}">
                            ${s.active ? '✓ نشط' : '✗ معطل'}
                        </span>
                    </div>
                `).join('');
                document.getElementById('sources-list').innerHTML = html;
            });
        }
        
        function loadNews() {
            fetch('/api/news')
            .then(r => r.json())
            .then(data => {
                const html = data.map((n, i) => `
                    <div class="news-item">
                        <div>${n}</div>
                    </div>
                `).join('');
                document.getElementById('news-list').innerHTML = html || '<p>لا توجد أخبار حتى الآن</p>';
            });
        }
        
        function loadStats() {
            fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('news-count').textContent = data.news_count;
                document.getElementById('sources-count').textContent = data.sources_count;
            });
        }
        
        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.innerHTML = `<div class="alert ${type}">${message}</div>`;
            setTimeout(() => alert.innerHTML = '', 3000);
        }
        
        // تحميل البيانات عند فتح الصفحة
        loadStats();
        loadSources();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/news', methods=['GET', 'POST'])
def api_news():
    if request.method == 'POST':
        data = request.json
        text = data.get('text', '')
        if text:
            NEWS.append({
                'text': text,
                'timestamp': datetime.now().isoformat(),
                'rewritten': f"عاجل\n\n{text}\n\n🇮🇶"
            })
        return jsonify({'status': 'ok'})
    return jsonify([n['text'] for n in NEWS])

@app.route('/api/rewrite', methods=['POST'])
def api_rewrite():
    data = request.json
    text = data.get('text', '')
    
    # إعادة صياغة بسيطة (بدون OpenAI للآن)
    rewritten = f"عاجل\n\n{text}\n\n🇮🇶 (محايد)"
    
    return jsonify({'rewritten': rewritten})

@app.route('/api/sources')
def api_sources():
    return jsonify(SOURCES)

@app.route('/api/stats')
def api_stats():
    return jsonify({
        'news_count': len(NEWS),
        'sources_count': len([s for s in SOURCES if s['active']])
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
