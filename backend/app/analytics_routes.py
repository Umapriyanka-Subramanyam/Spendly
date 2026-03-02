"""Analytics blueprint with routes and insights."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .analytics import (
    get_expense_summary, get_spending_trends, get_category_distribution,
    get_member_analysis, get_spending_patterns, predict_future_expenses,
    predict_category_budget, get_insights, get_spending_forecast_data,
    get_predictions_data, clear_cache
)
import json

bp = Blueprint('analytics', __name__, url_prefix='/analytics', template_folder='templates')

@bp.route('/')
@login_required
def analytics():
    """Main analytics dashboard."""
    return render_template('analytics.html')

@bp.route('/predictions')
@login_required
def predictions():
    """AI predictions page."""
    predictions_data = get_predictions_data(current_user.id)
    return render_template('predictions.html', data=predictions_data)

# ===== AJAX API ENDPOINTS =====

@bp.route('/api/summary')
@login_required
def api_summary():
    """Get expense summary for selected period."""
    period = request.args.get('period', 'month')
    
    # Map period to days
    period_days = {
        'week': 7,
        'month': 30,
        'quarter': 90,
        'year': 365
    }
    days = period_days.get(period, 30)
    
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    summary = get_expense_summary(current_user.id, start_date, end_date)
    return jsonify(summary)

@bp.route('/api/trends')
@login_required
def api_trends():
    """Get spending trends for chart."""
    period = request.args.get('period', 'day')
    months = request.args.get('months', 6, type=int)
    
    trends = get_spending_trends(current_user.id, period=period, months_back=months)
    return jsonify(trends)

@bp.route('/api/categories')
@login_required
def api_categories():
    """Get category distribution."""
    months = request.args.get('months', 3, type=int)
    data = get_category_distribution(current_user.id, months_back=months)
    return jsonify(data)

@bp.route('/api/members')
@login_required
def api_members():
    """Get member analysis."""
    data = get_member_analysis(current_user.id)
    return jsonify(data)

@bp.route('/api/patterns')
@login_required
def api_patterns():
    """Get spending patterns."""
    months = request.args.get('months', 3, type=int)
    data = get_spending_patterns(current_user.id, months_back=months)
    return jsonify(data)

@bp.route('/api/insights')
@login_required
def api_insights():
    """Get AI insights."""
    days = request.args.get('days', 30, type=int)
    insights = get_insights(current_user.id, days=days)
    return jsonify({'insights': insights})

@bp.route('/api/predictions')
@login_required
def api_predictions():
    """Get spending predictions."""
    months = request.args.get('months', 3, type=int)
    predictions = predict_future_expenses(current_user.id, months_ahead=months)
    return jsonify(predictions)

@bp.route('/api/category-budget')
@login_required
def api_category_budget():
    """Get budget recommendation for category."""
    category = request.args.get('category')
    if not category:
        return jsonify({'error': 'Category required'}), 400
    
    budget = predict_category_budget(current_user.id, category)
    return jsonify(budget)

@bp.route('/api/forecast')
@login_required
def api_forecast():
    """Get forecast data for visualization."""
    data = get_spending_forecast_data(current_user.id)
    return jsonify(data)

@bp.route('/api/export')
@login_required
def api_export():
    """Export analytics as PDF or CSV."""
    export_type = request.args.get('type', 'pdf')
    period = request.args.get('period', 'month')
    
    from datetime import datetime, timedelta
    period_days = {
        'week': 7,
        'month': 30,
        'quarter': 90,
        'year': 365
    }
    days = period_days.get(period, 30)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    if export_type == 'csv':
        return export_csv(current_user.id, start_date, end_date)
    else:
        return export_pdf(current_user.id, start_date, end_date)

def export_csv(user_id, start_date, end_date):
    """Export analytics as CSV."""
    from .models import Expense
    import pandas as pd
    from io import StringIO
    from flask import send_file
    
    expenses = Expense.query.filter_by(user_id=user_id).filter(
        Expense.created_at >= start_date,
        Expense.created_at <= end_date
    ).all()
    
    data = []
    for exp in expenses:
        data.append({
            'Date': exp.created_at.strftime('%Y-%m-%d'),
            'Description': exp.description,
            'Category': exp.category,
            'Amount': exp.amount,
            'Paid By': exp.payer_member.name if exp.payer_member else 'N/A'
        })
    
    df = pd.DataFrame(data)
    
    # Create CSV in memory
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    from io import BytesIO
    csv_bytes = BytesIO(csv_buffer.getvalue().encode())
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"spendly_analytics_{start_date.date()}.csv"
    )

def export_pdf(user_id, start_date, end_date):
    """Export analytics as PDF with charts."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
        from flask import send_file
        
        summary = get_expense_summary(user_id, start_date, end_date)
        categories = get_category_distribution(user_id)
        
        # Create PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph('Spendly Analytics Report', title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary section
        summary_style = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=12
        )
        story.append(Paragraph('Expense Summary', summary_style))
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Expenses', f"₹{summary['total']:.2f}"],
            ['Number of Expenses', str(summary['count'])],
            ['Average Expense', f"₹{summary['average']:.2f}"],
            ['Highest Expense', f"₹{summary['highest_expense']:.2f}"],
            ['Period', f"{summary['period_days']} days"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Category breakdown
        story.append(Paragraph('Category Breakdown', summary_style))
        cat_data = [['Category', 'Amount', 'Percentage']]
        for cat, stats in summary['categories_breakdown'].items():
            cat_data.append([
                cat,
                f"₹{stats['amount']:.2f}",
                f"{stats['percentage']:.1f}%"
            ])
        
        cat_table = Table(cat_data, colWidths=[2*inch, 2*inch, 2*inch])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(cat_table)
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"spendly_analytics_{start_date.date()}.pdf"
        )
    
    except ImportError:
        return jsonify({
            'error': 'PDF export requires reportlab. Install with: pip install reportlab'
        }), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
