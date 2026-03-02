"""Member management blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from . import db
from .models import Member, Expense, ExpenseSplit

bp = Blueprint('members', __name__, url_prefix='/members', template_folder='templates')

@bp.route('/')
@login_required
def members_list():
    """List all members with stats."""
    members = Member.query.filter_by(user_id=current_user.id).all()
    
    # Calculate stats per member
    for member in members:
        # Total paid
        member.total_paid = sum(e.amount for e in Expense.query.filter_by(paid_by_member_id=member.id).all())
        
        # Total share (unsettled)
        member.total_share = sum(s.share_amount for s in ExpenseSplit.query.filter_by(member_id=member.id, is_settled=False).all())
    
    return render_template('members/manage.html', members=members)

@bp.route('/add', methods=['POST'])
@login_required
def add_member():
    """Add new member (AJAX)."""
    try:
        data = request.get_json() or request.form
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        member = Member(
            user_id=current_user.id,
            name=name,
            email=email or None,
            phone=phone or None
        )
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'member': {
                'id': member.id,
                'name': member.name,
                'email': member.email,
                'phone': member.phone
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/get/<int:id>')
@login_required
def get_member(id):
    """Get member details (AJAX)."""
    member = Member.query.get_or_404(id)
    if member.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    return jsonify({
        'success': True,
        'member': {
            'id': member.id,
            'name': member.name,
            'email': member.email or '',
            'phone': member.phone or ''
        }
    })

@bp.route('/<int:id>/expenses-count')
@login_required
def member_expenses_count(id):
    """Get count of expenses involving this member."""
    member = Member.query.get_or_404(id)
    if member.user_id != current_user.id:
        return jsonify({'count': 0}), 403
    
    count = ExpenseSplit.query.filter_by(member_id=id).count()
    return jsonify({'count': count})

@bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit_member(id):
    """Edit member details."""
    member = Member.query.get_or_404(id)
    if member.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json() or request.form
        member.name = data.get('name', member.name).strip()
        member.email = data.get('email', member.email or '').strip() or None
        member.phone = data.get('phone', member.phone or '').strip() or None
        
        db.session.commit()
        return jsonify({'success': True, 'member': {
            'id': member.id,
            'name': member.name,
            'email': member.email,
            'phone': member.phone
        }})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_member(id):
    """Delete member (check for associated expenses)."""
    member = Member.query.get_or_404(id)
    if member.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Check if member has any associated expenses
        expenses = Expense.query.filter_by(paid_by_member_id=id).count()
        splits = ExpenseSplit.query.filter_by(member_id=id).count()
        
        if expenses > 0 or splits > 0:
            return jsonify({
                'success': False,
                'error': f'Cannot delete. Member is used in {splits} split(s).'
            }), 400
        
        db.session.delete(member)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
