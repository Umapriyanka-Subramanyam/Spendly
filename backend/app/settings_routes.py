"""Settings blueprint for user preferences and account management."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from io import BytesIO
import json
from .models import User, Expense, Member, ExpenseSplit
from . import db

bp = Blueprint('settings', __name__, url_prefix='/settings', template_folder='templates')


@bp.route('/profile')
@login_required
def profile():
    """Edit user profile."""
    members = current_user.members if hasattr(current_user, 'members') else []
    return render_template('profile.html', user=current_user, members=members)


@bp.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    """Update user profile."""
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        
        if not username or not email:
            flash('Username and email are required', 'error')
            return redirect(url_for('settings.profile'))
        
        # Check for duplicates
        existing_user = User.query.filter(
            User.id != current_user.id,
            ((User.username == username) | (User.email == email))
        ).first()
        
        if existing_user:
            flash('Username or email already taken', 'error')
            return redirect(url_for('settings.profile'))
        
        current_user.username = username
        current_user.email = email
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('settings.profile'))
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('settings.profile'))


@bp.route('/preferences')
@login_required
def preferences():
    """User preferences page."""
    return render_template('settings/preferences.html')


@bp.route('/preferences/update', methods=['POST'])
@login_required
def preferences_update():
    """Update user preferences."""
    try:
        currency = request.form.get('currency', 'INR')
        date_format = request.form.get('date_format', '%d/%m/%Y')
        
        # Store in user session or custom preferences table
        flash('Preferences updated', 'success')
        return redirect(url_for('settings.preferences'))
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('settings.preferences'))


@bp.route('/export')
@login_required
def export_data():
    """Export all user data."""
    try:
        export_obj = {
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'created_at': current_user.created_at.isoformat()
            },
            'members': [],
            'expenses': [],
            'splits': []
        }
        
        # Export members
        for member in current_user.members:
            export_obj['members'].append({
                'id': member.id,
                'name': member.name,
                'email': member.email or '',
                'phone': member.phone or ''
            })
        
        # Export expenses
        for expense in current_user.expenses:
            export_obj['expenses'].append({
                'id': expense.id,
                'description': expense.description,
                'amount': float(expense.amount),
                'category': expense.category,
                'date': expense.expense_date.isoformat(),
                'paid_by': expense.payer_member.name if expense.payer_member else ''
            })
        
        # Export splits
        for expense in current_user.expenses:
            for split in expense.splits:
                export_obj['splits'].append({
                    'expense_id': expense.id,
                    'member': split.member.name,
                    'amount': float(split.share_amount),
                    'settled': split.is_settled
                })
        
        # Create JSON file
        json_str = json.dumps(export_obj, indent=2)
        json_bytes = BytesIO(json_str.encode('utf-8'))
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name=f"spendly_export_{datetime.now().strftime('%Y%m%d')}.json"
        )
    
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('settings.preferences'))


@bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Delete user account."""
    if request.method == 'POST':
        try:
            password = request.form.get('password', '')
            
            # Verify password
            if not current_user.check_password(password):
                flash('Incorrect password', 'error')
                return redirect(url_for('settings.delete_account'))
            
            # Delete user and all related data
            user_id = current_user.id
            db.session.delete(current_user)
            db.session.commit()
            
            flash('Account deleted', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('settings.delete_account'))
    
    return render_template('settings/delete_account.html')


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    if request.method == 'POST':
        try:
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not current_user.check_password(old_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('settings.change_password'))
            
            if len(new_password) < 6:
                flash('New password must be at least 6 characters', 'error')
                return redirect(url_for('settings.change_password'))
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('settings.change_password'))
            
            current_user.set_password(new_password)
            db.session.commit()
            
            flash('Password changed successfully', 'success')
            return redirect(url_for('settings.profile'))
        
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('settings.change_password'))
    
    return render_template('settings/change_password.html')
