from app import create_app
import os
from app.extensions import db  # changed import
from app.models import Tag

app = create_app()

with app.app_context():
    db.create_all()
    if Tag.query.count() == 0:
        tags = ['funny', 'action', 'drama', 'sci-fi', 'horror', 'romance', 'thriller']
        for t in tags:
            db.session.add(Tag(name=t))
        db.session.commit()


if app.debug:
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # ensure static (JS/CSS) not cached
    @app.after_request
    def _no_cache(response):
        # Prevent caching so updated JS/CSS for modal behavior always load
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
