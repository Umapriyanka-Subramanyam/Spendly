"""Spendly Routes - Main Blueprint"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from .models import Expense, ExpenseSplit, EXPENSE_CATEGORIES
from .utils import format_currency
from . import db

bp = Blueprint('main', __name__)

def get_greeting():
    """Get time-based greeting message."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 18:
        return "Good Afternoon"
    else:
        return "Good Evening"

def get_dashboard_stats(user):
    """Calculate dashboard statistics for user."""
    from decimal import Decimal
    
    # Get user's expenses
    expenses = Expense.query.filter_by(user_id=user.id).all()
    
    # Total spent (all expenses user created)
    total_spent = Decimal(str(sum(e.amount for e in expenses)))
    
    # Get user's primary member (first member, or create if doesn't exist)
    primary_member = user.members[0] if user.members else None
    
    # Your share (splits assigned to user)
    your_share = Decimal('0')
    you_owe = Decimal('0')
    
    if primary_member:
        user_splits = ExpenseSplit.query.filter_by(member_id=primary_member.id).all()
        your_share = Decimal(str(sum(s.share_amount for s in user_splits if not s.is_settled)))
        you_owe = Decimal(str(sum(s.share_amount for s in user_splits if not s.is_settled and s.share_amount > 0)))
    
    # You're owed (expenses you paid for others)
    you_owed = Decimal(str(total_spent - your_share)) if total_spent > your_share else Decimal('0')
    
    # Format currency using utils (₹)
    def fmt_currency(val):
        try:
            return format_currency(float(val))
        except Exception:
            return format_currency(0)
    
    # Top categories
    category_counts = {}
    for expense in expenses:
        category_counts[expense.category] = category_counts.get(expense.category, 0) + 1
    top_categories = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])
    
    # Recent expenses
    recent_expenses = []
    for expense in sorted(expenses, key=lambda x: x.created_at, reverse=True)[:10]:
        recent_expenses.append({
            'description': expense.description,
            'amount': fmt_currency(Decimal(str(expense.amount))),
            'category': expense.category,
            'date': expense.created_at.strftime('%b %d, %Y')
        })
    
    return {
        'total_spent': fmt_currency(total_spent),
        'your_share': fmt_currency(your_share),
        'you_owe': fmt_currency(you_owe),
        'you_owed': fmt_currency(you_owed),
        'top_categories': top_categories,
        'recent_expenses': recent_expenses
    }

@bp.route('/')
def index():
    """Home page - redirect based on auth status."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.dashboard_view'))

@bp.route('/dashboard')
@login_required
def dashboard_view():
    """Dashboard home page."""
    stats = get_dashboard_stats(current_user)
    greeting = get_greeting()
    return render_template('dashboard.html', stats=stats, greeting=greeting, username=current_user.username)

@bp.route('/expenses')
@login_required
def expenses():
    """Expenses management page."""
    return render_template('expenses.html')

@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    members = current_user.members if hasattr(current_user, 'members') else []
    return render_template('profile.html', user=current_user, members=members)

@bp.route('/api/summary')
def api_summary():
    """API endpoint for expense summary."""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        
        stats = get_dashboard_stats(current_user)
        return jsonify({
            'highest_spender': 'You',
            'most_common_category': list(stats['top_categories'].keys())[0] if stats['top_categories'] else 'N/A',
            'avg_share': float(stats['your_share'].replace('$', '').replace(',', ''))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return render_template('500.html'), 500
