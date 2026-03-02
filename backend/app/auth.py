"""Authentication blueprint for Spendly"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required
from . import db
from .models import User
import re

bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')


def valid_password(pw: str) -> bool:
    """Check password strength: min 8 chars, at least 1 digit and 1 special."""
    if len(pw) < 8:
        return False
    if not re.search(r"\d", pw):
        return False
    if not re.search(r"[^A-Za-z0-9]", pw):
        return False
    return True


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')

    # Basic validation
    if not username or not email or not password:
        flash('Please fill all required fields', 'danger')
        return redirect(url_for('auth.register'))
    if password != confirm:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('auth.register'))
    if not valid_password(password):
        flash('Password must be at least 8 characters, include a number and a special character', 'danger')
        return redirect(url_for('auth.register'))

    # Unique checks
    existing = User.query.filter((User.email == email) | (User.username == username)).first()
    if existing:
        flash('Username or email already exists', 'danger')
        return redirect(url_for('auth.register'))

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Auto login
    login_user(user)
    flash('Welcome to Spendly!', 'success')
    return redirect(url_for('main.dashboard_view'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')

    identifier = request.form.get('identifier', '').strip()
    password = request.form.get('password', '')
    remember = bool(request.form.get('remember_me'))

    if not identifier or not password:
        flash('Please provide username/email and password', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter((User.email == identifier.lower()) | (User.username == identifier)).first()
    if user is None or not user.check_password(password):
        flash('Invalid credentials', 'danger')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)
    flash('Logged in successfully', 'success')
    return redirect(url_for('main.dashboard_view'))


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('auth.login'))
