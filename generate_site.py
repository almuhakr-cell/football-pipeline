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
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "football-match-hub/2.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
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

    url = f"{API_BASE}/eventsnext.php?id={team_id}"

    data = get_json(url)

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
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text
    ).strip("-")

    return f"{text}-{event_id}"


def clean_text(value, fallback):
    value = value or ""

    value = str(value).strip()

    return escape(value if value else fallback)


def match_title(event):
    home = event.get("strHomeTeam") or "Deutschland"
    away = event.get("strAwayTeam") or "Gegner"

    return f"{home} – {away}"


def create_match_page(event):
    title = match_title(event)

    event_id = event.get("idEvent") or "unknown"

    slug = slugify(
        title,
        event_id
    )

    dt = parse_datetime(event)

    league = clean_text(
        event.get("strLeague"),
        "Nationalmannschaft"
    )

    venue = clean_text(
        event.get("strVenue"),
        "Spielort folgt"
    )

    country = clean_text(
        event.get("strCountry"),
        "Deutschland"
    )

    home = clean_text(
        event.get("strHomeTeam"),
        "Deutschland"
    )

    away = clean_text(
        event.get("strAwayTeam"),
        "Gegner"
    )

    date_display = format_date(dt)

    html = f"""<!doctype html>

<html lang="de">

<head>

<meta charset="utf-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>
{escape(title)} | Deutschland Match-Hub
</title>

<meta name="description"
content="{escape(title)} – Spielzeit, Wettbewerb, Spielort und Match-Hub.">

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family:
        Arial,
        Helvetica,
        sans-serif;
    background: #f2f4f7;
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
    width: min(900px, 100%);
    margin: auto;
    padding: 16px;
}}

.hero {{
    background: white;
    border-radius: 20px;
    padding: 24px;
    margin-top: 15px;
    box-shadow:
        0 4px 20px
        rgba(0,0,0,.06);
}}

.teams {{
    display: grid;
    grid-template-columns:
        1fr auto 1fr;
    gap: 15px;
    align-items: center;
    text-align: center;
}}

.team {{
    font-size: 24px;
    font-weight: 700;
}}

.vs {{
    font-weight: 700;
    color: #6b7280;
}}

.meta {{
    display: grid;
    grid-template-columns:
        repeat(3, 1fr);
    gap: 12px;
    margin-top: 22px;
}}

.meta div {{
    background: #f8fafc;
    border-radius: 14px;
    padding: 15px;
}}

.label {{
    color: #6b7280;
    font-size: 13px;
}}

.value {{
    font-weight: 700;
    margin-top: 5px;
}}

.card {{
    background: white;
    border-radius: 18px;
    padding: 20px;
    margin-top: 16px;
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
← Deutschland Match-Hub
</a>

</header>

<main>

<section class="hero">

<div class="teams">

<div class="team">
{home}
</div>

<div class="vs">
VS
</div>

<div class="team">
{away}
</div>

</div>

<div class="meta">

<div>

<div class="label">
Datum & Uhrzeit
</div>

<div class="value">
{date_display}
</div>

</div>

<div>

<div class="label">
Wettbewerb
</div>

<div class="value">
{league}
</div>

</div>

<div>

<div class="label">
Spielort
</div>

<div class="value">
{venue}
</div>

</div>

</div>

</section>


<section class="card">

<h2>
⚽ Match-Hub
</h2>

<p class="muted">

Diese Match-Seite wird automatisch
aktualisiert, sobald neue Daten verfügbar sind.

</p>

<p>
🌍 {country}
</p>

<p>
🆔 Match ID: {escape(str(event_id))}
</p>

</section>


<section class="card">

<h2>
📊 البيانات القادمة
</h2>

<p class="muted">

ستتم إضافة الإحصائيات والأخبار
والتفاصيل الإضافية عندما تتوفر مصادر
بيانات موثوقة لها.

</p>

</section>

</main>

</body>

</html>
"""

    MATCHES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = MATCHES_DIR / f"{slug}.html"

    path.write_text(
        html,
        encoding="utf-8"
    )

    return slug, title, dt


def build_home(matches):
    cards = []

    for event in matches:

        slug, title, dt = create_match_page(
            event
        )

        league = clean_text(
            event.get("strLeague"),
            "Nationalmannschaft"
        )

        venue = clean_text(
            event.get("strVenue"),
            "Spielort folgt"
        )

        cards.append(
            f"""
<div class="card">

<h2>
{escape(title)}
</h2>

<div class="date">
{format_date(dt)}
</div>

<p>
🏆 {league}
</p>

<p>
📍 {venue}
</p>

<a class="button"
href="matches/{slug}.html">

Match-Hub öffnen →

</a>

</div>
"""
        )

    if not cards:

        cards.append(
            """
<div class="card">

<h2>
Keine kommenden Spiele
</h2>

<p>
Aktuell wurden keine kommenden
Deutschland-Spiele gefunden.
</p>

</div>
"""
        )

    updated = datetime.now().astimezone()

    updated_text = updated.strftime(
        "%d.%m.%Y %H:%M"
    )

    return f"""<!doctype html>

<html lang="de">

<head>

<meta charset="utf-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>
Deutschland Spiele | Match-Hub
</title>

<meta name="description"
content="Automatisch aktualisierte kommende Spiele der deutschen Nationalmannschaft.">

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family:
        Arial,
        Helvetica,
        sans-serif;
    background: #f2f4f7;
    color: #111827;
}}

header {{
    background: #111827;
    color: white;
    padding: 28px 18px;
}}

main {{
    width: min(900px, 100%);
    margin: auto;
    padding: 16px;
}}

.hero {{
    background: white;
    border-radius: 20px;
    padding: 24px;
    margin-top: -10px;
    box-shadow:
        0 4px 20px
        rgba(0,0,0,.06);
}}

.card {{
    background: white;
    border-radius: 18px;
    padding: 20px;
    margin-top: 16px;
}}

.date {{
    font-size: 18px;
    font-weight: 700;
}}

.muted {{
    color: #6b7280;
}}

.button {{
    display: inline-block;
    margin-top: 10px;
    padding: 12px 16px;
    border-radius: 12px;
    background: #111827;
    color: white;
    text-decoration: none;
    font-weight: 700;
}}

</style>

</head>

<body>

<header>

<h1>
🇩🇪 Deutschland Match-Hub
</h1>

<p>
Automatisch aktualisierte Spiele
</p>

</header>

<main>

<section class="hero">

<h2>
🔜 Nächste Deutschland-Spiele
</h2>

<p class="muted">

Letzte Aktualisierung:
{updated_text}

</p>

</section>

{''.join(cards)}

</main>

</body>

</html>
"""


def cleanup_old_pages(valid_slugs):

    if not MATCHES_DIR.exists():
        return

    for file in MATCHES_DIR.glob("*.html"):

        if file.stem not in valid_slugs:

            try:
                file.unlink()

            except Exception:
                pass


def main():

    print("Starting football match engine...")

    OUT.mkdir(
        parents=True,
        exist_ok=True
    )

    MATCHES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    events = fetch_matches()

    now = datetime.now(timezone.utc)

    matches = []

    for event in events:

        dt = parse_datetime(event)

        if not dt:
            continue

        if dt < now:
            continue

        matches.append(event)

    matches.sort(
        key=lambda event:
        parse_datetime(event)
    )

    matches = matches[:MAX_MATCHES]

    valid_slugs = set()

    for event in matches:

        slug, _, _ = create_match_page(
            event
        )

        valid_slugs.add(slug)

    cleanup_old_pages(
        valid_slugs
    )

    home = build_home(
        matches
    )

    index_path = OUT / "index.html"

    index_path.write_text(
        home,
        encoding="utf-8"
    )

    print(
        f"Generated {len(matches)} upcoming matches."
    )

    print(
        "Football match engine completed successfully."
    )


if __name__ == "__main__":

    main()
