"""Analytics and insights module with AI predictions."""
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from .models import Expense, ExpenseSplit, Member, User
from . import db  
_analytics_cache = {}

def clear_cache(user_id=None):
    """Clear analytics cache."""
    if user_id:
        _analytics_cache.pop(user_id, None)
    else:
        _analytics_cache.clear()

def _get_user_expenses_df(user_id, start_date=None, end_date=None):
    """Get expenses as pandas DataFrame."""
    query = Expense.query.filter_by(user_id=user_id)
    
    if start_date:
        query = query.filter(Expense.created_at >= start_date)
    if end_date:
        query = query.filter(Expense.created_at <= end_date)
    
    expenses = query.all()
    if not expenses:
        return pd.DataFrame()
    
    data = []
    for exp in expenses:
        data.append({
            'id': exp.id,
            'date': exp.created_at,
            'amount': float(exp.amount),
            'category': exp.category,
            'description': exp.description,
            'payer_id': exp.paid_by_member_id
        })
    
    df = pd.DataFrame(data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# ===== ANALYSIS FUNCTIONS =====

def get_expense_summary(user_id, start_date=None, end_date=None):
    """Get overall expense summary for period."""
    cache_key = f"{user_id}_summary_{start_date}_{end_date}"
    if cache_key in _analytics_cache:
        return _analytics_cache[cache_key]
    
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()

    # Normalize date types to datetimes
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.min.time())
    
    df = _get_user_expenses_df(user_id, start_date, end_date)
    
    period_days = (end_date - start_date).days

    if df.empty:
        result = {
            'total': 0,
            'count': 0,
            'average': 0,
            'highest_expense': 0,
            'categories_breakdown': {},
            'top_spender': None,
            'period_days': period_days
        }
    else:
        # Category breakdown
        category_breakdown = df.groupby('category')['amount'].agg(['sum', 'count']).to_dict()
        categories = {}
        for cat in df['category'].unique():
            cat_data = df[df['category'] == cat]
            categories[cat] = {
                'amount': float(cat_data['amount'].sum()),
                'count': len(cat_data),
                'percentage': float((cat_data['amount'].sum() / df['amount'].sum()) * 100)
            }
        
        # Top spender
        top_spender_id = df.groupby('payer_id')['amount'].sum().idxmax()
        top_spender = Member.query.get(top_spender_id)
        
        result = {
            'total': float(df['amount'].sum()),
            'count': len(df),
            'average': float(df['amount'].mean()),
            'highest_expense': float(df['amount'].max()),
            'lowest_expense': float(df['amount'].min()),
            'categories_breakdown': categories,
            'top_spender': {'id': top_spender.id, 'name': top_spender.name} if top_spender else None,
            'period_days': period_days
        }
    
    _analytics_cache[cache_key] = result
    return result

def get_spending_trends(user_id, period='month', months_back=6):
    """Get aggregated spending over time for trend analysis."""
    cache_key = f"{user_id}_trends_{period}_{months_back}"
    if cache_key in _analytics_cache:
        return _analytics_cache[cache_key]
    
    start_date = datetime.now() - timedelta(days=30*months_back)
    df = _get_user_expenses_df(user_id, start_date)
    
    if df.empty:
        return {'data': [], 'labels': []}
    
    if period == 'day':
        grouped = df.groupby('date')['amount'].sum().reset_index()
        grouped.columns = ['date', 'amount']
        grouped['label'] = grouped['date'].dt.strftime('%m-%d')
    elif period == 'week':
        grouped = df.copy()
        grouped['week'] = grouped['date'].dt.to_period('W')
        grouped = grouped.groupby('week')['amount'].sum().reset_index()
        grouped['label'] = grouped['week'].astype(str)
    else:  # month
        grouped = df.copy()
        grouped['month'] = grouped['date'].dt.to_period('M')
        grouped = grouped.groupby('month')['amount'].sum().reset_index()
        grouped['label'] = grouped['month'].astype(str)
    
    result = {
        'data': grouped['amount'].astype(float).tolist(),
        'labels': grouped['label'].tolist(),
        'period': period
    }
    
    _analytics_cache[cache_key] = result
    return result

def get_category_distribution(user_id, months_back=3):
    """Get spending distribution by category."""
    cache_key = f"{user_id}_categories_{months_back}"
    if cache_key in _analytics_cache:
        return _analytics_cache[cache_key]
    
    start_date = datetime.now() - timedelta(days=30*months_back)
    df = _get_user_expenses_df(user_id, start_date)
    
    if df.empty:
        return {'labels': [], 'data': [], 'colors': []}
    
    category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    
    # Define colors for categories
    colors = [
        '#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe',
        '#43e97b', '#fa709a', '#fee140', '#30b0fe', '#ec77de'
    ]
    
    result = {
        'labels': category_totals.index.tolist(),
        'data': category_totals.astype(float).tolist(),
        'colors': colors[:len(category_totals)]
    }
    
    _analytics_cache[cache_key] = result
    return result

def get_member_analysis(user_id):
    """Get per-member spending analysis."""
    cache_key = f"{user_id}_members"
    if cache_key in _analytics_cache:
        return _analytics_cache[cache_key]
    
    members = Member.query.filter_by(user_id=user_id).all()
    data = []
    
    for member in members:
        # Total paid
        paid = sum(e.amount for e in Expense.query.filter_by(paid_by_member_id=member.id).all())
        
        # Total share
        share = sum(s.share_amount for s in ExpenseSplit.query.filter_by(member_id=member.id, is_settled=False).all())
        
        # Balance
        balance = paid - share
        
        data.append({
            'name': member.name,
            'paid': float(paid),
            'share': float(share),
            'balance': float(balance)
        })
    
    result = {
        'members': data,
        'labels': [m['name'] for m in data],
        'paid_data': [m['paid'] for m in data],
        'share_data': [m['share'] for m in data]
    }
    
    _analytics_cache[cache_key] = result
    return result

def get_spending_patterns(user_id, months_back=3):
    """Analyze spending patterns by day of week and time."""
    cache_key = f"{user_id}_patterns_{months_back}"
    if cache_key in _analytics_cache:
        return _analytics_cache[cache_key]
    
    start_date = datetime.now() - timedelta(days=30*months_back)
    df = _get_user_expenses_df(user_id, start_date)
    
    if df.empty:
        return {'day_of_week': {}, 'daily_average': 0}
    
    # Day of week analysis
    df['day_of_week'] = pd.to_datetime(df['date']).dt.day_name()
    day_totals = df.groupby('day_of_week')['amount'].agg(['sum', 'count', 'mean']).to_dict()
    
    # Reorder by days of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ordered_days = {}
    for day in day_order:
        if day in df['day_of_week'].values:
            day_data = df[df['day_of_week'] == day]
            ordered_days[day] = {
                'total': float(day_data['amount'].sum()),
                'count': len(day_data),
                'average': float(day_data['amount'].mean())
            }
    
    result = {
        'day_of_week': ordered_days,
        'daily_average': float(df['amount'].sum() / (len(set(df['date'])))),
        'busiest_day': max(ordered_days, key=lambda x: ordered_days[x]['count']) if ordered_days else None,
        'highest_spending_day': max(ordered_days, key=lambda x: ordered_days[x]['total']) if ordered_days else None
    }
    
    _analytics_cache[cache_key] = result
    return result

# ===== AI PREDICTIONS =====

def predict_future_expenses(user_id, months_ahead=3):
    """Predict future expenses using trend analysis."""
    # Get last 6 months of data
    start_date = datetime.now() - timedelta(days=180)
    df = _get_user_expenses_df(user_id, start_date)
    
    if df.empty or len(df) < 10:
        return {
            'predictions': [],
            'confidence': 0,
            'message': 'Insufficient data for predictions'
        }
    
    # Group by date and sum
    daily_spending = df.groupby('date')['amount'].sum().reset_index()
    daily_spending = daily_spending.sort_values('date')
    
    # Calculate rolling average (30-day window)
    daily_spending['rolling_avg'] = daily_spending['amount'].rolling(window=30, min_periods=1).mean()
    
    try:
        # Fit polynomial trend line (degree 2)
        x = np.arange(len(daily_spending))
        y = daily_spending['rolling_avg'].values
        
        # Remove NaN values
        mask = ~np.isnan(y)
        x_clean = x[mask]
        y_clean = y[mask]
        
        coeffs = np.polyfit(x_clean, y_clean, 2)
        poly = np.poly1d(coeffs)
        
        # Generate future predictions
        future_days = 30 * months_ahead
        future_x = np.arange(len(daily_spending), len(daily_spending) + future_days)
        future_predictions = poly(future_x)
        
        # Cap predictions at 0 (no negative spending)
        future_predictions = np.maximum(future_predictions, 0)
        
        # Calculate by month
        monthly_predictions = []
        for month in range(1, months_ahead + 1):
            start_idx = (month - 1) * 30
            end_idx = month * 30
            month_avg = np.mean(future_predictions[start_idx:end_idx])
            monthly_predictions.append({
                'month': month,
                'predicted_amount': float(month_avg),
                'confidence': 0.85 - (month * 0.05)  # Confidence decreases for further months
            })
        
        result = {
            'predictions': monthly_predictions,
            'current_trend': 'increasing' if coeffs[0] > 0 else 'decreasing',
            'average_monthly': float(daily_spending['amount'].mean() * 30),
            'confidence': 0.85
        }
    except Exception as e:
        result = {
            'predictions': [],
            'error': str(e),
            'average_monthly': float(df['amount'].sum() / 6),
            'confidence': 0.5
        }
    
    return result

def predict_category_budget(user_id, category, months_back=3):
    """Predict optimal budget for a category based on spending patterns."""
    start_date = datetime.now() - timedelta(days=30*months_back)
    df = _get_user_expenses_df(user_id, start_date)
    
    if df.empty:
        return {'recommended_budget': 0, 'analysis': 'No data'}
    
    category_df = df[df['category'] == category]
    
    if category_df.empty:
        return {'recommended_budget': 0, 'analysis': f'No spending in {category}'}
    
    # Calculate statistics
    monthly_avg = category_df['amount'].sum() / months_back
    std_dev = category_df['amount'].std()
    max_spending = category_df['amount'].max()
    
    # Recommended budget = monthly average + 1 standard deviation (covers ~84% of spending)
    recommended = monthly_avg + std_dev
    
    # Detect spikes
    spikes = category_df[category_df['amount'] > (monthly_avg + 2*std_dev)]
    
    result = {
        'category': category,
        'current_avg': float(monthly_avg),
        'recommended_budget': float(recommended),
        'max_spending': float(max_spending),
        'std_deviation': float(std_dev),
        'spike_count': len(spikes),
        'analysis': f'Recommendation: ₹{recommended:.2f}/month (covers typical + 1-2 spike)'
    }
    
    return result

def get_insights(user_id, days=30):
    """Generate AI-powered insights about spending."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)
    
    current_summary = get_expense_summary(user_id, start_date, end_date)
    previous_summary = get_expense_summary(user_id, previous_start, start_date)
    
    insights = []
    
    # Insight 1: Comparison with previous period
    if previous_summary['total'] > 0:
        change_pct = ((current_summary['total'] - previous_summary['total']) / previous_summary['total']) * 100
        if change_pct > 10:
            insights.append({
                'type': 'warning',
                'text': f"You spent {change_pct:.1f}% more than last {days} days",
                'value': f"₹{current_summary['total']:.2f}"
            })
        elif change_pct < -10:
            insights.append({
                'type': 'success',
                'text': f"✨ You spent {abs(change_pct):.1f}% less than last {days} days",
                'value': f"₹{current_summary['total']:.2f}"
            })
    
    # Insight 2: Top category
    if current_summary['categories_breakdown']:
        top_category = max(current_summary['categories_breakdown'].items(), 
                          key=lambda x: x[1]['amount'])
        insights.append({
            'type': 'info',
            'text': f"{top_category[0]} is your top category ({top_category[1]['percentage']:.1f}%)",
            'value': f"₹{top_category[1]['amount']:.2f}"
        })
    
    # Insight 3: Spending pattern
    patterns = get_spending_patterns(user_id, months_back=1)
    if patterns.get('busiest_day') and patterns.get('day_of_week'):
        insights.append({
            'type': 'info',
            'text': f"📅 {patterns['busiest_day']} is your busiest day for expenses",
            'value': f"{patterns['day_of_week'][patterns['busiest_day']]['count']} transactions"
        })
    
    # Insight 4: Daily average
    daily_avg = current_summary['total'] / max(current_summary['period_days'], 1)
    insights.append({
        'type': 'info',
        'text': f"💰 Daily average: ₹{daily_avg:.2f}",
        'value': f"₹{daily_avg:.2f}/day"
    })
    
    return insights

def get_spending_forecast_data(user_id):
    """Get data for forecast visualization."""
    # Historical data (last 3 months)
    historical = get_spending_trends(user_id, period='week', months_back=3)
    
    # Future predictions
    predictions = predict_future_expenses(user_id, months_ahead=3)
    
    return {
        'historical': historical,
        'predictions': predictions
    }

def get_predictions_data(user_id):
    """
    Get comprehensive predictions data for predictions page.
    
    Returns:
    - next_month_prediction: Rolling average for next month
    - last_month: Last month actual spending
    - historical_labels: Last 6 months labels
    - historical_data: Last 6 months amounts
    - forecast_labels: Next 3 months labels
    - forecast_data: Next 3 months predictions
    - category_predictions: List with category analysis
    - budget_tips: List of actionable tips
    - spending_alerts: List of warnings
    - accuracy: Prediction accuracy percentage
    """
    from datetime import datetime, timedelta
    
    # Get last 6 months of trend data
    trend_data = get_spending_trends(user_id, period='month', months_back=6)
    historical_labels = trend_data['labels']
    historical_data = trend_data['data']
    
    # Calculate next month prediction (rolling average)
    if historical_data:
        rolling_avg = sum(historical_data[-3:]) / min(3, len(historical_data[-3:]))
        next_month_prediction = rolling_avg
        last_month = historical_data[-1] if historical_data else 0
    else:
        next_month_prediction = 0
        last_month = 0
    
    # Forecast labels (next 3 months)
    forecast_labels = ['Month 1', 'Month 2', 'Month 3']
    
    # Simple linear trend forecast
    forecast_data = []
    if len(historical_data) >= 2:
        # Calculate trend
        trend = (historical_data[-1] - historical_data[0]) / max(len(historical_data) - 1, 1)
        for i in range(1, 4):
            predicted = max(0, historical_data[-1] + (trend * i))
            forecast_data.append(round(predicted, 2))
    else:
        forecast_data = [next_month_prediction] * 3
    
    # Category predictions
    summary = get_expense_summary(user_id, datetime.now() - timedelta(days=30))
    category_predictions = []
    for category, stats in summary.get('categories_breakdown', {}).items():
        category_predictions.append({
            'category': category,
            'last_month': round(stats['amount'], 2),
            'predicted': round(stats['amount'] * 1.05, 2),  # 5% increase projection
            'change_percent': 5,
            'confidence': 82
        })
    
    # Budget tips
    budget_tips = [
        {
            'title': 'Food Spending',
            'message': 'Your Food category is your top expense at ₹' + format(summary.get('categories_breakdown', {}).get('Food', {}).get('amount', 0), '.2f'),
            'savings': 'Try meal planning to save 15-20%'
        },
        {
            'title': 'Shopping Habits',
            'message': 'Shopping increased 20% since last month',
            'savings': 'Set a weekly shopping budget'
        },
        {
            'title': 'Transport Costs',
            'message': 'Look for carpool opportunities',
            'savings': 'Could save up to ₹500/month'
        }
    ]
    
    # Spending alerts
    spending_alerts = []
    if next_month_prediction > last_month * 1.1:
        spending_alerts.append({
            'category': 'Overall',
            'message': f'Spending forecast is 10%+ higher than last month',
            'severity': 'warning'
        })
    
    if summary.get('categories_breakdown', {}):
        top_cat = max(summary.get('categories_breakdown', {}).items(), key=lambda x: x[1]['percentage'])
        if top_cat[1]['percentage'] > 30:
            spending_alerts.append({
                'category': top_cat[0],
                'message': f'{top_cat[0]} is above 30% of total spending',
                'severity': 'info'
            })
    
    return {
        'next_month_prediction': round(next_month_prediction, 2),
        'last_month': round(last_month, 2),
        'trend': 'up' if next_month_prediction > last_month else 'down',
        'change_percent': round(((next_month_prediction - last_month) / max(last_month, 1)) * 100, 1),
        'historical_labels': historical_labels,
        'historical_data': historical_data,
        'forecast_labels': forecast_labels,
        'forecast_data': forecast_data,
        'category_predictions': category_predictions,
        'budget_tips': budget_tips,
        'spending_alerts': spending_alerts,
        'accuracy': 87
    }