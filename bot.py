
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

CHANNEL = "annet_mouse"
TZ = ZoneInfo("Europe/Moscow")
LEAD_MINUTES = 120
STATE = Path("posted.json")


def request_json(url, headers=None, data=None):
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers or {}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")
        # Discord может вернуть HTTP 204 без тела ответа.
        return json.loads(body) if body.strip() else None


def twitch_token(client_id, secret):
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": secret,
        "grant_type": "client_credentials",
    }).encode()

    result = request_json(
        "https://id.twitch.tv/oauth2/token",
        {"Content-Type": "application/x-www-form-urlencoded"},
        data,
    )
    return result["access_token"]



def twitch_get(url, client_id, token):
    try:
        return request_json(url, {
            "Client-Id": client_id,
            "Authorization": f"Bearer {token}",
        })
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        headers = error.headers or {}

        details = {
            "http_status": error.code,
            "response": body[:1000],
            "ratelimit_limit": headers.get("Ratelimit-Limit"),
            "ratelimit_remaining": headers.get("Ratelimit-Remaining"),
            "ratelimit_reset": headers.get("Ratelimit-Reset"),
            "retry_after": headers.get("Retry-After"),
        }

        raise RuntimeError(
            "Twitch API request failed: "
            + json.dumps(details, ensure_ascii=False)
        ) from error


def get_segments(client_id, token):
    print("Looking up Twitch channel...", flush=True)

    url = (
        "https://api.twitch.tv/helix/users?"
        + urllib.parse.urlencode({"login": CHANNEL})
    )

    users = twitch_get(url, client_id, token).get("data", [])

    if not users:
        raise RuntimeError(
            f"Twitch channel {CHANNEL!r} not found"
        )

    broadcaster_id = users[0]["id"]
    print("Channel found. Loading schedule...", flush=True)

    segments = []
    cursor = None
    seen_cursors = set()
    max_pages = 5

    for page in range(1, max_pages + 1):
        print(
            f"Loading schedule page {page}/{max_pages}...",
            flush=True
        )

        params = {
            "broadcaster_id": broadcaster_id,
            "first": "25"
        }

        if cursor:
            params["after"] = cursor

        url = (
            "https://api.twitch.tv/helix/schedule?"
            + urllib.parse.urlencode(params)
        )

        result = twitch_get(url, client_id, token)

        segments.extend(
            result.get("data", {}).get("segments", [])
        )

        next_cursor = result.get("pagination", {}).get("cursor")

        if not next_cursor:
            print(
                f"Schedule loaded. Segments: {len(segments)}",
                flush=True
            )
            return segments

        if next_cursor in seen_cursors:
            raise RuntimeError(
                "Twitch returned a repeated pagination cursor."
            )

        seen_cursors.add(next_cursor)
        cursor = next_cursor

    raise RuntimeError(
        f"Schedule has more than {max_pages} pages. "
        "Stopped to prevent an endless loop."
    )



def send_telegram(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
    }).encode()

    request_json(
        f"https://api.telegram.org/bot{token}/sendMessage",
        {"Content-Type": "application/x-www-form-urlencoded"},
        data,
    )


def send_discord(message):
    data = json.dumps({
        "content": message
    }).encode()

    request_json(
        os.environ["DISCORD_WEBHOOK_URL"],
        {"Content-Type": "application/json"},
        data,
    )


def main():
    client_id = os.environ["TWITCH_CLIENT_ID"]
    client_secret = os.environ["TWITCH_CLIENT_SECRET"]

    token = twitch_token(client_id, client_secret)
    segments = get_segments(client_id, token)

    now = datetime.now(timezone.utc).timestamp()

    posted = (
        set(json.loads(STATE.read_text(encoding="utf-8")))
        if STATE.exists()
        else set()
    )

    changed = False

    for segment in segments:
        start = datetime.fromisoformat(
            segment["start_time"].replace("Z", "+00:00")
        )

        # Анонсируем только в течение двух часов
        # перед началом стрима.
        if (
            now < start.timestamp() - LEAD_MINUTES * 60
            or now >= start.timestamp()
        ):
            continue

        title = segment.get("title") or "Стрим"

        key = (
            f'{segment.get("id", "")}|'
            f'{segment["start_time"]}|{title}'
        )

        if key in posted:
            continue

        local = start.astimezone(TZ)

        message = (
            f"🎮 {title}\n\n"
            f"📅 Дата: {local:%d.%m.%Y}\n"
            f"🕒 Время: {local:%H:%M} (МСК)\n\n"
            "⚠️ Возможны изменения"
        )

        send_telegram(message)
        send_discord(message)

        posted.add(key)
        changed = True

        print(
            f"Sent announcement for Twitch segment "
            f"{segment.get('id')}"
        )

    if changed:
        STATE.write_text(
            json.dumps(
                sorted(posted),
                ensure_ascii=False,
                indent=2
            ) + "\n",
            encoding="utf-8",
        )
    else:
        print("No announcements due.")


if __name__ == "__main__":
    main()
