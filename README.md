# 💸 Spendly — Smart Expense Manager

A **full-stack Flask web app** for tracking, splitting, and analyzing group expenses with AI-powered insights.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange)

---

## ✨ Features

- 📊 **Dashboard** — real-time expense summaries & charts
- 💳 **Expense Tracking** — add, edit, delete expenses with category tagging
- 👥 **Group Splits** — equal, exact, or percentage-based splits across members
- 🤝 **Settlements** — track who owes whom and settle balances
- 📈 **Analytics** — spending trends, category breakdowns, date-range filters
- 🔮 **Predictions** — AI-powered spend forecasts
- 🔐 **Auth** — secure login / registration with Flask-Login
- 🎨 **Dark UI** — glassmorphism design with indigo-violet brand theme

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/Spendly.git
cd Spendly
```

### 2. Set up virtual environment
```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Create a `.env` file inside `backend/`:
```env
SECRET_KEY=your-secret-key-here
```

### 5. Run the app
```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000) 🎉

---

## 📁 Project Structure

```
Spendly/
└── backend/
    ├── app/
    │   ├── __init__.py        # App factory
    │   ├── models.py          # SQLAlchemy models
    │   ├── routes.py          # Main routes (dashboard, profile)
    │   ├── auth.py            # Login / register
    │   ├── expenses.py        # Expense CRUD + splits
    │   ├── analytics.py       # Analytics & predictions
    │   ├── members.py         # Member management
    │   ├── settlements.py     # Settlement tracking
    │   ├── templates/         # Jinja2 HTML templates
    │   └── static/            # CSS, JS, images
    ├── requirements.txt
    ├── config.py
    └── run.py                 # Entry point
```

---

## 🛠️ Tech Stack

| Layer      | Technology |
|------------|-----------|
| Backend    | Flask 3, Flask-Login, Flask-SQLAlchemy |
| Database   | SQLite (dev) |
| Frontend   | Bootstrap 5, Vanilla JS, Chart.js |
| Fonts      | Plus Jakarta Sans, Inter |
| Analytics  | Pandas, NumPy |

---

## 📄 License

MIT License — feel free to use and modify.
