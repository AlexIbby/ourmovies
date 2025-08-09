import os
import click
from flask import Flask
from flask.cli import with_appcontext
from app import create_app
from app.extensions import db
from app.models import User, Media, Viewing, Tag

# Create the Flask app
app = create_app()

@app.cli.command()
@with_appcontext
def create_default_users():
    """Create default users Alex and Carrie"""
    alex = User.query.filter_by(username='alex').first()
    if not alex:
        alex = User(username='alex')
        alex.set_password('alex')
        db.session.add(alex)
        click.echo('Created user: alex')
    else:
        click.echo('User alex already exists')
    
    carrie = User.query.filter_by(username='carrie').first()
    if not carrie:
        carrie = User(username='carrie')
        carrie.set_password('carrie')
        db.session.add(carrie)
        click.echo('Created user: carrie')
    else:
        click.echo('User carrie already exists')
    
    db.session.commit()
    click.echo('Default users setup complete')

@app.cli.command()
@click.option('--username', prompt=True, help='Username for the new user')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password for the new user')
@with_appcontext
def create_user(username, password):
    """Create a new user"""
    if User.query.filter_by(username=username.lower()).first():
        click.echo(f'User {username} already exists!')
        return
    
    user = User(username=username.lower())
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f'Created user: {username}')

@app.cli.command()
@with_appcontext
def list_users():
    """List all users"""
    users = User.query.all()
    if not users:
        click.echo('No users found')
        return
    
    click.echo('Users:')
    for user in users:
        click.echo(f'  - {user.username} (ID: {user.id}, Created: {user.created_at})')

@app.cli.command()
@click.option('--username', prompt=True, help='Username to reset password for')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='New password')
@with_appcontext
def reset_password(username, password):
    """Reset a user's password"""
    user = User.query.filter_by(username=username.lower()).first()
    if not user:
        click.echo(f'User {username} not found!')
        return
    
    user.set_password(password)
    db.session.commit()
    click.echo(f'Password reset for user: {username}')

@app.cli.command()
@with_appcontext
def init_db():
    """Initialize the database"""
    db.create_all()
    click.echo('Database initialized')
    
    # Create default users if none exist
    if User.query.count() == 0:
        create_default_users.callback()

if __name__ == '__main__':
    app.run(debug=True)