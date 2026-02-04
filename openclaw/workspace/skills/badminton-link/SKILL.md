---
name: badminton-link
description: Link your WhatsApp number to your badminton club account.
metadata: { "openclaw": { "emoji": "🔗" } }
---

# Badminton Account Linking Skill

You help new WhatsApp users link their phone number to their badminton club account.

## API Base URL

Use the environment variable `BADMINTON_API_URL` (e.g. `http://api:8001/api`) for all requests.
Include the header `X-API-Key` with the value from the `API_KEY` environment variable.

## When to Use

This skill activates when a user's phone number is not yet linked to an account.
Other skills (like badminton-availability) will direct unlinked users here.

## Linking Flow

1. Ask the user for their badminton club username
2. Call `POST {BADMINTON_API_URL}/users/link-phone` with body:
   ```json
   {
     "username": "their_username",
     "phone_number": "+15551234567"
   }
   ```
3. On success (200): confirm linking and tell them they can now manage availability
4. On 404: username not found, ask them to check spelling or register on the website first
5. On 409: phone number already linked to another account

## Formatting Guidelines

- Be welcoming to new users
- Keep messages concise for WhatsApp
- If linking fails, provide clear next steps
