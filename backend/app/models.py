"""Spendly Database Models"""
from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Expense Categories (no emojis - use plain names or Font Awesome icons in templates)
EXPENSE_CATEGORIES = {
    'Food': 'fa-utensils',
    'Transport': 'fa-car',
    'Shopping': 'fa-shopping-bag',
    'Bills': 'fa-file-invoice',
    'Entertainment': 'fa-film',
    'Travel': 'fa-plane',
    'Health': 'fa-heart-pulse',
    'Other': 'fa-bookmark'
}

class User(UserMixin, db.Model):
    """User model for authentication and group management."""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_pic = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    members = db.relationship('Member', backref='user', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password."""
        return check_password_hash(self.password_hash, password)
    
    def total_spent(self):
        """Calculate total amount spent by user."""
        return sum(e.amount for e in self.expenses)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Member(db.Model):
    """Group member model for expense sharing."""
    __tablename__ = 'member'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    avatar_color = db.Column(db.String(7), default='#6366f1')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expense_splits = db.relationship('ExpenseSplit', backref='member', lazy=True, cascade='all, delete-orphan')
    paid_expenses = db.relationship('Expense', backref='payer_member', lazy=True, foreign_keys='Expense.paid_by_member_id')
    
    def total_share(self):
        """Calculate total amount this member owes/is owed."""
        return sum(split.share_amount for split in self.expense_splits if not split.is_settled)
    
    def __repr__(self):
        return f'<Member {self.name}>'


class Expense(db.Model):
    """Expense model for tracking group expenses."""
    __tablename__ = 'expense'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    paid_by_member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80), default='Other')
    split_type = db.Column(db.String(20), default='equal')  # equal, custom, percentage
    expense_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    splits = db.relationship('ExpenseSplit', backref='expense', lazy=True, cascade='all, delete-orphan')
    
    def get_category_emoji(self):
        """Get emoji for category."""
        return EXPENSE_CATEGORIES.get(self.category, '')
    
    def __repr__(self):
        return f'<Expense {self.description}: ₹{self.amount}>'


class ExpenseSplit(db.Model):
    """Expense split model for tracking individual shares."""
    __tablename__ = 'expense_split'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False, index=True)
    share_amount = db.Column(db.Float, nullable=False)
    is_settled = db.Column(db.Boolean, default=False)
    settled_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ExpenseSplit member={self.member_id}: ₹{self.share_amount}>'
