# Flask Microblog

A full-featured microblogging application built while following the [Flask Mega-Tutorial by Miguel Grinberg](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world). This project serves as a hands-on deep-dive into the Flask ecosystem, covering authentication, ORM, REST APIs, i18n, and more.

## Features

- **User accounts** — registration, login/logout, password reset via JWT email link
- **Posts** — create posts with automatic language detection, delete
- **Social** — follow/unfollow users, personalized feed
- **Profiles** — avatar (Gravatar), "about me", last-seen tracking
- **REST API** — `/api/posts` with offset-based and keyset-based pagination
- **AJAX translation** — translate posts inline using Google Cloud Translate
- **Internationalization** — Flask-Babel i18n/l10n pipeline (`.pot` → `.po` → `.mo`)
- **Error handling** — custom 404/500 pages, SMTP and rotating-file error logging
- **Bootstrap UI** — custom theme, responsive layout

## Tech Stack

| Layer | Libraries |
|---|---|
| Framework | Flask 3.1, Werkzeug, Click |
| Database | SQLAlchemy 2.0, Flask-SQLAlchemy, Flask-Migrate (Alembic) |
| Auth | Flask-Login, Flask-WTF (CSRF), PyJWT, Werkzeug password hashing |
| Forms | WTForms, email-validator |
| Email | Flask-Mail |
| Translations | Flask-Babel, Google Cloud Translate, langdetect |
| Datetime | Flask-Moment |
| Dev tooling | python-dotenv, aiosmtpd (local SMTP debug server) |

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
#    Copy the template and fill in values
cp .env.example .env          # sensitive: SECRET_KEY, MAIL_*, GOOGLE_APPLICATION_CREDENTIALS
# .flaskenv already sets FLASK_APP=microblog.py

# 4. Initialize the database
flask db upgrade

# 5. Compile translations
flask translate compile

# 6. Run the development server
flask run
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask secret key for CSRF and sessions |
| `DATABASE_URL` | No | Database URI (defaults to `sqlite:///app.db`) |
| `MAIL_SERVER` | No | SMTP server hostname |
| `MAIL_PORT` | No | SMTP port (default: 25) |
| `MAIL_USE_TLS` | No | Enable TLS (set to any value to enable) |
| `MAIL_USERNAME` | No | SMTP username |
| `MAIL_PASSWORD` | No | SMTP password |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | Path to GCP service account JSON for translation |

For local email testing without a live server:

```bash
aiosmtpd -n -c aiosmtpd.handlers.Debugging -l localhost:8025
export MAIL_SERVER=localhost MAIL_PORT=8025
```

## Translation CLI

```bash
flask translate init LANG    # add a new language (e.g. jp)
flask translate update       # sync .po files after marking new strings
flask translate compile      # compile .po → .mo for runtime use
```

## REST API

| Endpoint | Auth | Description |
|---|---|---|
| `GET /api/posts` | Required | Paginated posts (offset or keyset) |
| `POST /api/translate` | Required | Translate text via Google Cloud Translate |

Key query parameters for `GET /api/posts`:

- `search_condition` — `all` \| `current_user_and_following` \| `user`
- `pagination_type` — `offset` (default) \| `keyset`
- `per_page` — items per page
- `page` — page number (offset mode)
- `cursor_timestamp` / `cursor_id` — cursor values (keyset mode)

## Key Learnings

### Application Architecture
- **Application factory pattern** — wrapping app creation in `create_app()` decouples configuration from the module import, making testing and multi-environment setups straightforward.
- **Blueprints** — splitting the app into `auth`, `main`, `api`, `errors`, and `cli` blueprints mirrors the concept of Areas (ASP.NET Core MVC) or Routers (Express.js). Route names become namespaced: `url_for('auth.login')` instead of `url_for('login')`.
- **Flask contexts** — Flask pushes an app context and request context automatically for each request; they must be pushed manually in CLI commands, background tasks, and tests. `current_app`, `g`, `request`, and `session` are all context-locals, not globals.
- **`.env` vs `.flaskenv`** — `.flaskenv` holds non-sensitive config loaded only by the `flask` CLI; `.env` holds secrets and is loaded explicitly so it also works in production outside the CLI.

### Database & ORM
- **SQLAlchemy 2.0 style** — columns are declared with `so.Mapped[T]` type hints and `so.mapped_column()`. `Optional[T]` maps to a nullable column; a bare `T` is non-nullable.
- **Self-referential many-to-many** — the followers relationship uses an association table with explicit `primaryjoin` and `secondaryjoin` to tell SQLAlchemy which side is "left" and which is "right".
- **Migrations** — `flask db migrate` auto-generates an Alembic script with `upgrade()` and `downgrade()` functions. Every schema change should go through this flow rather than modifying the DB directly.
- **Pagination strategies** — offset-based (`OFFSET n LIMIT k`) is simple but degrades on large tables. Keyset-based pagination uses a `(timestamp, id)` cursor in the `WHERE` clause; results stay stable even as new rows are inserted, making it ideal for infinite scroll.

### Auth & Security
- **Password hashing** — Werkzeug's `generate_password_hash` / `check_password_hash` handle salting automatically; never store plain-text passwords.
- **CSRF protection** — Flask-WTF injects a hidden token via `form.hidden_tag()` and validates it on every POST. The `SECRET_KEY` is the cryptographic basis for this token.
- **Safe redirects** — after login, the `next` query parameter is validated with `urlsplit(next).netloc == ''` before following it, preventing open-redirect attacks to external domains.
- **JWT password reset** — a short-lived token encodes the user ID and expiry. Verification decodes and checks expiry without any server-side state.

### Forms
- **`validate_on_submit()`** — returns `True` only on POST requests that pass all validators, cleanly combining the GET/POST check.
- **Lazy strings** — form labels and Flask-Login messages are defined at import time, before any request exists. `lazy_gettext` (aliased `_l`) defers translation lookup until the string is rendered inside a request.
- **Post/Redirect/Get** — after a successful form POST, always redirect so that a page refresh doesn't resubmit the form.

### Internationalization (I18n)
- **Extraction → init → translate → compile** — `pybabel extract` scans marked strings into a `.pot` template; `pybabel init` creates per-language `.po` files; human translators fill them in; `pybabel compile` produces binary `.mo` files read at runtime.
- **`_()` vs `_l()`** — use `_()` inside view functions (request is active); use `_l()` for module-level strings like form labels (no request yet).
- **Custom CLI commands** — Click (Flask's CLI backbone) lets you wrap the pybabel commands into `flask translate init/update/compile` so teammates don't need to remember the full pybabel invocations.

### Error Handling & Logging
- **`@bp.app_errorhandler`** — unlike `@bp.errorhandler`, this registers the handler application-wide from inside a blueprint.
- **`SMTPHandler`** — attaches to `app.logger` and emails the traceback to admins on `ERROR`-level events; only active outside debug mode.
- **`RotatingFileHandler`** — caps log files at 10 KB with up to 10 backups, preventing unbounded disk growth.

### AJAX & Real-Time UX
- **Language detection on write** — `langdetect` runs at post-creation time and stores the result in the DB, so the "Translate" link can be shown or hidden without an extra API call per render.
- **Keyset cursor over the API** — the `/api/posts` endpoint returns `next_cursor` (`timestamp` + `id`) so the JS client can request the next batch without tracking a page number.

## Project Structure

```
microblog/
├── app/
│   ├── __init__.py        # application factory
│   ├── models.py          # User, Post, QueryUtility
│   ├── constants.py
│   ├── translate.py       # Google Cloud Translate wrapper
│   ├── auth/              # blueprint: login, register, password reset
│   ├── main/              # blueprint: index, explore, profile, follow
│   ├── api/               # blueprint: REST endpoints
│   ├── errors/            # blueprint: 404/500 handlers
│   ├── cli/               # blueprint: translate CLI commands
│   ├── templates/
│   └── static/
├── migrations/
├── .flaskenv
├── .env                   # not committed — secrets
├── config.py
└── microblog.py           # entry point
```
