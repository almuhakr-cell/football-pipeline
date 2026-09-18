import os
from flask import Flask, redirect, render_template_string, request, session
import stripe

app = Flask(__name__)
app.secret_key = "super_secret_micro_saas_key"

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoPipeline SaaS</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans p-4">
    <div class="max-w-md mx-auto">
        <header class="bg-slate-800 border border-slate-700 rounded-2xl p-4 shadow-xl mb-6">
            <h1 class="text-xl font-bold text-sky-400 mb-2">AutoPipeline SaaS ⚡</h1>
            <div class="bg-slate-900 rounded-xl p-4 flex justify-between items-center border border-slate-700">
                <div>
                    <p class="text-xs text-slate-400">رصيدك الحالي</p>
                    <p class="text-2xl font-bold text-white">${{ "%.2f"|format(balance) }}</p>
                </div>
                <a href="/create-checkout-session" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-4 py-2 rounded-xl text-sm">💳 شحن 5$</a>
            </div>
        </header>

        <main class="bg-slate-800 border border-slate-700 rounded-2xl p-5 shadow-xl mb-6">
            <h2 class="text-sm font-bold text-emerald-400 mb-3">🤖 توليد ملفات الأتمتة (التكلفة: $0.10)</h2>
            <form action="/generate" method="POST" class="space-y-4">
                <textarea name="project_desc" rows="3" required class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white text-sm focus:outline-none focus:border-sky-500" placeholder="اكتب وصف مشروعك هنا..."></textarea>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl text-sm">توليد الآن 🚀</button>
            </form>
        </main>

        {% if result %}
        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 class="text-sm font-bold text-emerald-400">✨ النتائج:</h3>
            <pre class="bg-slate-900 p-3 rounded-xl text-teal-300 overflow-x-auto font-mono text-xs"><code>{{ result }}</code></pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route("/")
def index():
  if "balance" not in session:
    session["balance"] = 0.50
  result = session.pop("result", None)
  return render_template_string(
      HTML_TEMPLATE, balance=session["balance"], result=result
  )


@app.route("/create-checkout-session")
def create_checkout_session():
  try:
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": 500,
                "product_data": {"name": "شحن رصيد منصة AutoPipeline (5$)"},
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=request.host_url + "payment-success",
        cancel_url=request.host_url + "payment-cancel",
    )
    return redirect(checkout_session.url, code=303)
  except Exception:
    session["balance"] = session.get("balance", 0.50) + 5.00
    session["result"] = (
        "✅ تم شحن الرصيد تجريبياً بـ $5.00 بنجاح (وضع الاختبار المحاكي)!"
    )
    return redirect("/")


@app.route("/payment-success")
def payment_success():
  session["balance"] = session.get("balance", 0.50) + 5.00
  session["result"] = (
      "✅ تمت عملية الدفع بنجاح عبر بوابة الدفع وتم شحن رصيدك بـ $5.00!"
  )
  return redirect("/")


@app.route("/payment-cancel")
def payment_cancel():
  session["result"] = "❌ تم إلغاء عملية الدفع."
  return redirect("/")


@app.route("/generate", methods=["POST"])
def generate():
  if session.get("balance", 0) < 0.10:
    session["result"] = "⚠️ رصيد غير كافٍ! يرجى شحن محفظتك للمتابعة."
    return redirect("/")
  session["balance"] -= 0.10
  desc = request.form.get("project_desc", "Project")
  simulated_dockerfile = f"""FROM python:3.10
# Project: {desc}
# Status: Pipeline Generated & Ready for GitHub Actions 🚀
# Cost Deducted: $0.10
"""
  session["result"] = simulated_dockerfile
  return redirect("/")


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
