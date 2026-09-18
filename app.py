from flask import Flask, render_template_string, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "super_secret_micro_saas_key"

@app.before_request
def init_user_session():
    if 'balance' not in session:
        session['balance'] = 0.50

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة أتمتة المشاريع - Micro-SaaS</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans p-4">
    <div class="max-w-md mx-auto">
        <header class="bg-slate-800 border border-slate-700 rounded-2xl p-5 mb-6 shadow-xl">
            <h1 class="text-lg font-bold text-emerald-400 mb-2">⚡ AutoPipeline SaaS</h1>
            <div class="bg-slate-900 rounded-xl p-4 flex justify-between items-center border border-slate-700">
                <div>
                    <p class="text-xs text-slate-400">رصيدك الحالي</p>
                    <p class="text-2xl font-black text-white">${{ "%.2f"|format(balance) }}</p>
                </div>
                <form action="/topup" method="POST">
                    <button type="submit" class="bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold px-4 py-2 rounded-lg">💳 شحن 5$</button>
                </form>
            </div>
        </header>

        <main class="bg-slate-800 border border-slate-700 rounded-2xl p-5 shadow-xl mb-6">
            <h2 class="text-sm font-bold text-slate-200 mb-2">🤖 توليد ملفات الأتمتة (التكلفة: 0.10$)</h2>
            <form action="/generate" method="POST" class="space-y-4">
                <textarea name="project_desc" rows="3" required class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-white" placeholder="اكتب وصف مشروعك هنا..."></textarea>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs py-3 rounded-xl">🚀 توليد الآن</button>
            </form>
        </main>

        {% if result %}
        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 class="text-xs font-bold text-emerald-400">✨ النتائج:</h3>
            <pre class="bg-slate-900 p-3 rounded-xl text-[11px] text-teal-300 overflow-x-auto font-mono"><code>{{ result.dockerfile }}</code></pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, balance=session['balance'], result=None)

@app.route("/topup", methods=["POST"])
def topup():
    session['balance'] += 5.00
    return redirect(url_for('index'))

@app.route("/generate", methods=["POST"])
def generate():
    if session['balance'] < 0.10:
        return redirect(url_for('index'))
    session['balance'] -= 0.10
    desc = request.form.get("project_desc", "Project")
    simulated_dockerfile = f"FROM python:3.10\n# Project: {desc}"
    return render_template_string(HTML_TEMPLATE, balance=session['balance'], result={"dockerfile": simulated_dockerfile})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
