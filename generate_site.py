import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from html import escape

API_BASE = "https://www.thesportsdb.com/api/v1/json/3"
OUT = Path("docs")


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "football-pipeline/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_matches():
    query = urllib.parse.urlencode({"t": "Germany"})
    search_url = f"{API_BASE}/searchteams.php?{query}"

    data = get_json(search_url)
    teams = data.get("teams") or []

    team = None

    for item in teams:
        if (
            (item.get("strTeam") or "").lower() == "germany"
            and (item.get("strSport") or "").lower() == "soccer"
        ):
            team = item
            break

    if not team and teams:
        team = teams[0]

    if not team:
        raise RuntimeError("Germany national team not found")

    team_id = team["idTeam"]

    matches_url = f"{API_BASE}/eventsnext.php?id={team_id}"
    matches_data = get_json(matches_url)

    return matches_data.get("events") or []


def parse_datetime(event):
    date = event.get("dateEvent")
    time = event.get("strTime") or "00:00:00"

    if not date:
        return None

    try:
        return datetime.fromisoformat(
            f"{date}T{time}"
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
    slug = (
        text.lower()
        .replace(" ", "-")
        .replace("–", "-")
        .replace("/", "-")
        .replace("&", "and")
    )

    return f"{slug}-{event_id}"


def create_page(match):
    home = match.get("strHomeTeam") or "Deutschland"
    away = match.get("strAwayTeam") or "Gegner"

    title = f"{home} – {away}"

    event_id = match.get("idEvent") or ""

    slug = slugify(title, event_id)

    dt = parse_datetime(match)

    venue = match.get("strVenue") or "Spielort folgt"

    league = (
        match.get("strLeague")
        or "Nationalmannschaft"
    )

    detail_dir = OUT / "matches"
    detail_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    html = f"""<!doctype html>
<html lang="de">

<head>

<meta charset="utf-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>{escape(title)} | Deutschland Match-Hub</title>

<meta name="description"
content="{escape(title)} – Termin, Spielort und Match-Informationen.">

<style>

body {{
    font-family: Arial, sans-serif;
    background: #f4f4f4;
    margin: 0;
}}

main {{
    max-width: 800px;
    margin: auto;
    padding: 20px;
}}

.card {{
    background: white;
    padding: 24px;
    border-radius: 18px;
    margin: 15px 0;
}}

a {{
    color: #155eef;
}}

</style>

</head>

<body>

<main>

<p>
<a href="../">← Alle Deutschland-Spiele</a>
</p>

<div class="card">

<h1>{escape(title)}</h1>

<h2>{format_date(dt)}</h2>

<p>
🏆 {escape(league)}
</p>

<p>
📍 {escape(venue)}
</p>

</div>

<div class="card">

<h2>⚽ Match-Hub</h2>

<p>
Alle wichtigen Informationen zu diesem Spiel
werden automatisch auf dieser Seite aktualisiert.
</p>

</div>

</main>

</body>

</html>
"""

    file = detail_dir / f"{slug}.html"

    file.write_text(
        html,
        encoding="utf-8"
    )

    return slug, title, dt, venue, league


def main():

    OUT.mkdir(
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
        key=lambda x: parse_datetime(x)
    )

    cards = []

    for event in matches[:20]:

        slug, title, dt, venue, league = create_page(
            event
        )

        cards.append(
            f"""
<div class="card">

<h2>{escape(title)}</h2>

<p>
<b>{format_date(dt)}</b>
</p>

<p>
🏆 {escape(league)}
</p>

<p>
📍 {escape(venue)}
</p>

<a href="matches/{slug}.html">
Match-Hub öffnen →
</a>

</div>
"""
        )

    if not cards:

        cards.append(
            """
<div class="card">
Keine kommenden Spiele gefunden.
</div>
"""
        )

    html = f"""<!doctype html>

<html lang="de">

<head>

<meta charset="utf-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>Deutschland Spiele | Match-Hub</title>

<meta name="description"
content="Automatisch aktualisierte Spiele der deutschen Nationalmannschaft.">

<style>

body {{
    font-family: Arial, sans-serif;
    background: #f4f4f4;
    margin: 0;
}}

main {{
    max-width: 800px;
    margin: auto;
    padding: 20px;
}}

.card {{
    background: white;
    padding: 24px;
    border-radius: 18px;
    margin: 15px 0;
}}

.muted {{
    color: #666;
}}

</style>

</head>

<body>

<main>

<div class="card">

<h1>🇩🇪 Deutschland – Spiele</h1>

<p class="muted">
Diese Seite wird automatisch aktualisiert.
</p>

<p>
Letzte Aktualisierung:
{datetime.now().astimezone().strftime("%d.%m.%Y %H:%M")}
</p>

</div>

<h2>🔜 Nächste Spiele</h2>

{''.join(cards)}

</main>

</body>

</html>
"""

    (OUT / "index.html").write_text(
        html,
        encoding="utf-8"
    )

    print(
        f"Created {len(matches)} upcoming matches."
    )


if __name__ == "__main__":
    main()
