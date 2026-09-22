import os
import sys
import requests
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

SPORTSDB_URL = "https://www.thesportsdb.com/api/v1/json/3"


def fail(message):
    print(f"ERROR: {message}")
    sys.exit(1)


if not SUPABASE_URL:
    fail("SUPABASE_URL is missing")

if not SUPABASE_KEY:
    fail("SUPABASE_SERVICE_ROLE_KEY is missing")


HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}


def get_json(url):
    response = requests.get(
        url,
        headers={
            "User-Agent": "football-pipeline/1.0",
            "Accept": "application/json",
        },
        timeout=30,
    )

    if not response.ok:
        fail(
            f"TheSportsDB HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    return response.json()


def get_germany_team():
    data = get_json(
        f"{SPORTSDB_URL}/searchteams.php?t=Germany"
    )

    teams = data.get("teams") or []

    for team in teams:
        if (
            (team.get("strTeam") or "").lower() == "germany"
            and (team.get("strSport") or "").lower() == "soccer"
        ):
            return team

    if teams:
        return teams[0]

    fail("Germany team was not found")


def fetch_matches():
    team = get_germany_team()

    team_id = team.get("idTeam")

    if not team_id:
        fail("Germany team ID is missing")

    data = get_json(
        f"{SPORTSDB_URL}/eventsnext.php?id={team_id}"
    )

    return data.get("events") or []


def parse_kickoff(event):
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


def normalize_status(event):
    status = (
        event.get("strStatus")
        or event.get("status")
        or ""
    ).upper()

    if status in ("FT", "FINISHED"):
        return "finished"

    if status in ("LIVE", "IN PLAY", "IN_PLAY"):
        return "live"

    if status in ("POSTPONED",):
        return "postponed"

    if status in ("CANCELLED", "CANCELED"):
        return "cancelled"

    return "scheduled"


def normalize_match(event):
    event_id = event.get("idEvent")

    kickoff = parse_kickoff(event)

    if not event_id or not kickoff:
        return None

    return {
        "external_id": str(event_id),

        "home_team": (
            event.get("strHomeTeam")
            or "Unknown"
        ),

        "away_team": (
            event.get("strAwayTeam")
            or "Unknown"
        ),

        "home_team_id": (
            str(event["idHomeTeam"])
            if event.get("idHomeTeam")
            else None
        ),

        "away_team_id": (
            str(event["idAwayTeam"])
            if event.get("idAwayTeam")
            else None
        ),

        "competition": (
            event.get("strLeague")
            or "Unknown"
        ),

        "kickoff_at": kickoff.isoformat(),

        "venue": event.get("strVenue"),

        "status": normalize_status(event),

        "home_score": (
            int(event["intHomeScore"])
            if str(event.get("intHomeScore") or "").isdigit()
            else None
        ),

        "away_score": (
            int(event["intAwayScore"])
            if str(event.get("intAwayScore") or "").isdigit()
            else None
        ),

        "prediction_locked": kickoff <= datetime.now(timezone.utc),

        "source": "TheSportsDB",

        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


def sync_matches(matches):
    if not matches:
        print("No matches found.")
        return

    url = f"{SUPABASE_URL}/rest/v1/matches"

    response = requests.post(
        url,
        headers=HEADERS,
        params={"on_conflict": "external_id"},
        json=matches,
        timeout=30,
    )

    if not response.ok:
        print(response.text)
        fail(
            f"Supabase HTTP {response.status_code}"
        )

    print(
        f"SUCCESS: {len(matches)} matches synced to Supabase"
    )


def main():

    print("===================================")
    print("FOOTBALL PIPELINE")
    print("TheSportsDB -> Supabase")
    print("===================================")

    events = fetch_matches()

    print(
        f"TheSportsDB returned {len(events)} events"
    )

    matches = []

    for event in events:
        match = normalize_match(event)

        if match:
            matches.append(match)

    print(
        f"Prepared {len(matches)} matches"
    )

    sync_matches(matches)

    print("DONE")


if __name__ == "__main__":
    main()
