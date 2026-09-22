import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from html import escape

API = (
    "https://site.api.espn.com/apis/site/v2/sports/"
    "soccer/all/teams/ger/schedule?limit=50"
)

OUT = Path("docs")
OUT.mkdir(exist_ok=True)


def fetch():
    req = urllib.request.Request(
        API,
        headers={"User-Agent": "football-match-engine/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fmt_date(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d.%m.%Y · %H:%M")
    except Exception:
        return value or "Termin folgt"


def main():
    data = fetch()
    events = data.get("events", [])

    now = datetime.now(timezone.utc)
    matches = []

    for event in events:
        try:
            dt = datetime.fromisoformat(
                event["date"].replace("Z", "+00:00")
            )
        except Exception:
            continue

        competition = (event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors") or []

        if len(competitors) < 2:
            continue

        teams = [
            c.get("team", {}).get("displayName", "Team")
            for c in competitors[:2]
        ]

        venue = (
            competition.get("venue", {}).get("fullName")
            or "Spielort folgt"
        )

        matches.append({
            "date": dt,
            "teams": teams,
            "venue": venue,
            "id": event.get("id", ""),
        })

    matches.sort(key=lambda x: x["date"])

    upcoming = [m for m in matches if m["date"] >= now]

    cards = []

    for match in upcoming[:20]:
        title = " – ".join(match["teams"])
        slug = (
            title.lower()
            .replace(" ", "-")
            .replace("–", "-")
            .replace("/", "-")
        )

        detail_dir = OUT / "matches"
        detail_dir.mkdir(exist_ok=True)

        detail = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Match-Hub</title>
<style>
body{{font-family:Arial,sans-serif;background:#f4f4f4;margin:0}}
main{{max-width:800px;margin:auto;padding:20px}}
.card{{background:white;padding:22px;border-radius:18px;margin:15px 0}}
a{{color:#155eef}}
</style>
</head>
<body>
<main>
<p><a href="../">← Alle Spiele</a></p>
<div class="card">
<h1>{escape(title)}</h1>
<h2>{fmt_date(match["date"].isoformat())}</h2>
<p>📍 {escape(match["venue"])}</p>
</div>

<div class="card">
<h2>Match-Hub</h2>
<p>Übertragung, Aufstellung, Live-Infos und weitere Informationen
werden hier automatisch ergänzt.</p>
</div>
</main>
</body>
</html>"""

        (detail_dir / f"{slug}.html").write_text(
            detail, encoding="utf-8"
        )

        cards.append(f"""
<div class="card">
<h2>{escape(title)}</h2>
<p><b>{fmt_date(match["date"].isoformat())}</b></p>
<p>📍 {escape(match["venue"])}</p>
<a href="matches/{slug}.html">Match-Hub öffnen →</a>
</div>
""")

    html = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Deutschland Spiele | Match-Hub</title>
<meta name="description"
content="Aktuelle Spiele der deutschen Nationalmannschaft.">
<style>
body{{font-family:Arial,sans-serif;background:#f4f4f4;margin:0}}
main{{max-width:800px;margin:auto;padding:20px}}
.card{{background:white;padding:22px;border-radius:18px;margin:15px 0}}
.muted{{color:#666}}
</style>
</head>
<body>
<main>
<div class="card">
<h1>🇩🇪 Deutschland – Spiele</h1>
<p class="muted">
Diese Seite wird automatisch aktualisiert.
</p>
<p>Letzte Aktualisierung:
{datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
</div>

<h2>🔜 Nächste Spiele</h2>

{''.join(cards) or
'<div class="card">Keine Spiele قادمة في المصدر حاليًا.</div>'}

</main>
</body>
</html>"""

    (OUT / "index.html").write_text(html, encoding="utf-8")

    print(f"Created {len(upcoming)} upcoming matches.")


if __name__ == "__main__":
    main()
