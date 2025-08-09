from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required
from . import bp
from .tmdb import tmdb_client
from ..models import Media, Viewing, User
from ..extensions import db
from datetime import datetime

@bp.route('/search')
@login_required
def search():
    """Search endpoint for HTMX requests"""
    query = request.args.get('q', '').strip()
    media_type = request.args.get('type', 'multi')
    page = int(request.args.get('page', 1))
    
    if not query:
        return render_template('components/_search_results.html', results=[], query=query)
    
    try:
        if media_type == 'movie':
            response = tmdb_client.search_movies(query, page)
        elif media_type == 'tv':
            response = tmdb_client.search_tv(query, page)
        else:
            response = tmdb_client.search_multi(query, page)
        
        if response and 'results' in response:
            # Add image URLs to results
            for result in response['results']:
                result['poster_url'] = tmdb_client.build_image_url(result.get('poster_path'), 'w342')
                # Handle different date fields
                if 'release_date' in result:
                    result['year'] = result['release_date'][:4] if result['release_date'] else None
                elif 'first_air_date' in result:
                    result['year'] = result['first_air_date'][:4] if result['first_air_date'] else None
                
                # Normalize title field
                if 'name' in result and 'title' not in result:
                    result['title'] = result['name']
        
            return render_template('components/_search_results.html', 
                                 results=response['results'], 
                                 query=query,
                                 page=page,
                                 total_pages=response.get('total_pages', 1))
        
    except Exception as e:
        current_app.logger.error(f"Search error: {e}")
    
    return render_template('components/_search_results.html', 
                         results=[], 
                         query=query, 
                         error="Search failed. Please try again.")

@bp.route('/title/<media_type>/<int:tmdb_id>')
@login_required
def title_detail(media_type, tmdb_id):
    """Show title detail page"""
    # Get or create media record
    media = Media.query.filter_by(tmdb_id=tmdb_id, media_type=media_type).first()
    
    if not media:
        # Fetch from TMDb and create record
        if media_type == 'movie':
            details = tmdb_client.get_movie_details(tmdb_id)
        elif media_type == 'tv':
            details = tmdb_client.get_tv_details(tmdb_id)
        else:
            return "Invalid media type", 400
        
        if not details:
            return "Media not found", 404
        
        # Create media record
        media = Media(
            tmdb_id=tmdb_id,
            media_type=media_type,
            title=details.get('title') or details.get('name'),
            release_year=None,
            poster_path=details.get('poster_path'),
            backdrop_path=details.get('backdrop_path'),
            cached_json=details
        )
        
        # Extract year
        if 'release_date' in details and details['release_date']:
            media.release_year = int(details['release_date'][:4])
        elif 'first_air_date' in details and details['first_air_date']:
            media.release_year = int(details['first_air_date'][:4])
        
        db.session.add(media)
        db.session.commit()
    else:
        # Check if cached data is stale (older than 7 days)
        if (not media.cached_json or 
            (media.updated_at and 
             (datetime.utcnow() - media.updated_at).days > 7)):
            
            if media_type == 'movie':
                details = tmdb_client.get_movie_details(tmdb_id)
            else:
                details = tmdb_client.get_tv_details(tmdb_id)
            
            if details:
                media.cached_json = details
                media.updated_at = datetime.utcnow()
                db.session.commit()
    
    # Get viewings from both users (including shared viewings)
    alex = User.query.filter_by(username='alex').first()
    carrie = User.query.filter_by(username='carrie').first()
    
    alex_viewing = None
    carrie_viewing = None
    
    if alex:
        alex_viewing = Viewing.query.filter(
            Viewing.user_id == alex.id,
            Viewing.media_id == media.id
        ).order_by(Viewing.watched_on.desc()).first()
    
    if carrie:
        carrie_viewing = Viewing.query.filter(
            Viewing.user_id == carrie.id,
            Viewing.media_id == media.id
        ).order_by(Viewing.watched_on.desc()).first()
    
    # Shared diary fallback: if a user has no personal viewing, show the latest viewing for this title by anyone
    latest_any_viewing = Viewing.query.filter(
        Viewing.media_id == media.id
    ).order_by(Viewing.watched_on.desc()).first()
    if latest_any_viewing is not None:
        if alex and alex_viewing is None:
            alex_viewing = latest_any_viewing
        if carrie and carrie_viewing is None:
            carrie_viewing = latest_any_viewing
    
    # Build image URLs
    poster_url = tmdb_client.build_image_url(media.poster_path, 'w500')
    backdrop_url = tmdb_client.build_image_url(media.backdrop_path, 'w1280')
    
    return render_template('media/detail.html', 
                         media=media,
                         alex_viewing=alex_viewing,
                         carrie_viewing=carrie_viewing,
                         poster_url=poster_url,
                         backdrop_url=backdrop_url)
