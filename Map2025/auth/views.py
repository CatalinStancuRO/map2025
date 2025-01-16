from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from .models import User, users
from .forms import LoginForm, RegistrationForm

auth = Blueprint('auth', __name__)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)  # Retrieve user from mock database

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        for user in users.values():
            if user.email == form.email.data and user.check_password(form.password.data):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.email.data in [u.email for u in users.values()]:
            flash('Email already registered', 'danger')
        else:
            user_id = len(users) + 1
            new_user = User(user_id, form.email.data, form.password.data)
            users[user_id] = new_user
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('auth.login'))
