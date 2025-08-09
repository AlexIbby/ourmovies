import os
from flask import Flask
from .config import config
from .extensions import init_extensions, login_manager, db  # use shared db
from .models import User, Tag

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize config (fix database URL if needed)
    config[config_name].init_app(app)
    
    # Configure the database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Removed separate db.init_app(app); init_extensions will handle it
    
    init_extensions(app)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .media import bp as media_bp
    app.register_blueprint(media_bp)
    
    from .diary import bp as diary_bp
    app.register_blueprint(diary_bp)
    
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Main routes
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('diary.my_diary'))
    
    @app.route('/health')
    def health():
        from .extensions import db
        try:
            db.session.execute('SELECT 1')
            return {'status': 'ok'}, 200
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500
    
    return app