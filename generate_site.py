import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from html import escape
import re

API_BASE = "https://www.thesportsdb.com/api/v1/json/3"
OUT = Path("docs")
MATCHES_DIR = OUT / "matches"
MAX_MATCHES = 20


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "football-match-hub/3.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_germany_team():
    url = (
        f"{API_BASE}/searchteams.php?"
        f"{urllib.parse.urlencode({'t': 'Germany'})}"
    )

    data = get_json(url)

    teams = data.get("teams") or []

    for team in teams:
        if (
            (team.get("strTeam") or "").lower() == "germany"
            and (team.get("strSport") or "").lower() == "soccer"
        ):
            return team

    if teams:
        return teams[0]

    raise RuntimeError("Germany national team not found")


def fetch_matches():
    team = get_germany_team()

    team_id = team.get("idTeam")

    if not team_id:
        raise RuntimeError("Germany team ID missing")

    data = get_json(
        f"{API_BASE}/eventsnext.php?id={team_id}"
    )

    return data.get("events") or []


def parse_datetime(event):
    date_value = event.get("dateEvent")
    time_value = event.get("strTime") or "00:00:00"

    if not date_value:
        return None

    try:
        return datetime.fromisoformat(
            f"{date_value}T{time_value}"
        ).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def format_date(dt):
    if not dt:
        return "Termin folgt"

    return dt.astimezone().strftime(
        "%d.%m.%Y · %H:%M"
    )


def slugify(text, event_id):
    value = text.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value
    ).strip("-")

    return f"{value}-{event_id}"


def create_match_page(event):

    home = event.get("strHomeTeam") or "Deutschland"
    away = event.get("strAwayTeam") or "Gegner"

    title = f"{home} – {away}"

    event_id = event.get("idEvent") or "unknown"

    slug = slugify(
        title,
        event_id
    )

    dt = parse_datetime(event)

    league = escape(
        event.get("strLeague")
        or "Nationalmannschaft"
    )

    venue = escape(
        event.get("strVenue")
        or "Spielort folgt"
    )

    home_safe = escape(home)
    away_safe = escape(away)

    date_text = format_date(dt)

    timestamp = int(
        dt.timestamp()
    ) * 1000 if dt else 0

    html = f"""
<!doctype html>

<html lang="de">

<head>

<meta charset="utf-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>
{escape(title)} | Match-Hub
</title>

<meta name="description"
content="{escape(title)} – Match-Hub mit Countdown und Fan-Challenge.">

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f3f4f6;
    color: #111827;
}}

header {{
    background: #111827;
    color: white;
    padding: 18px;
}}

header a {{
    color: white;
    text-decoration: none;
}}

main {{
    max-width: 900px;
    margin: auto;
    padding: 16px;
}}

.card {{
    background: white;
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 4px 18px rgba(0,0,0,.06);
}}

.teams {{
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    text-align: center;
    gap: 15px;
}}

.team {{
    font-size: 25px;
    font-weight: 800;
}}

.vs {{
    color: #6b7280;
    font-weight: 800;
}}

.countdown {{
    text-align: center;
    font-size: 30px;
    font-weight: 800;
    margin: 22px 0;
}}

.meta {{
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 10px;
}}

.meta div {{
    background: #f8fafc;
    padding: 14px;
    border-radius: 14px;
}}

.label {{
    color: #6b7280;
    font-size: 13px;
}}

.value {{
    font-weight: 700;
    margin-top: 5px;
}}

.predictions {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}}

.prediction {{
    padding: 16px;
    border: 2px solid #e5e7eb;
    border-radius: 16px;
    background: white;
    font-size: 18px;
    font-weight: 700;
    cursor: pointer;
}}

.prediction.selected {{
    border-color: #111827;
    background: #f3f4f6;
}}

.result {{
    text-align: center;
    margin-top: 14px;
    font-weight: 700;
}}

.share {{
    width: 100%;
    padding: 14px;
    border: 0;
    border-radius: 14px;
    background: #111827;
    color: white;
    font-weight: 700;
    font-size: 16px;
    cursor: pointer;
}}

.muted {{
    color: #6b7280;
}}

@media(max-width:650px) {{

    .teams {{
        grid-template-columns: 1fr;
    }}

    .vs {{
        display: none;
    }}

    .meta {{
        grid-template-columns: 1fr;
    }}

}}

</style>

</head>

<body>

<header>

<a href="../">
← مركز مباريات ألمانيا
</a>

</header>

<main>

<section class="card">

<div class="teams">

<div class="team">
{home_safe}
</div>

<div class="vs">
VS
</div>

<div class="team">
{away_safe}
</div>

</div>

<div
id="countdown"
class="countdown"
data-time="{timestamp}">
جاري حساب الوقت...
</div>

<div class="meta">

<div>

<div class="label">
التاريخ والوقت
</div>

<div class="value">
{date_text}
</div>

</div>

<div>

<div class="label">
المسابقة
</div>

<div class="value">
{league}
</div>

</div>

<div>

<div class="label">
المكان
</div>

<div class="value">
{venue}
</div>

</div>

</div>

</section>


<section class="card">

<h2>
🔥 تحدي المباراة
</h2>

<p class="muted">
اختر توقعك. سيتم حفظ اختيارك على جهازك.
</p>

<div class="predictions">

<button
class="prediction"
data-choice="home">
{home_safe}
</button>

<button
class="prediction"
data-choice="away">
{away_safe}
</button>

</div>

<div
id="prediction-result"
class="result">
</div>

</section>


<section class="card">

<h2>
📊 مركز المباراة
</h2>

<p class="muted">
الإحصائيات والأخبار ستظهر هنا عندما تتوفر
من مصادر بيانات موثوقة.
</p>

</section>


<section class="card">

<button
class="share"
onclick="shareMatch()">
📤 مشاركة المباراة
</button>

</section>

</main>


<script>

const countdown =
document.getElementById("countdown");

const target =
Number(countdown.dataset.time);

function updateCountdown() {{

    if (!target) {{
        countdown.textContent =
            "موعد المباراة غير متوفر";
        return;
    }}

    const now =
        Date.now();

    let diff =
        target - now;

    if (diff <= 0) {{
        countdown.textContent =
            "🔥 المباراة بدأت";
        return;
    }}

    const days =
        Math.floor(
            diff / 86400000
        );

    diff %= 86400000;

    const hours =
        Math.floor(
            diff / 3600000
        );

    diff %= 3600000;

    const minutes =
        Math.floor(
            diff / 60000
        );

    const seconds =
        Math.floor(
            (diff % 60000) / 1000
        );

    countdown.textContent =
        days + " يوم · " +
        hours + " ساعة · " +
        minutes + " دقيقة · " +
        seconds + " ثانية";
}}

updateCountdown();

setInterval(
    updateCountdown,
    1000
);


const buttons =
    document.querySelectorAll(
        ".prediction"
    );

const result =
    document.getElementById(
        "prediction-result"
    );

const storageKey =
    "prediction-{event_id}";

const saved =
    localStorage.getItem(
        storageKey
    );

if (saved) {{
    selectPrediction(saved);
}}

buttons.forEach(button => {{

    button.addEventListener(
        "click",
        () => {{

            const choice =
                button.dataset.choice;

            localStorage.setItem(
                storageKey,
                choice
            );

            selectPrediction(
                choice
            );
        }}
    );

}});


function selectPrediction(choice) {{

    buttons.forEach(button => {{

        button.classList.toggle(
            "selected",
            button.dataset.choice === choice
        );

    }});

    if (choice === "home") {{
        result.textContent =
            "تم حفظ توقعك: " +
            "{home_safe}";
    }} else {{
        result.textContent =
            "تم حفظ توقعك: " +
            "{away_safe}";
    }}
}}


async function shareMatch() {{

    const shareData = {{
        title:
            "{escape(title)}",
        text:
            "🔥 تحدي مباراة {escape(title)}",
        url:
            window.location.href
    }};

    try {{

        if (
            navigator.share
        ) {{

            await navigator.share(
                shareData
            );

        }} else {{

            await navigator.clipboard.writeText(
                window.location.href
            );

            alert(
                "تم نسخ رابط المباراة"
            );
        }}

    }} catch (error) {{}}
}}

</script>

</body>

</html>
"""

    MATCHES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        MATCHES_DIR /
        f"{slug}.html"
    )

    path.write_text(
        html,
        encoding="utf-8"
    )

    return slug, title, dt


def main():

    print(
        "Starting Match-Hub engine..."
    )

    OUT.mkdir(
        parents=True,
        exist_ok=True
    )

    MATCHES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    events = fetch_matches()

    now = datetime.now(
        timezone.utc
    )

    matches = []

    for event in events:

        dt = parse_datetime(event)

        if not dt:
            continue

        if dt < now:
            continue

        matches.append(event)

    matches.sort(
        key=parse_datetime
    )

    matches = matches[:MAX_MATCHES]

    cards = []

    for event in matches:

        slug, title, dt = \
            create_match_page(event)

        venue = escape(
            event.get("strVenue")
            or "سيتم الإعلان لاحقًا"
        )

        league = escape(
            event.get("strLeague")
            or "Nationalmannschaft"
        )

        cards.append(
            f"""
<div class="card">

<h2>
{escape(title)}
</h2>

<p>
<b>{format_date(dt)}</b>
</p>

<p>
🏆 {league}
</p>

<p>
📍 {venue}
</p>

<a href="matches/{slug}.html">
🔥 افتح تحدي المباراة →
</a>

</div>
"""
        )

    if not cards:

        cards.append(
            """
<div class="card">
لا توجد مباريات قادمة حاليًا.
</div>
"""
        )

    updated = datetime.now().astimezone()

    index_html = f"""
<!doctype html>

<html lang="de">

<head>

<meta charset="utf-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>
🇩🇪 Deutschland Match-Hub
</title>

<style>

body {{
    margin: 0;
    font-family: Arial,sans-serif;
    background: #f3f4f6;
    color: #111827;
}}

header {{
    background: #111827;
    color: white;
    padding: 28px 18px;
}}

main {{
    max-width: 900px;
    margin: auto;
    padding: 16px;
}}

.card {{
    background: white;
    padding: 20px;
    margin: 16px 0;
    border-radius: 18px;
}}

a {{
    color: #111827;
    font-weight: 800;
}}

.muted {{
    color: #6b7280;
}}

</style>

</head>

<body>

<header>

<h1>
🇩🇪 Deutschland Match-Hub
</h1>

<p>
المباريات + التحديات
</p>

</header>

<main>

<div class="card">

<h2>
🔥 المباريات القادمة
</h2>

<p class="muted">

آخر تحديث:
{updated.strftime("%d.%m.%Y %H:%M")}

</p>

</div>

{''.join(cards)}

</main>

</body>

</html>
"""

    (
        OUT / "index.html"
    ).write_text(
        index_html,
        encoding="utf-8"
    )

    print(
        f"Generated {len(matches)} matches."
    )

    print(
        "Match-Hub engine completed."
    )


if __name__ == "__main__":
    main()
