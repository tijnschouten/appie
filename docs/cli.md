# CLI

## `appie-login`

Authenticate and store tokens locally:

```bash
uv run appie-login
```

The CLI is intended as a one-time or occasional setup step. Day-to-day usage should normally rely on stored tokens and automatic refresh.

Expected outcome:
- a Chrome window opens for login
- the CLI captures the redirect code automatically
- it prints a success message after storing tokens
