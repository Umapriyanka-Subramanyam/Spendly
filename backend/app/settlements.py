"""Settlement and payment tracking module."""
from datetime import datetime
from .models import Expense, ExpenseSplit, Member
from . import db


def calculate_net_balances(user_id):
    """
    Calculate net balance for each member.
    Positive = member is owed money, Negative = member owes money.
    """
    members = Member.query.filter_by(user_id=user_id).all()
    balances = {}
    
    for member in members:
        # Total paid by member
        paid_total = sum(
            exp.amount for exp in Expense.query.filter_by(paid_by_member_id=member.id).all()
        )
        
        # Total owed by member (from splits)
        owed_total = sum(
            split.share_amount for split in ExpenseSplit.query.filter_by(member_id=member.id).all()
            if not split.is_settled
        )
        
        # Exclude what member paid for themselves
        self_paid = sum(
            split.share_amount for split in ExpenseSplit.query.filter_by(member_id=member.id).all()
            if split.expense.paid_by_member_id == member.id
        )
        
        net_balance = paid_total - owed_total
        balances[member.id] = {
            'member': member,
            'paid': paid_total,
            'owed': owed_total,
            'balance': net_balance
        }
    
    return balances


def calculate_optimal_settlements(user_id):
    """
    Generate optimal settlement recommendations using greedy algorithm.
    Minimizes number of transactions needed to settle all debts.
    
    Algorithm:
    1. Calculate net balance for each member
    2. Separate creditors (positive balance) and debtors (negative balance)
    3. Match largest debtor with largest creditor
    4. Settle maximum possible amount
    5. Remove settled members and repeat
    """
    balances = calculate_net_balances(user_id)
    
    # Separate creditors and debtors
    creditors = []  # (member_id, amount)
    debtors = []    # (member_id, amount)
    
    for member_id, data in balances.items():
        if data['balance'] > 0.01:  # Small tolerance for float precision
            creditors.append([member_id, data['balance']])
        elif data['balance'] < -0.01:
            debtors.append([member_id, -data['balance']])
    
    settlements = []
    
    # Greedy matching algorithm
    while creditors and debtors:
        # Get largest creditor and debtor
        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)
        
        creditor_id, credit_amount = creditors[0]
        debtor_id, debt_amount = debtors[0]
        
        # Settle minimum of credit and debt
        settle_amount = min(credit_amount, debt_amount)
        
        creditor = Member.query.get(creditor_id)
        debtor = Member.query.get(debtor_id)
        
        settlements.append({
            'from': debtor.name,
            'from_id': debtor_id,
            'to': creditor.name,
            'to_id': creditor_id,
            'amount': round(settle_amount, 2),
            'type': 'settlement'
        })
        
        # Update amounts
        creditors[0][1] -= settle_amount
        debtors[0][1] -= settle_amount
        
        # Remove if settled
        if creditors[0][1] < 0.01:
            creditors.pop(0)
        if debtors[0][1] < 0.01:
            debtors.pop(0)
    
    return settlements


def mark_settlement_paid(debtor_id, creditor_id, amount, user_id):
    """
    Mark expense splits as settled when payment is made.
    Marks the minimum splits needed to cover the settlement amount.
    """
    unsettled_splits = ExpenseSplit.query.filter(
        ExpenseSplit.member_id == debtor_id,
        ExpenseSplit.is_settled == False
    ).all()
    
    # Filter for splits from expenses paid by creditor
    relevant_splits = [
        split for split in unsettled_splits
        if split.expense.paid_by_member_id == creditor_id
    ]
    
    remaining = amount
    settled_splits = []
    
    for split in relevant_splits:
        if remaining <= 0.01:
            break
        
        settle_amount = min(split.share_amount, remaining)
        
        # For simplicity, mark the entire split as settled if partially paid
        split.is_settled = True
        split.settled_at = datetime.utcnow()
        settled_splits.append(split)
        
        remaining -= settle_amount
    
    db.session.commit()
    
    return {
        'settled_splits': len(settled_splits),
        'remaining': max(0, remaining),
        'success': remaining < 0.01
    }


def get_settlement_history(user_id):
    """Get history of settled transactions."""
    settled_splits = ExpenseSplit.query.filter(
        ExpenseSplit.is_settled == True,
        ExpenseSplit.settled_at.isnot(None)
    ).all()
    
    history = []
    for split in settled_splits:
        if split.expense.user_id == user_id:
            history.append({
                'member': split.member.name,
                'amount': split.share_amount,
                'date': split.settled_at,
                'expense': split.expense.description,
                'category': split.expense.category
            })
    
    return sorted(history, key=lambda x: x['date'], reverse=True)


def get_settlement_summary(user_id):
    """Get overall settlement summary."""
    balances = calculate_net_balances(user_id)
    
    total_owed_to_user = sum(
        data['balance'] for data in balances.values() if data['balance'] > 0
    )
    total_user_owes = sum(
        abs(data['balance']) for data in balances.values() if data['balance'] < 0
    )
    
    return {
        'total_owed_to_you': round(total_owed_to_user, 2),
        'total_you_owe': round(total_user_owes, 2),
        'net_balance': round(total_owed_to_user - total_user_owes, 2),
        'members_involved': len([b for b in balances.values() if abs(b['balance']) > 0.01])
    }
