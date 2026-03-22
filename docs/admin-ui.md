# Admin UI Guide

The admin UI is available at `/admin` and is intended for **superusers** who manage the chatbot configuration.

## Accessing the Admin UI

Open your browser to:

```
http://localhost:8000/admin       # local dev
https://your-domain.com/admin     # production
```

Sign in with an account that has the `superuser` role in PocketBase.

## Screen Layout

### Top Bar

| Element | Description |
|---|---|
| **Bot icon** | Displayed if `BOT_ICON_URL` is set in `.env`. Shows the custom icon for this clone. |
| **Bot name** | The name configured via `BOT_NAME` in `.env` (default: "Chat Assistant"). |
| **Backend badge** | Shows the currently selected retrieval backend (e.g. `none`, `rag_store`). Updates when you change the Backend dropdown. |
| **User email** | Your logged-in email address. |
| **Sign out** | Ends your session and returns to the login screen. |

### Settings Bar

This bar is **only visible in the admin UI** and gives you direct control over how each chat request is processed.

| Control | What it does |
|---|---|
| **Backend** dropdown | Override the retrieval backend for the next message. Options: `Use config default`, `None (direct Gemini)`, `RAG Store`, `Vertex Search`, `Vector Search`. When set to "Use config default", the active PocketBase config decides. |
| **Config ID** dropdown | Pick a specific `rag_configs` record from PocketBase. The dropdown loads all configs and marks the active one. When set to "Active config", the system uses whichever config has `is_active=true`. |

### Chat Area

- **User messages** appear on the right in blue.
- **Bot responses** appear on the left in dark gray.
- If the response includes retrieval sources (RAG/Search/Vector modes), a collapsible **"N source(s)"** section appears below the answer showing source URIs and relevance scores.
- A **typing indicator** (three bouncing dots) shows while waiting for the LLM response.

### Input Area

- Type your message and press **Enter** to send, or click the **Send** button.
- Press **Shift+Enter** for a new line without sending.
- The textarea auto-grows as you type (up to 150px height).

## What Admins Can Do

### 1. Test Different Backends

Use the Backend dropdown to quickly switch between retrieval modes and compare results for the same query.

### 2. Test Different Configurations

Use the Config ID dropdown to try different system prompts, temperature settings, or retrieval parameters without editing anything.

### 3. View Statistics

Call the stats API endpoint to see usage data:

```
GET /api/admin/stats
Authorization: Bearer YOUR_TOKEN
```

Returns:
- Total users, superusers, regular users
- Total chats, chats per backend
- Last 10 chat queries
- Active config info

### 4. Manage RAG Configs

Use the PocketBase admin UI at `/pb/_/` or the API:

```
GET    /api/admin/rag-configs          # list all
POST   /api/admin/rag-configs          # create
PATCH  /api/admin/rag-configs/{id}     # update
DELETE /api/admin/rag-configs/{id}     # delete
```

### 5. Monitor Errors

If SMTP is configured in `.env`, superusers listed in `ERROR_NOTIFY_EMAILS` receive email notifications when unhandled errors occur, including:
- Error type and message
- Request context (method, path)
- User who triggered it
- Full Python traceback

### 6. Review Moderation Logs

The platform automatically blocks harmful content (harassment, hate speech, threats, etc.). View all moderation violations:

```bash
GET /api/admin/moderation-logs?page=1&per_page=50
Authorization: Bearer YOUR_TOKEN
```

Each log entry shows:
- **Category**: which safety filter was triggered (e.g. `sexual_harassment`, `hate_speech`)
- **Direction**: whether the blocked content was user `input` or bot `output`
- **User email**: who triggered the violation
- **Matched pattern**: the specific phrase that was caught
- **Text snippet**: first 500 chars of the blocked message

You can also view these directly in PocketBase admin under the `moderation_logs` collection.

## Differences from the User UI

| Feature | User UI (`/`) | Admin UI (`/admin`) |
|---|---|---|
| Backend selector | No | Yes |
| Config selector | No | Yes |
| Backend badge | No | Yes |
| Source citations | No | Yes |
| Stats endpoint | No | Yes (via API) |
| Moderation log access | No | Yes (via API) |
| Branding | Full | Partial (name + icon) |
