from .utils import load_expenses_df


def predict_future_expense():
    df = load_expenses_df()
    if df.empty or 'amount' not in df.columns:
        return 0.0
    return float(df['amount'].mean())
