---
name: badminton-sessions
description: View upcoming badminton sessions via WhatsApp.
metadata: { "openclaw": { "emoji": "🏸" } }
---

# Badminton Sessions Skill

You help members check upcoming badminton sessions.

## API Base URL

Use the environment variable `BADMINTON_API_URL` (e.g. `http://api:8001/api`) for all requests.
Include the header `X-API-Key` with the value from the `API_KEY` environment variable.

## Capabilities

### View upcoming sessions
Call `GET {BADMINTON_API_URL}/sessions/upcoming` to list all sessions in the next 14 days.

Response format:
```json
[{"date": "2026-02-10", "total_interest": 5}, ...]
```

### View session details
Call `GET {BADMINTON_API_URL}/sessions/{date}` to see who is playing on a specific date.

Response format:
```json
{
  "date": "2026-02-10",
  "total_interest": 5,
  "slots": [
    {
      "time_slot": "18:00-19:00",
      "location": {"id": 1, "name": "Sports Hall A"},
      "members": [{"username": "alice", "num_guests": 1}]
    }
  ]
}
```

## Formatting Guidelines

- Format dates as "Mon, Feb 10" style
- Group consecutive time slots (e.g. "6-8pm" instead of "18:00-19:00, 19:00-20:00")
- Keep messages concise for WhatsApp
- Show member count and names when available
