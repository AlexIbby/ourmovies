from flask import Blueprint, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db  # changed import
from app.models import Review

main = Blueprint('main', __name__)
bp = main  # alias so @bp.route works; or rename decorators to @main.route and remove this line.

VALID_TAGS = [
    "Banger Soundtrack!", "Character Study", "Classic", "Date Night",
    "Deep", "Easy Watch", "Feel-Good", "Hidden Gem", "I May Have Cried",
    "Not For Kids", "Slow-Burn", "True Story", "Twist!", "Unique!", 
    "Visual Feast"
]

@bp.route('/movie/<int:movie_id>/rate', methods=['POST'])
@login_required
def update_rating(movie_id):
    rating = request.json.get('rating')
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'Invalid rating'}), 400
    
    review = Review.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if review:
        review.rating = rating
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Review not found'}), 404

@bp.route('/movie/<int:movie_id>/review', methods=['POST'])
@login_required
def create_review(movie_id):
    # ...existing code...
    tags = request.form.getlist('tags')
    # Validate tags
    for tag in tags:
        if tag not in VALID_TAGS:
            flash('Invalid tag selected')
            return redirect(url_for('main.movie', movie_id=movie_id))
    # ...existing code...