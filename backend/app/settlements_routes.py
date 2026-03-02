"""Settlements blueprint for payment tracking and settlement management."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from .settlements import (
    calculate_optimal_settlements, get_settlement_history,
    get_settlement_summary, mark_settlement_paid
)
from .models import Member, Expense

bp = Blueprint('settlements', __name__, url_prefix='/settlements', template_folder='templates')


@bp.route('/')
@login_required
def settlements():
    """Display settlement recommendations and history."""
    settlements_list = calculate_optimal_settlements(current_user.id)
    summary = get_settlement_summary(current_user.id)
    history = get_settlement_history(current_user.id)
    
    return render_template(
        'settlements.html',
        settlements=settlements_list,
        summary=summary,
        history=history[:10]  # Last 10 settlements
    )


@bp.route('/mark-settled', methods=['POST'])
@login_required
def mark_settled():
    """Mark a settlement as paid."""
    try:
        data = request.get_json()
        debtor_id = data.get('debtor_id')
        creditor_id = data.get('creditor_id')
        amount = float(data.get('amount', 0))
        
        if not all([debtor_id, creditor_id, amount > 0]):
            return jsonify({'error': 'Invalid settlement data'}), 400
        
        # Verify both members belong to current user
        debtor = Member.query.get(debtor_id)
        creditor = Member.query.get(creditor_id)
        
        if not debtor or not creditor or debtor.user_id != current_user.id or creditor.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        result = mark_settlement_paid(debtor_id, creditor_id, amount, current_user.id)
        
        if result['success']:
            flash(f"Settlement of ₹{amount:.2f} marked as paid", 'success')
            return jsonify({'success': True, 'remaining': result['remaining']})
        else:
            flash(f"Only ₹{amount - result['remaining']:.2f} could be settled", 'warning')
            return jsonify({'success': False, 'remaining': result['remaining']})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history')
@login_required
def history():
    """Show complete settlement history."""
    history_list = get_settlement_history(current_user.id)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    total = len(history_list)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated = history_list[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    return render_template(
        'settlements_history.html',
        history=paginated,
        page=page,
        total_pages=total_pages,
        total=total
    )


@bp.route('/api/summary')
@login_required
def api_summary():
    """Get settlement summary as JSON."""
    summary = get_settlement_summary(current_user.id)
    return jsonify(summary)


@bp.route('/api/recommendations')
@login_required
def api_recommendations():
    """Get settlement recommendations as JSON."""
    settlements_list = calculate_optimal_settlements(current_user.id)
    return jsonify({'settlements': settlements_list})
