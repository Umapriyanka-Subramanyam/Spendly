"""Spendly Flask Application Entry Point"""
import os
from app import create_app, db
from app.models import User, Member, Expense, ExpenseSplit

app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Register models for flask shell."""
    return {
        'db': db,
        'User': User,
        'Member': Member,
        'Expense': Expense,
        'ExpenseSplit': ExpenseSplit
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
