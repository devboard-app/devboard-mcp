from html import escape
from string import Template

_LAYOUT = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in to DevBoard</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; display: grid; place-items: center; min-height: 100vh; margin: 0; }
  main { width: min(360px, 90vw); display: grid; gap: 12px; }
  input, button { padding: 10px; font: inherit; }
  .error { color: #b3261e; }
</style>
</head>
<body><main>$body</main></body>
</html>""")

_FORM = Template("""<form method="post" action="/login" style="display:grid;gap:12px">
  <h1>Sign in to DevBoard</h1>
  <p><strong>$requester</strong> is asking to access your DevBoard tickets.</p>
  $error
  <input type="hidden" name="session" value="$session">
  <input type="email" name="email" placeholder="Email" autocomplete="username" required autofocus>
  <input type="password" name="password" placeholder="Password" autocomplete="current-password" required>
  <button type="submit">Sign in</button>
</form>""")


def render_login_page(session: str, requester: str, error: str | None = None) -> str:
    error_html = f'<p class="error">{escape(error)}</p>' if error else ""
    body = _FORM.substitute(
        session=escape(session, quote=True),
        requester=escape(requester),
        error=error_html,
    )
    return _LAYOUT.substitute(body=body)


def render_message_page(message: str) -> str:
    return _LAYOUT.substitute(body=f"<p>{escape(message)}</p>")
