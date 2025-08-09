from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from . import bp
from .forms import LoginForm
from ..models import User
from ..extensions import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('diary.my_diary'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('diary.my_diary'))
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('auth.login'))