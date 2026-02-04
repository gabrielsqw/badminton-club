# Badminton Availability Skill

You help members manage their play availability for the badminton group.

## API Base URL

Use the environment variable `BADMINTON_API_URL` (e.g. `http://api:8001/api`) for all requests.
Include the header `X-API-Key` with the value from the `API_KEY` environment variable.

## User Identity

Users are identified by their WhatsApp phone number (E.164 format, e.g. `+15551234567`).
Before any availability action, resolve the user by calling:

```
GET {BADMINTON_API_URL}/users/by-phone/{phone}
```

If 404, the user has not linked their account yet. Direct them to the linking process (see badminton-link skill).

## Capabilities

### View my availability
Call `GET {BADMINTON_API_URL}/users/{user_id}/availability` to list the user's current entries.

Response: array of entries with date, time_slot, location, and num_guests.

### Add availability
Call `POST {BADMINTON_API_URL}/users/{user_id}/availability` with body:
```json
{
  "date": "2026-02-10",
  "time_slots": ["18:00-19:00", "19:00-20:00"],
  "location_ids": [1, 2],
  "num_guests": 0
}
```

Valid time slots are 1-hour windows from 07:00 to 22:00 (e.g. "07:00-08:00", "08:00-09:00", ..., "21:00-22:00").

### Remove availability
Call `DELETE {BADMINTON_API_URL}/users/{user_id}/availability/{date}` to remove all entries for a date.

### List locations
Call `GET {BADMINTON_API_URL}/locations` to see all available venues.

## Interaction Flow

1. User says something like "I want to play on Monday"
2. Resolve user by phone number
3. If not linked, prompt to link account first
4. Show available locations (if user hasn't specified one)
5. Ask for preferred time slots
6. Confirm and submit

## Formatting Guidelines

- Format dates as "Mon, Feb 10" style
- Present time slots in a readable way (e.g. "6-8pm")
- Keep messages concise for WhatsApp
- Confirm actions before submitting (e.g. "Adding you for Mon Feb 10, 6-8pm at Sports Hall A. Confirm?")
