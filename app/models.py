from datetime import datetime, date
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Index, func
from passlib.hash import argon2
from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    viewings = db.relationship('Viewing', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = argon2.hash(password)
    
    def check_password(self, password):
        return argon2.verify(password, self.password_hash)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Media(db.Model):
    __tablename__ = 'media'
    
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    media_type = db.Column(db.Enum('movie', 'tv', name='media_type_enum'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    release_year = db.Column(db.Integer, nullable=True)
    poster_path = db.Column(db.Text, nullable=True)
    backdrop_path = db.Column(db.Text, nullable=True)
    cached_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    viewings = db.relationship('Viewing', backref='media', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('ix_media_type_title', 'media_type', 'title'),
    )
    
    def __repr__(self):
        return f'<Media {self.title} ({self.media_type})>'

class Viewing(db.Model):
    __tablename__ = 'viewings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    watched_on = db.Column(db.Date, nullable=False, default=date.today)
    with_partner = db.Column(db.Boolean, nullable=False, default=True)  # Temporary - to be removed in migration
    rewatch = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tags = db.relationship('Tag', secondary='viewing_tags', backref='viewings')
    
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        Index('ix_user_watched_on', 'user_id', 'watched_on'),
    )
    
    def __repr__(self):
        return f'<Viewing {self.media.title} by {self.user.username}>'

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    slug = db.Column(db.Text, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def create_slug(name):
        import re
        return re.sub(r'[^\w\s-]', '', name.lower().strip()).replace(' ', '-')
    
    def __repr__(self):
        return f'<Tag {self.name}>'

# Many-to-many relationship table
viewing_tags = db.Table('viewing_tags',
    db.Column('viewing_id', db.Integer, db.ForeignKey('viewings.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)