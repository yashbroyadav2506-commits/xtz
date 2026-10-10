# BookSwap

BookSwap is a responsive Flask application for students to list books, discover books shared by others, and coordinate exchange requests.

## Features

- Account registration, login, logout, and securely hashed passwords.
- Create, edit, and delete your own book listings.
- Search books by title or author; filter by category, condition, and exchange status; sort and paginate results.
- Book detail pages identify the owner and show availability.
- Real book covers are looked up through Open Library; designed title/author covers are shown when no matching cover is available.
- A dashboard for listings, incoming requests, and requests you've sent.
- Request, accept, decline, or cancel exchanges with status updates.
- CSRF protection for all form submissions and owner/requester authorization checks.
- Flask-Migrate database migrations, a SQLite default, and a repeatable demo-data seed command.

## Requirements

- Python 3.11 or newer
- A virtual environment

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a private `SECRET_KEY` in `.env` before deploying. The database defaults to the SQLite file `instance/books_swap.db` for local development. Vercel's function filesystem is not persistent, so production must set `DATABASE_URL` to a persistent PostgreSQL database (for example, a Neon database). PostgreSQL URLs using the standard `postgresql://` or `postgres://` scheme are automatically configured to use the included psycopg driver.

## Deploy to Vercel

This project includes a Vercel entry point in `pyproject.toml`. Vercel detects the Flask application exposed as `run:app`; static assets live in `public/` so Vercel can serve them from its CDN.

1. Push this repository to GitHub and import it into Vercel, or install the Vercel CLI and run `vercel` from the project root.
2. Create a persistent PostgreSQL project in Neon. Use Neon’s pooled connection string for `DATABASE_URL` (it includes the `-pooler` hostname and `sslmode=require`) and add it in Vercel’s project settings along with a generated, private `SECRET_KEY`. You can generate a key locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Apply both to Preview and Production environments as needed. Do not use SQLite for a deployed instance.
3. Pull the Vercel Production environment variables locally (Vercel CLI):

   ```powershell
   vercel link
   vercel env pull .env
   ```

   Keep `.env` private; it is ignored by Git. Apply migrations against the PostgreSQL database before serving the app:

   ```powershell
   flask --app run.py db upgrade
   ```

4. Deploy the project from Vercel. Vercel installs packages from `requirements.txt`. Subsequent schema changes should be migrated against the same database before or as part of the deployment process.

The app intentionally fails fast on Vercel if either `DATABASE_URL` or `SECRET_KEY` is missing rather than silently using ephemeral SQLite or an insecure development secret. Demo data is optional; if needed, run `flask --app run.py seed` with the target database configured before deploying. Change the demo passwords before making seeded accounts publicly accessible.

Initialize and apply the database migrations:

```powershell
flask --app run.py db upgrade
```

The initial migration is included in the repository. For future model changes, generate a migration with `flask --app run.py db migrate -m "Describe the change"` and apply it with `flask --app run.py db upgrade`.

Seed three demo users and 15 sample books:

```powershell
flask --app run.py seed
```

Look up and cache real covers for the current listings (new listings are looked up automatically):

```powershell
flask --app run.py refresh-covers
```

Cover metadata is stored in the local database. Cover image files are served by Open Library when displayed; unavailable images fall back to the built-in designed covers.

Demo accounts (all use password `BookSwap123!`):

- aarav@example.com
- meera@example.com
- kabir@example.com

Run the application locally:

```powershell
flask --app run.py run --debug
```

Or run directly with `python run.py` (loads `.env` automatically):

```powershell
python run.py
```

Open <http://127.0.0.1:5000>.

## Tests

```powershell
python -m pytest
```

## Exchange lifecycle

An available book can receive one pending request at a time. Creating the request marks it `Requested`. The owner may accept it, which marks the request `Accepted` and the book `Exchanged`, or decline it, returning the book to `Available`. A requester can cancel their own pending request, also returning the book to `Available`. A request for the same book by the same user cannot be duplicated while a pending request exists.

## Design decisions and future improvements

- The application factory and blueprints keep setup and feature areas separable for testing and future growth.
- SQLite is the zero-configuration local default; deployments use persistent PostgreSQL through `DATABASE_URL`.
- Requesting is limited to available books so only one active exchange request can control the book's status at a time.
- Bootstrap and a small local stylesheet provide responsive, accessible layouts without adding a frontend build pipeline.
- Future improvements could include in-app messaging between students, cover image uploads, email notifications, and exchange completion confirmation.
