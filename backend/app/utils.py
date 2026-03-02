import pandas as pd
from . import db
from .models import Expense


def load_expenses_df():
    """Load expenses as a pandas DataFrame."""
    try:
        expenses = Expense.query.all()
        data = []
        for exp in expenses:
            data.append({
                'id': exp.id,
                'amount': exp.amount,
                'category': exp.category,
                'description': exp.description,
                'expense_date': exp.expense_date,
                'user_id': exp.user_id,
                'created_at': exp.created_at
            })
        df = pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        print(f"Error loading expenses: {e}")
        df = pd.DataFrame()
    return df

def format_currency(amount):
    """Format amount as Indian Rupees (₹)."""
    if not isinstance(amount, (int, float)):
        return "₹0.00"
    return f"₹{amount:,.2f}"


def parse_amount(amount_str):
    """Parse amount string to float."""
    if isinstance(amount_str, (int, float)):
        return float(amount_str)
    
    # Remove ₹ and commas, convert to float
    cleaned = str(amount_str).replace('₹', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0