# Two-Person Letterboxd-Style App — Requirements (Flask, Railway)

> Private, mobile-first diary for two users to log movies/TV with 1–5 star ratings and tags like “memorable,” powered by TMDb search.

---

## 1) Goal & Scope

- Build a private, mobile-first web app for **two specific users** (me and my partner) to log and review what we’ve watched.
- Search titles via a **free movie/TV database** (**TMDb**).
- Each viewing includes:
  - **Star rating: integer 1–5 only** (no halves, no 0).
  - **Free-form tags** (e.g., “memorable”) with autocomplete and create-new.
  - Optional comment and watched date.
- Views: individual diaries, “together” view, title detail, poster grid, search.
- Deploy to **Railway** with managed Postgres (optional Redis for caching).

## 2) Tech Stack & Conventions

- **Backend:** Python 3.11+, Flask app factory, Blueprints.
- **Templates/UX:** Jinja2 + **HTMX** (AJAX partials, modals, infinite scroll).
- **Styling:** **Tailwind CSS** (dark theme by default, poster-forward aesthetic).
- **Auth:** Flask-Login; passlib (argon2id or bcrypt).
- **DB:** Postgres + SQLAlchemy; Alembic/Flask-Migrate.
- **Caching:** No Redis. Optional in-memory LRU (per-process) and/or DB-backed caching via `media.cached_json`.
- **HTTP client:** `requests` with timeouts & retry/backoff.
- **Serving:** Gunicorn.
- **Lint/Format:** ruff + black + isort; pre-commit.
- **Testing:** pytest (unit + integration).
- **Compliance:** TMDb attribution required.

## 3) Environment & Deployment (Railway)

- Env vars:
  - `SECRET_KEY`, `DATABASE_URL`, `TMDB_API_KEY`, `FLASK_ENV=production`
- **Procfile:** `web: gunicorn "app:create_app()"`
- **Railway.toml:** startCommand, healthcheck `/health`, NIXPACKS builder.
- **Migrations:** run `flask db upgrade` on deploy.
- **User seeding:** On first startup, if `users` is empty, auto-create two accounts:
  - Username: `alex`, Password: `alex`
  - Username: `carrie`, Password: `carrie` Passwords are stored **hashed**; changing passwords is optional and out of scope for MVP.
- **No public signup**; only these two accounts exist.

## 4) Data Model (Postgres)

### `users`

- `id` PK
- `username` TEXT UNIQUE (case-insensitive preferred)
- `password_hash` TEXT
- `created_at` TIMESTAMP (UTC) default now

### `media`

Represents a movie **or** TV series.

- `id` PK
- `tmdb_id` INT UNIQUE NOT NULL
- `media_type` ENUM('movie','tv') NOT NULL
- `title` TEXT NOT NULL
- `release_year` INT NULL
- `poster_path` TEXT NULL
- `backdrop_path` TEXT NULL
- `cached_json` JSONB NULL (details/credits snapshot)
- `created_at`, `updated_at` TIMESTAMP
- Indexes: (`media_type`,`title`), (`tmdb_id`)

### `viewings`

One diary entry per user per watch.

- `id` PK
- `user_id` FK → `users.id` (ON DELETE CASCADE)
- `media_id` FK → `media.id` (ON DELETE CASCADE)
- `rating` SMALLINT NOT NULL CHECK 1≤rating≤5
- `comment` TEXT NULL
- `watched_on` DATE NOT NULL (default today in app)
- `with_partner` BOOL NOT NULL DEFAULT TRUE
- `rewatch` BOOL NOT NULL DEFAULT FALSE
- `created_at`, `updated_at` TIMESTAMP
- Index: (`user_id`, `watched_on` DESC)

### `tags`

Canonical tag catalog (shared).

- `id` PK
- `name` CITEXT UNIQUE (trimmed, 1–30 chars)
- `slug` TEXT UNIQUE (derived)
- `created_at` TIMESTAMP

### `viewing_tags` (many-to-many)

- `viewing_id` FK → `viewings.id` (ON DELETE CASCADE)
- `tag_id` FK → `tags.id` (ON DELETE CASCADE)
- Composite PK (`viewing_id`,`tag_id`)

## 5) Core User Stories (Must-Have)

1. **Login/Logout**\
   Exactly **two accounts** exist: **Alex** and **Carrie**.

   - Usernames: `alex`, `carrie` (store canonical lowercase; case-insensitive login acceptable).
   - **Default passwords:** `alex` and `carrie`. Store passwords **hashed** even if they are simple.
   - On first run, if no users exist, seed both accounts automatically. No signup/reset flows needed for MVP.
   - Session-based auth via Flask-Login; CSRF on POSTs.

2. **Search Titles (TMDb)**\
   Typeahead search for **movies and TV**. Results show poster, title, year, media type. Pagination / infinite scroll.

3. **Add Viewing**\
   Modal shows poster & synopsis. Inputs: **rating (1–5)**, tags (chips with autocomplete + create), optional comment, date (default today), `with_partner` (default ON). On save: insert `media` (if needed), create `viewing`, link tags. Success toast + link.

4. **Edit/Delete Viewing**\
   Users can edit/remove **their own** entries, including tags and rating.

5. **My Diary**\
   Reverse-chron list with poster tiles. Filters: year, media type, rating (1–5), tags (multi-select). Sort: newest, highest rated.

6. **Together View**\
   Shows entries where `with_partner = TRUE` from either user. (v2: intersection by same title/date.)

7. **Title Detail Page**\
   Hero backdrop + poster, synopsis, cast (from cache). Show **both users’ most recent** ratings/comments for this title. CTA to add/update viewing.

8. **Tags UX**\
   Autocomplete from global `tags` (case-insensitive). Creating a new tag inserts into `tags` if not exists. Chips UI: add/remove inline; keyboard accessible.

9. **Attribution**\
   Footer: “This product uses the TMDb API but is not endorsed or certified by TMDb.” Include TMDb logo.

## 6) Non-Functional Requirements

- **Mobile-first:** 360–768px optimized; touch targets ≥44px; sticky bottom nav.
- **Performance:** TTI < 2s on mid-range mobile; search response < 500ms (with cache).
- **Accessibility:** WCAG AA; keyboard navigable; star rating via radio group; labeled form fields & errors.
- **Security:** HttpOnly/Secure cookies; SameSite=Lax; CSRF on POSTs; strong password hashing; input validation & sanitization.
- **Reliability:** Graceful fallback if TMDb fails (clear error + retry).
- **Logging:** JSON logs at INFO; include request ID; log TMDb errors/rate limits.

## 7) TMDb Integration

- Fetch `/configuration` for image base URLs; cache 24h (in-memory per process).
- Search: `/search/movie`, `/search/tv` (query, page).
- Details: `/movie/{id}` or `/tv/{id}` (optionally append `credits`).
- Use TMDb CDN URLs for images (do not proxy/download); honor rate limits; implement backoff on 429.
- **Cache policy (no Redis):**
  - Keep `/configuration` in-process for 24h.
  - Optionally persist details to `media.cached_json` with `updated_at`; refresh if stale (>7d) or on-demand.
  - Search responses may be returned live or cached in-process with a simple LRU/TTL (\~2h) per process.

## 8) HTTP Routes

- `GET /` → redirect to `/diary/me`
- `GET /login` + `POST /login` (CSRF), `POST /logout`
- `GET /search?type=(movie|tv)&q=…&page=…` → partial HTML list (HTMX)
- `GET /title/<media_type>/<tmdb_id>` → detail (ensure `media` row exists; fetch/cache details)
- `GET /viewing/add/<media_type>/<tmdb_id>` → modal (partial)
- `POST /viewing` → create (fields: `tmdb_id`, `media_type`, `rating` 1–5, `tags[]`, `comment`, `watched_on`, `with_partner`)
- `GET /viewing/<id>/edit` → modal (partial)
- `POST /viewing/<id>` → update
- `POST /viewing/<id>/delete` → delete (confirm)
- `GET /diary/me` → list with filters (supports HTMX infinite scroll)
- `GET /diary/together` → list with filters
- `GET /tags/autocomplete?q=…` → JSON suggestions
- `GET /health` → 200 OK

## 9) Templates & Components

- **Layout:** `base.html` (Tailwind, dark theme, sticky bottom nav: Search | Diary | Together | Profile)
- **Partials:** `_search_bar.html`, `_result_card.html`, `_add_viewing_modal.html`, `_viewing_card.html`, `_filters_bar.html`, `_pagination_infinite.html`, `_star_input.html` (1–5 radios), `_tag_input.html` (chips + autocomplete)
- **Pages:** `auth/login.html`, `diary/list.html` (me/together variants), `media/detail.html`

## 10) Visual Design Requirements

- **Aesthetic:** Minimal, Shadcn/ui-inspired. Clean surfaces, subtle borders, soft shadows, rounded corners (lg–2xl).
- **Fonts (Google Fonts):** Use high-quality, free fonts. Preferred stacks:
  - Primary UI: **Inter** or **Plus Jakarta Sans**.
  - Alternative: **DM Sans**. Include system fallbacks.
  - Load via `<link>` from Google Fonts; font-display: swap.
- **Color modes:** Support **dark and light** modes; default to **system preference** with a toggle in the profile/menu.
- **Color palette:** Neutral grays with a single accent; ensure WCAG AA contrast. Use Tailwind tokens (e.g., slate/neutral).
- **Poster-forward layout:** `w342` posters in grids, `w500` on detail; maintain consistent aspect ratios.
- **Motion:** Fast, subtle transitions (<100ms perceived) for modals and hover/focus.
- **Loading/empty states:** Skeleton loaders for grids; friendly empty states ("Search something you watched!").

## 11) Business Rules

- **Two-user model:** Only two users exist: usernames `alex` and `carrie`. Default passwords equal usernames; passwords stored hashed. No signup, invite, or password reset in MVP.
- Rating is **required** and must be integer **1–5**.
- Tags are optional; normalize by trimming & lowercasing for uniqueness; display in Title Case.
- Users can only edit/delete **their own** viewings.
- “Together” view: any viewing with `with_partner = TRUE` (MVP rule).
- Comment max 1,000 chars; render safely (escape HTML).
- Create a `media` row on first interaction (log or detail fetch).

## 12) Security & Privacy

- This is a private app for two people; **basic security** is sufficient.
- Use HTTPS; set `SESSION_COOKIE_SECURE=True`; CSRF on POSTs.
- Store passwords **hashed** (argon2id or bcrypt) even if defaults are simple.
- Minimal brute-force mitigation optional (e.g., small sleep on failed login); no full lockout required.
- Validate/sanitize all inputs.

## 13) CLI Utilities

- `flask create-default-users` → creates `alex`/`carrie` with default passwords if they do not exist.
- `flask create-user --username <name>` → password prompt (≥4 chars acceptable for this private app).
- `flask list-users`
- `flask reset-password --username <name>`

## 14) Tests (Representative)

- **Auth:** default users are seeded on first run; valid login for `alex`/`carrie`; logout clears session.
- **Search:** returns results; optional in-memory cache exercised if enabled.
- **Add viewing:** validates required fields; rating 1–5 enforced; tags stored & deduped.
- **Edit/Delete:** only owner can mutate.
- **Filters:** rating filter 4–5; tag filter “memorable”.
- **Together view:** shows `with_partner=TRUE` entries.
- **Title page:** shows both users’ latest ratings/comments.
- **Accessibility:** star input keyboard/ARIA; labels present.

## 15) Deliverables

```
app/
  __init__.py
  config.py
  extensions.py
  models.py
  auth/ (bp)
    routes.py, forms.py
  media/ (bp)
    routes.py, tmdb.py
  diary/ (bp)
    routes.py, forms.py
  templates/ (... as above)
  static/
    css/ (Tailwind build)
    js/ (htmx + helpers)
migrations/
manage.py                # exposes CLI + create_app()
pyproject.toml
Procfile
Railway.toml
README.md                # setup, env vars, run, deploy
.pre-commit-config.yaml
```

## 16) Implementation Notes (for an LLM)

- Use **HTMX** for search, modals, infinite scroll; generate partial templates.
- **Star rating**: ARIA-friendly radio group (1–5), keyboard accessible.
- **Tags**: chip input; Enter/Comma to commit; `/tags/autocomplete` for suggestions.
- Mirror client hints with **server-side validation**.
- Build image URLs using TMDb `/configuration` response; include attribution text + logo in footer.
- Use **app factory** + Blueprints; avoid global state.
- `/health` should check DB only.

---

## 17) Open Questions / To Decide

- Should “Together” eventually require both users to log the **same title and date**, or keep the simple `with_partner` boolean?
- TV: log at **series** level only (MVP) or add episode-level logging later?
- Do we want a **PWA** (installable, offline queue for adds)?
- Should tags be **shared** across both users (current) or per-user variants?

## 18) Future Enhancements (Nice-to-Have)

- Stats: top genres/directors, streaks, avg rating by year (small charts).
- Rewatches counter; favorites list.
- “To Watch” local list.
- CSV export/import for backup.
- Shareable image cards (poster grid + rating).

## 19) Changelog

- **v1.0** — Initial spec with **integer 1–5 star ratings** and **free-form tags**.

