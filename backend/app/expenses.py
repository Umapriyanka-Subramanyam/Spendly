"""Expense management blueprint with split calculations."""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal
from . import db
from .models import Expense, ExpenseSplit, Member, EXPENSE_CATEGORIES

bp = Blueprint('expenses', __name__, url_prefix='/expenses', template_folder='templates')

# ===== SPLIT CALCULATION LOGIC =====

def calculate_equal_split(total_amount: float, member_ids: list) -> dict:
    """Split amount equally among members."""
    if not member_ids:
        return {}
    amount_per_member = Decimal(str(total_amount)) / len(member_ids)
    return {mid: float(amount_per_member) for mid in member_ids}

def calculate_exact_split(splits_dict: dict) -> dict:
    """Use custom amounts per member.
    Args: splits_dict = {member_id: amount, ...}
    """
    total = sum(splits_dict.values())
    if abs(total - sum(Decimal(str(v)) for v in splits_dict.values())) > Decimal('0.01'):
        raise ValueError(f"Splits don't add up to total. Got {total}")
    return splits_dict

def calculate_percentage_split(total_amount: float, percentages_dict: dict) -> dict:
    """Calculate split based on percentages.
    Args: percentages_dict = {member_id: percentage, ...}
    """
    total_pct = sum(percentages_dict.values())
    if abs(total_pct - 100.0) > 0.01:
        raise ValueError(f"Percentages must sum to 100, got {total_pct}")
    return {mid: float(Decimal(str(total_amount)) * Decimal(str(pct)) / 100) 
            for mid, pct in percentages_dict.items()}

# ===== ROUTES =====

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add new expense with multi-step wizard."""
    if request.method == 'GET':
        members = Member.query.filter_by(user_id=current_user.id).all()
        return render_template('expenses/add.html', 
                             members=members,
                             categories=EXPENSE_CATEGORIES,
                             today=datetime.now().strftime('%Y-%m-%d'))
    
    # POST: Handle form submission
    try:
        description = request.form.get('description', '').strip()
        amount = float(request.form.get('amount', 0))
        category = request.form.get('category', 'Other')
        paid_by_member_id = int(request.form.get('paid_by_member_id'))
        split_type = request.form.get('split_type', 'equal')
        expense_date = datetime.strptime(request.form.get('expense_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
        notes = request.form.get('notes', '')
        
        # Validate
        if not description or amount <= 0:
            flash('Invalid expense details', 'danger')
            return redirect(url_for('expenses.add_expense'))
        
        # Create expense
        expense = Expense(
            user_id=current_user.id,
            paid_by_member_id=paid_by_member_id,
            description=description,
            amount=amount,
            category=category,
            split_type=split_type,
            expense_date=expense_date,
            notes=notes
        )
        db.session.add(expense)
        db.session.flush()  # Get expense.id before creating splits
        
        # Calculate and create splits
        member_ids = request.form.getlist('split_members')
        if not member_ids:
            flash('Select at least one member for split', 'danger')
            db.session.rollback()
            return redirect(url_for('expenses.add_expense'))
        
        if split_type == 'equal':
            splits = calculate_equal_split(amount, [int(m) for m in member_ids])
        elif split_type == 'exact':
            # Get exact amounts from form: split_amount_MEMBER_ID
            splits = {}
            for mid in member_ids:
                amt = float(request.form.get(f'split_amount_{mid}', 0))
                if amt > 0:
                    splits[int(mid)] = amt
            splits = calculate_exact_split(splits)
        elif split_type == 'percentage':
            # Get percentages from form: split_pct_MEMBER_ID
            percentages = {}
            for mid in member_ids:
                pct = float(request.form.get(f'split_pct_{mid}', 0))
                if pct > 0:
                    percentages[int(mid)] = pct
            splits = calculate_percentage_split(amount, percentages)
        else:
            raise ValueError(f"Invalid split_type: {split_type}")
        
        # Create ExpenseSplit records
        for member_id, share_amount in splits.items():
            split = ExpenseSplit(
                expense_id=expense.id,
                member_id=member_id,
                share_amount=share_amount,
                is_settled=False
            )
            db.session.add(split)
        
        db.session.commit()
        flash(f'Expense "{description}" added successfully!', 'success')
        return redirect(url_for('expenses.list_expenses'))
    
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid input: {str(e)}', 'danger')
        return redirect(url_for('expenses.add_expense'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding expense: {str(e)}', 'danger')
        return redirect(url_for('expenses.add_expense'))

@bp.route('/list')
@login_required
def list_expenses():
    """List expenses with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Build query
    query = Expense.query.filter_by(user_id=current_user.id)
    
    # Filters
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    date_range = request.args.get('date_range')
    if date_range == 'week':
        query = query.filter(Expense.created_at >= datetime.now() - timedelta(days=7))
    elif date_range == 'month':
        query = query.filter(Expense.created_at >= datetime.now() - timedelta(days=30))
    
    # Paginate
    paginated = query.order_by(Expense.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('expenses/list.html',
                         expenses=paginated.items,
                         pagination=paginated,
                         categories=EXPENSE_CATEGORIES,
                         EXPENSE_CATEGORIES=EXPENSE_CATEGORIES,
                         date_range=date_range)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    """Edit expense."""
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('expenses.list_expenses'))
    
    if request.method == 'GET':
        members = Member.query.filter_by(user_id=current_user.id).all()
        return render_template('expenses/edit.html',
                             expense=expense,
                             members=members,
                             categories=EXPENSE_CATEGORIES)
    
    # POST: Update expense
    try:
        expense.description = request.form.get('description', '').strip()
        expense.amount = float(request.form.get('amount', 0))
        expense.category = request.form.get('category', 'Other')
        expense.paid_by_member_id = int(request.form.get('paid_by_member_id'))
        expense.notes = request.form.get('notes', '')
        
        # Update splits
        ExpenseSplit.query.filter_by(expense_id=id).delete()
        member_ids = request.form.getlist('split_members')
        split_type = request.form.get('split_type', 'equal')
        
        if split_type == 'equal':
            splits = calculate_equal_split(expense.amount, [int(m) for m in member_ids])
        elif split_type == 'exact':
            splits = {}
            for mid in member_ids:
                amt = float(request.form.get(f'split_amount_{mid}', 0))
                if amt > 0:
                    splits[int(mid)] = amt
            splits = calculate_exact_split(splits)
        elif split_type == 'percentage':
            percentages = {}
            for mid in member_ids:
                pct = float(request.form.get(f'split_pct_{mid}', 0))
                if pct > 0:
                    percentages[int(mid)] = pct
            splits = calculate_percentage_split(expense.amount, percentages)
        
        for member_id, share_amount in splits.items():
            split = ExpenseSplit(
                expense_id=id,
                member_id=member_id,
                share_amount=share_amount
            )
            db.session.add(split)
        
        db.session.commit()
        flash('Expense updated', 'success')
        return redirect(url_for('expenses.list_expenses'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('expenses.edit_expense', id=id))

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_expense(id):
    """Delete expense (soft delete)."""
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('expenses.list_expenses'))
    
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting: {str(e)}', 'danger')
    
    return redirect(url_for('expenses.list_expenses'))

@bp.route('/<int:id>')
@login_required
def expense_details(id):
    """Detailed view of an expense."""
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('expenses.list_expenses'))
    
    splits = ExpenseSplit.query.filter_by(expense_id=id).all()
    return render_template('expenses/details.html', 
                         expense=expense, 
                         splits=splits,
                         EXPENSE_CATEGORIES=EXPENSE_CATEGORIES)

@bp.route('/<int:id>/settle', methods=['POST'])
@login_required
def settle_splits(id):
    """Mark splits as settled."""
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        split_ids = request.json.get('split_ids', [])
        for split_id in split_ids:
            split = ExpenseSplit.query.get(split_id)
            if split and split.expense.user_id == current_user.id:
                split.settled_at = datetime.now()
                split.is_settled = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
