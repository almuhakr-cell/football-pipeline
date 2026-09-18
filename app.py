import os
import requests
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'super_secret_micro_saas_key'

@app.before_request
def init_user_session():
    if 'balance' not in session:
        session['balance'] = 10.0

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة توليد الأنابيب البرمجية - AutoPipeline SaaS</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans p-4">
    <div class="max-w-xl mx-auto">
        <header class="bg-slate-800 border border-slate-700 rounded-2xl p-4 shadow-xl mb-6 flex justify-between items-center">
            <div>
                <p class="text-xs text-slate-400">رصيد المحفظة الحالي</p>
                <p class="text-2xl font-bold text-emerald-400">{{ "%.2f"|format(balance) }}$</p>
            </div>
        </header>

        <main class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl mb-6">
            <h2 class="text-xl font-bold text-sky-400 mb-4">🛠️ توليد أنبوب برمجي جديد عبر GitHub</h2>
            <form id="pipeline-form" class="space-y-4">
                <div>
                    <label for="repo_desc" class="block text-sm text-slate-300 mb-1">وصف المشروع أو الأنبوب البرمجي:</label>
                    <textarea id="repo_desc" name="repo_desc" rows="3" required class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-sky-500" placeholder="مثال: football-pipeline-v1"></textarea>
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-lg transition">توليد الأنبوب الآن (-1 رصيد)</button>
            </form>
            <div id="result" class="mt-4 p-4 bg-slate-900 border border-slate-700 rounded-lg hidden break-all"></div>
        </main>
    </div>

    <script>
        document.getElementById('pipeline-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const desc = document.getElementById('repo_desc',).value;
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '<span class="text-yellow-400">⏳ جاري الاتصال بمحرك GitHub API وتوليد المستودع...</span>';
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repo_desc: desc })
                });
                const data = await response.json();
                if (response.ok) {
                    resultDiv.innerHTML = `<span class="text-emerald-400 font-bold">✅ تم التوليد بنجاح!</span><br>رابط المستودع: <a href="${data.repo_url}" target="_blank" class="text-sky-400 underline">${data.repo_url}</a>`;
                    setTimeout(() => { location.reload(); }, 3000);
                } else {
                    resultDiv.innerHTML = `<span class="text-red-400 font-bold">❌ خطأ: ${data.error}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<span class="text-red-400">❌ حدث خطأ في الاتصال بالخادم.</span>`;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, balance=session.get('balance', 10.0))

@app.route('/generate', methods=['POST'])
def generate():
    if session.get('balance', 0) < 1:
        return jsonify({'error': 'رصيد المحفظة غير كافٍ!'}), 400

    data = request.get_json() or {}
    repo_desc = data.get('repo_desc', 'football-pipeline-project')
    
    # تنظيف اسم المستودع ليكون صالحاً لـ GitHub
    repo_name = "".join(c if c.isalnum() or c in ('-', '_') else '-' for c in repo_desc.lower())[:30].strip('-')
    if not repo_name:
        repo_name = "football-pipeline-auto"

    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        return jsonify({'error': 'متغير البيئة GITHUB_TOKEN غير مُعَرّف على Render!'}), 500

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "name": repo_name,
        "description": repo_desc,
        "private": False,
        "auto_init": True
    }

    response = requests.post("https://api.github.com/user/repos", json=payload, headers=headers)
    
    if response.status_code == 201:
        repo_data = response.json()
        session['balance'] = session.get('balance', 10.0) - 1.0
        return jsonify({
            'success': True,
            'repo_url': repo_data.get('html_url')
        })
    else:
        try:
            err_json = response.json()
            err_msg = err_json.get('message', 'Unknown error')
        except:
            err_msg = response.text
        return jsonify({'error': f'فشل إنشاء المستودع في GitHub: {err_msg}'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
