from .utils import load_expenses_df


def summary():
    df = load_expenses_df()
    if df.empty:
        return {'highest_spender': None, 'most_common_category': None, 'avg_share': 0}
    totals = df.groupby('payer')['amount'].sum()
    highest_spender = int(totals.idxmax()) if not totals.empty else None
    most_common_category = df['category'].mode().iloc[0] if not df['category'].mode().empty else None
    unique_payers = df['payer'].nunique() if 'payer' in df.columns else 1
    avg_share = float(df['amount'].sum() / max(1, unique_payers))
    return {
        'highest_spender': highest_spender,
        'most_common_category': most_common_category,
        'avg_share': avg_share,
    }
