"""Simple AI endpoints: category prediction and insights (rule-based)."""
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from .models import Expense, EXPENSE_CATEGORIES
from . import db
import re

bp = Blueprint('ai', __name__, url_prefix='/api')

# Simple keyword-based mapping
KEYWORD_MAP = {
    'food': ['lunch', 'dinner', 'breakfast', 'coffee', 'restaurant', 'cafe', 'meal', 'pizza', 'burger'],
    'transport': ['uber', 'taxi', 'bus', 'train', 'uber', 'lyft', 'gas', 'petrol', 'taxi', 'parking'],
    'shopping': ['shop', 'mall', 'amazon', 'purchase', 'order', 'shirt', 'shoes', 'grocery', 'store'],
    'bills': ['bill', 'utility', 'electricity', 'water', 'internet', 'rent', 'subscription'],
    'entertainment': ['movie', 'netflix', 'cinema', 'concert', 'tickets', 'games', 'spotify'],
    'travel': ['flight', 'hotel', 'airbnb', 'trip', 'travel', 'ticket'],
    'health': ['doctor', 'pharmacy', 'hospital', 'clinic', 'medicine', 'medical']
}

@bp.route('/predict_category', methods=['POST'])
def predict_category():
    """Predict category from description using simple keyword matches.
    Request JSON: { "description": "..." }
    Response: { "category": "Food", "emoji": "🍔", "confidence": 0.75 }
    """
    data = request.get_json(silent=True) or {}
    description = (data.get('description') or '').lower()
    if not description:
        return jsonify({'error': 'Missing description'}), 400

    scores = {}
    for cat, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in description:
                scores[cat] = scores.get(cat, 0) + 1

    # also consider numbers (bills, amounts)
    if re.search(r"\b\d+[\.,]?\d*\b", description):
        scores.setdefault('bills', 0)
        scores['bills'] += 0.2

    if scores:
        best = max(scores.items(), key=lambda x: x[1])[0]
        # normalize confidence
        total = sum(scores.values())
        confidence = min(0.95, scores[best] / (total if total > 0 else 1))
    else:
        best = 'Other'
        confidence = 0.25

    # Map to one of EXPENSE_CATEGORIES keys if possible
    matched = None
    for k in EXPENSE_CATEGORIES.keys():
        if k.lower() == best.lower():
            matched = k
            break
    if matched is None:
        # fallback to 'Other'
        matched = 'Other'

    return jsonify({'category': matched, 'confidence': round(float(confidence), 2)})

@bp.route('/insights', methods=['GET'])
@login_required
def insights():
    """Return simple insights for current user: top categories and averages."""
    try:
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        total = sum(e.amount for e in expenses) if expenses else 0.0
        count = len(expenses)
        avg = (total / count) if count else 0.0

        # top categories
        counts = {}
        sums = {}
        for e in expenses:
            c = e.category or 'Other'
            counts[c] = counts.get(c, 0) + 1
            sums[c] = sums.get(c, 0.0) + float(e.amount)

        top_categories = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        avg_by_category = {c: round((sums[c] / counts[c]) if counts[c] else 0.0, 2) for c in counts}

        return jsonify({
            'total_spent': round(total, 2),
            'transaction_count': count,
            'average_transaction': round(avg, 2),
            'top_categories': [{'category': c, 'count': n} for c, n in top_categories],
            'avg_by_category': avg_by_category
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
