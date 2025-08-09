from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc
from . import bp
from .forms import ViewingForm
from ..models import Media, Viewing, Tag, User, viewing_tags
from ..extensions import db
from ..media.tmdb import tmdb_client
from datetime import datetime, date

@bp.route('/diary/me')
@login_required
def my_diary():
    """Show shared diary (all viewings from both users)"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get distinct media IDs to build the diary around unique movies/shows
    media_query = db.session.query(Media.id).join(Viewing)
    
    # Filter by year
    year_filter = request.args.get('year', type=int)
    if year_filter:
        media_query = media_query.filter(db.extract('year', Viewing.watched_on) == year_filter)
    
    # Filter by media type
    media_type_filter = request.args.get('media_type')
    if media_type_filter in ['movie', 'tv']:
        media_query = media_query.filter(Media.media_type == media_type_filter)
    
    # Filter by rating
    rating_filter = request.args.get('rating', type=int)
    if rating_filter and 1 <= rating_filter <= 5:
        media_query = media_query.filter(Viewing.rating >= rating_filter)
    
    # Filter by tags
    tag_filter = request.args.getlist('tags')
    if tag_filter:
        media_query = media_query.join(viewing_tags).join(Tag).filter(Tag.name.in_(tag_filter))
    
    # Get unique media IDs
    media_ids_subquery = media_query.distinct().subquery()
    
    # Get media records with their latest viewing for ordering
    media_query = db.session.query(Media)\
                           .join(media_ids_subquery, Media.id == media_ids_subquery.c.id)\
                           .join(Viewing)\
                           .group_by(Media.id)
    
    # Sort
    sort_by = request.args.get('sort', 'newest')
    if sort_by == 'highest_rated':
        media_query = media_query.order_by(desc(db.func.max(Viewing.rating)), desc(db.func.max(Viewing.watched_on)))
    else:  # newest
        media_query = media_query.order_by(desc(db.func.max(Viewing.watched_on)))
    
    media_pagination = media_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get both users' viewings for each media item
    alex_user = User.query.filter_by(username='alex').first()
    carrie_user = User.query.filter_by(username='carrie').first()
    
    media_items = []
    for media in media_pagination.items:
        alex_viewing = None
        carrie_viewing = None
        latest_viewing = None
        
        if alex_user:
            alex_viewing = Viewing.query.filter(
                Viewing.user_id == alex_user.id,
                Viewing.media_id == media.id
            ).order_by(Viewing.watched_on.desc()).first()
        
        if carrie_user:
            carrie_viewing = Viewing.query.filter(
                Viewing.user_id == carrie_user.id,
                Viewing.media_id == media.id
            ).order_by(Viewing.watched_on.desc()).first()
        
        # Get the latest viewing overall for date display
        latest_viewing = Viewing.query.filter(
            Viewing.media_id == media.id
        ).order_by(Viewing.watched_on.desc()).first()
        
        media_items.append({
            'media': media,
            'alex_viewing': alex_viewing,
            'carrie_viewing': carrie_viewing,
            'latest_viewing': latest_viewing
        })
    
    # Create a pagination-like object for the template
    class MediaPagination:
        def __init__(self, items, pagination):
            self.items = items
            self.page = pagination.page
            self.pages = pagination.pages
            self.has_prev = pagination.has_prev
            self.has_next = pagination.has_next
            self.prev_num = pagination.prev_num
            self.next_num = pagination.next_num
            
        def iter_pages(self):
            return range(1, self.pages + 1)
    
    media_viewings = MediaPagination(media_items, media_pagination)
    
    # Get available years and tags for filters
    years = db.session.query(db.extract('year', Viewing.watched_on).label('year'))\
                     .distinct()\
                     .order_by(desc('year')).all()
    
    user_tags = db.session.query(Tag)\
                          .join(viewing_tags)\
                          .join(Viewing)\
                          .distinct().all()
    
    return render_template('diary/list.html', 
                         viewings=media_viewings, 
                         years=[y[0] for y in years],
                         tags=user_tags,
                         current_filters={
                             'year': year_filter,
                             'media_type': media_type_filter,
                             'rating': rating_filter,
                             'tags': tag_filter,
                             'sort': sort_by
                         },
                         page_title="Our Diary")

@bp.route('/diary/together')
@login_required
def together_diary():
    """Redirect to shared diary since everything is shared now"""
    return redirect(url_for('diary.my_diary', **request.args))

@bp.route('/viewing/add/<media_type>/<int:tmdb_id>')
@login_required
def add_viewing_modal(media_type, tmdb_id):
    """Show add viewing modal (HTMX partial)"""
    # Get or create media record
    media = Media.query.filter_by(tmdb_id=tmdb_id, media_type=media_type).first()
    
    if not media:
        # Fetch from TMDb
        if media_type == 'movie':
            details = tmdb_client.get_movie_details(tmdb_id)
        elif media_type == 'tv':
            details = tmdb_client.get_tv_details(tmdb_id)
        else:
            return "Invalid media type", 400
        
        if not details:
            return "Media not found", 404
        
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
    
    form = ViewingForm()
    form.tmdb_id.data = tmdb_id
    form.media_type.data = media_type
    
    poster_url = tmdb_client.build_image_url(media.poster_path, 'w342')
    
    return render_template('components/_add_viewing_modal.html', 
                         form=form, 
                         media=media,
                         poster_url=poster_url)

@bp.route('/viewing', methods=['POST'])
@login_required
def create_viewing():
    """Create a new viewing"""
    form = ViewingForm()
    
    if form.validate_on_submit():
        # Get or create media
        media = Media.query.filter_by(
            tmdb_id=form.tmdb_id.data,
            media_type=form.media_type.data
        ).first()
        
        if not media:
            flash('Media not found', 'error')
            return redirect(url_for('diary.my_diary'))
        
        # Create viewing
        viewing = Viewing(
            user_id=current_user.id,
            media_id=media.id,
            rating=form.rating.data,
            comment=form.comment.data,
            watched_on=form.watched_on.data,
            with_partner=True,  # Always True since this is a shared diary
            rewatch=form.rewatch.data
        )
        
        db.session.add(viewing)
        db.session.flush()  # Get viewing ID
        
        # Handle tags
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name.lower()).first()
                if not tag:
                    tag = Tag(
                        name=tag_name.lower(),
                        slug=Tag.create_slug(tag_name)
                    )
                    db.session.add(tag)
                    db.session.flush()
                viewing.tags.append(tag)
        
        db.session.commit()
        flash(f'Added viewing for {media.title}!', 'success')
        
        # If HTMX request, return a response that triggers modal close and page refresh
        if request.headers.get('HX-Request'):
            from flask import make_response
            response = make_response('')
            response.headers['HX-Trigger'] = 'viewing-added'
            return response
        
        return redirect(url_for('diary.my_diary'))
    
    # Form validation failed - if this is an HTMX request, re-render the modal with errors
    if request.headers.get('HX-Request'):
        # Get the media record for re-rendering the modal
        media = Media.query.filter_by(
            tmdb_id=form.tmdb_id.data,
            media_type=form.media_type.data
        ).first()
        
        if media:
            from ..media.tmdb import tmdb_client
            poster_url = tmdb_client.build_image_url(media.poster_path, 'w342')
            return render_template('components/_add_viewing_modal.html', 
                                 form=form, 
                                 media=media,
                                 poster_url=poster_url)
    
    # Non-HTMX request - flash errors and redirect
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('diary.my_diary'))

@bp.route('/viewing/edit/<int:viewing_id>')
@login_required
def edit_viewing_modal(viewing_id):
    """Show edit viewing modal (HTMX partial)"""
    viewing = Viewing.query.get_or_404(viewing_id)
    
    # Check if user owns this viewing
    if viewing.user_id != current_user.id:
        return "Unauthorized", 403
    
    media = viewing.media
    form = ViewingForm()
    
    # Pre-populate form with existing data
    form.tmdb_id.data = media.tmdb_id
    form.media_type.data = media.media_type
    form.rating.data = viewing.rating
    form.comment.data = viewing.comment
    form.watched_on.data = viewing.watched_on
    # with_partner removed; shared diary by default
    form.rewatch.data = viewing.rewatch
    form.tags.data = ', '.join([tag.name for tag in viewing.tags])
    
    poster_url = tmdb_client.build_image_url(media.poster_path, 'w342')
    
    return render_template('components/_edit_viewing_modal.html', 
                         form=form, 
                         media=media,
                         viewing=viewing,
                         poster_url=poster_url)

@bp.route('/viewing/<int:viewing_id>', methods=['PUT'])
@login_required
def update_viewing(viewing_id):
    """Update an existing viewing"""
    viewing = Viewing.query.get_or_404(viewing_id)
    
    # Check if user owns this viewing
    if viewing.user_id != current_user.id:
        return "Unauthorized", 403
    
    form = ViewingForm()
    
    if form.validate_on_submit():
        # Update viewing
        viewing.rating = form.rating.data
        viewing.comment = form.comment.data
        viewing.watched_on = form.watched_on.data
        viewing.with_partner = True  # Always True since this is a shared diary
        viewing.rewatch = form.rewatch.data
        
        # Clear existing tags
        viewing.tags.clear()
        
        # Handle new tags
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name.lower()).first()
                if not tag:
                    tag = Tag(
                        name=tag_name.lower(),
                        slug=Tag.create_slug(tag_name)
                    )
                    db.session.add(tag)
                    db.session.flush()
                viewing.tags.append(tag)
        
        db.session.commit()
        flash(f'Updated viewing for {viewing.media.title}!', 'success')
        
        # If HTMX request, return a response that triggers modal close and page refresh
        if request.headers.get('HX-Request'):
            from flask import make_response
            response = make_response('')
            response.headers['HX-Trigger'] = 'viewing-updated'
            return response
        
        return redirect(url_for('diary.my_diary'))
    
    # Form validation failed
    if request.headers.get('HX-Request'):
        media = viewing.media
        poster_url = tmdb_client.build_image_url(media.poster_path, 'w342')
        return render_template('components/_edit_viewing_modal.html', 
                             form=form, 
                             media=media,
                             viewing=viewing,
                             poster_url=poster_url)
    
    # Non-HTMX request - flash errors and redirect
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('diary.my_diary'))

@bp.route('/tags/autocomplete')
@login_required
def tags_autocomplete():
    """Get tag suggestions for autocomplete"""
    q = request.args.get('q', '').strip().lower()
    
    if not q:
        return jsonify([])
    
    tags = Tag.query.filter(Tag.name.ilike(f'%{q}%')).limit(10).all()
    suggestions = [{'name': tag.name, 'slug': tag.slug} for tag in tags]
    
    return jsonify(suggestions)
