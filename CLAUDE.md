# Alex & Carrie Movie App Documentation

## Overview
This is a Flask-based web application for tracking movies and TV shows watched by Alex and Carrie. It uses The Movie Database (TMDb) API for movie/TV data and allows users to log viewings with ratings, comments, and tags.

## Core Architecture

### Flask App Structure
- **Entry Point**: `main.py` - Runs the Flask development server
- **App Factory**: `app/__init__.py:create_app()` - Creates and configures the Flask application
- **Configuration**: `app/config.py` - Environment-based configuration classes
- **Extensions**: `app/extensions.py` - Initializes Flask extensions (SQLAlchemy, Login Manager, etc.)

### Database Models (`app/models.py`)
- **User**: User accounts (username, password_hash, viewings relationship)
- **Media**: Movies/TV shows cached from TMDb (tmdb_id, title, poster_path, cached_json)
- **Viewing**: Individual viewing records (user_id, media_id, rating, comment, watched_on, with_partner, rewatch)
- **Tag**: Custom tags for categorizing viewings (name, slug)
- **viewing_tags**: Many-to-many relationship table between viewings and tags

### Application Blueprints

#### Authentication (`app/auth/`)
- **Routes** (`routes.py`):
  - `/auth/login` - Login page and form handling
  - `/auth/logout` - Logout endpoint
- **Forms** (`forms.py`): LoginForm with username/password validation

#### Media Management (`app/media/`)
- **Routes** (`routes.py`):
  - `/search` - HTMX-powered search for movies/TV shows
  - `/title/<media_type>/<int:tmdb_id>` - Media detail page with both users' viewings
- **TMDb Client** (`tmdb.py`): API wrapper for The Movie Database
  - `search_movies()`, `search_tv()`, `search_multi()` - Search functions
  - `get_movie_details()`, `get_tv_details()` - Detail fetching
  - `build_image_url()` - Image URL construction
  - Rate limiting and retry logic built-in

#### Diary Management (`app/diary/`)
- **Routes** (`routes.py`):
  - `/diary/me` - Current user's personal diary with filtering/pagination
  - `/diary/together` - Shared viewings (with_partner=True)
  - `/viewing/add/<media_type>/<int:tmdb_id>` - HTMX modal for adding viewings
  - `/viewing` (POST) - Create new viewing record
  - `/tags/autocomplete` - Tag suggestions for forms
- **Forms** (`forms.py`): ViewingForm for rating, comments, dates, tags

## Key Features

### User System
- Two main users: "alex" and "carrie"
- Secure password hashing with Argon2
- Flask-Login for session management

### Movie/TV Show Management
- TMDb integration for movie/show data
- Local caching of media details in database
- Automatic data refresh (7-day cache expiry)
- Support for both movies and TV shows

### Viewing Tracking
- Personal diary entries with ratings (1-5 stars)
- Comments and custom tags
- "With partner" flag for shared viewings
- Rewatch tracking
- Date-based organization

### Search & Filtering
- Real-time search using HTMX
- Filter by year, media type, rating, tags
- Sorting by newest or highest rated
- Pagination for large result sets

## Template Structure (`app/templates/`)
- **base.html** - Main layout template
- **auth/login.html** - Login page
- **diary/list.html** - Diary listing (both personal and together)
- **media/detail.html** - Movie/TV show detail page
- **components/_add_viewing_modal.html** - HTMX modal for adding viewings
- **components/_search_results.html** - HTMX search results partial

## Development Tools
- **Linting**: ruff for code linting
- **Formatting**: black for code formatting
- **Import sorting**: isort
- **Testing**: pytest with flask plugin
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Flask-Migrate for database versioning

## Environment Variables Required
- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - PostgreSQL connection string
- `TMDB_API_KEY` - The Movie Database API key
- `FLASK_ENV` - development/production

## Common Development Commands
- Start dev server: `python main.py`
- Database migrations: `flask db migrate -m "description"`
- Apply migrations: `flask db upgrade`
- Install dependencies: `pip install -r requirements.txt`

## Key Relationships
- Users have many Viewings
- Media (movies/shows) have many Viewings
- Viewings belong to one User and one Media
- Tags have many-to-many relationship with Viewings
- TMDb data is cached locally in Media.cached_json field

## Important Implementation Notes
- All TMDb API calls go through `tmdb_client` with retry logic and rate limiting
- Search is handled via HTMX for responsive UX
- Media detail pages show viewings from both users side-by-side
- Tags are automatically created from comma-separated input
- Database uses proper foreign key constraints and cascading deletes
- Images use TMDb's CDN with configurable sizes