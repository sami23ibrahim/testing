# User UI Guide

The user UI is the default interface available at `/` and is designed for **regular users** who just want to chat.

## Accessing the User UI

Open your browser to:

```
http://localhost:8000              # local dev
https://your-domain.com           # production
```

This is the default page. No special URL needed.

## Screen Layout

### Login Screen

| Element | Description |
|---|---|
| **Bot icon** | Custom icon if configured (from `BOT_ICON_URL` in `.env`). |
| **Bot name** | Displayed as the page title. Configured via `BOT_NAME` in `.env`. |
| **Email / Password** | Your login credentials. |
| **Register link** | Click "Register" to create a new account, then auto-login. |

### Chat Screen

| Element | Description |
|---|---|
| **Top bar** | Shows the bot icon, bot name, your email, and a sign out button. |
| **Welcome area** | Shows a large bot icon, welcome title, and welcome subtitle. These are customizable per clone via `.env`. Disappears after first message. |
| **Messages** | User messages (right, blue) and bot responses (left, dark). Clean and simple — no technical details like backend or sources. |
| **Typing indicator** | Three bouncing dots while the bot is thinking. |
| **Input area** | Type and press Enter to send, Shift+Enter for new line. Auto-resizes. |
| **Powered by** | Optional footer text, set via `POWERED_BY_TEXT` in `.env`. |

## What Users Can Do

### Chat

Type a question and press Enter. The bot responds using whichever retrieval backend and system prompt the superuser has configured as active. Users have no control over these settings — they just chat.

### Register

Click "Register" on the login screen to create a new account. New accounts get the `user` role by default (no admin access).

### Sign Out

Click "Sign out" in the top bar to end your session.

### Safety Filters

All messages are automatically checked for harmful content including harassment, hate speech, threats, and explicit material. If a message is blocked, you'll see a message like:

> "Your message was blocked by our safety filter. This platform does not allow harassment, hate speech, threats, sexually explicit content, or other harmful material. Please rephrase your message respectfully."

This applies to both your messages and bot responses. The filters cannot be disabled by regular users.

## What Users Cannot Do

- Change the retrieval backend
- Select a different RAG configuration
- View retrieval sources or scores
- Access the stats endpoint
- Manage RAG configs
- Access the admin UI
- Disable content moderation filters
- View moderation violation logs

These restrictions are enforced both in the UI (controls are absent) and the API (role-based access).

## Customization (for Admins)

The user UI reads its branding from the `/api/branding` endpoint, which is configured via `.env`:

| `.env` Variable | What it controls | Default |
|---|---|---|
| `BOT_NAME` | Page title, login heading, top bar title | `Chat Assistant` |
| `BOT_ICON_URL` | Icon on login, welcome screen, top bar, and favicon | _(none)_ |
| `WELCOME_TITLE` | Large text on the welcome screen | `How can I help you?` |
| `WELCOME_SUBTITLE` | Smaller text below the welcome title | `Ask me anything.` |
| `POWERED_BY_TEXT` | Footer text at the bottom of the chat | _(none)_ |

### Example `.env` for a custom clone

```env
BOT_NAME=Acme Support
BOT_ICON_URL=https://example.com/acme-logo.png
WELCOME_TITLE=Welcome to Acme Support
WELCOME_SUBTITLE=Ask about our products, billing, or anything else.
POWERED_BY_TEXT=Powered by Acme AI
```

Each VM clone can have different values, giving each deployment its own identity.
