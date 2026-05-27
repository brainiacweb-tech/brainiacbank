# BrainiacBank — Modern Bank Management System

A full-stack banking web application built with Flask, MySQL, and vanilla JavaScript featuring a professional fintech-style dashboard UI.

## Features

- **User Authentication** — Secure registration, login, logout with bcrypt password hashing
- **Dashboard** — Real-time balance, deposits/withdrawals stats, Chart.js analytics
- **Deposit & Withdraw** — With validation, overdraft protection, transaction logging
- **Money Transfers** — Atomic database transactions with rollback, recipient verification
- **Transaction History** — Search, filter by type, pagination
- **Admin Panel** — Manage users, freeze/deactivate accounts, view all transactions
- **Profile Management** — Update info, change password
- **Responsive Design** — Mobile-friendly with sidebar navigation
- **Modern UI** — Glassmorphism, animations, gold/navy color palette

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Frontend  | HTML5, CSS3, Vanilla JavaScript   |
| Backend   | Python Flask                      |
| Database  | MySQL                             |
| Charts    | Chart.js                          |
| Auth      | Flask Sessions + bcrypt           |
| Icons     | Inline SVG                        |

## Project Structure

```
Bank/
├── app.py                  # Flask application entry point
├── config.py               # Configuration (env vars)
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── database/
│   ├── db.py               # Connection pool & query helpers
│   └── schema.sql          # MySQL schema + seed data
├── models/
│   ├── user.py             # User model (CRUD, auth)
│   └── transaction.py      # Transaction model (deposit, withdraw, transfer)
├── routes/
│   ├── auth.py             # Login, register, logout
│   ├── main.py             # Dashboard, banking operations, profile
│   └── admin.py            # Admin panel routes
├── templates/
│   ├── base.html           # Base template with navbar & sidebar
│   ├── index.html          # Landing page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── dashboard.html      # User dashboard
│   ├── deposit.html        # Deposit page
│   ├── withdraw.html       # Withdrawal page
│   ├── transfer.html       # Transfer page
│   ├── transactions.html   # Transaction history
│   ├── profile.html        # Profile settings
│   └── admin/
│       ├── dashboard.html  # Admin dashboard
│       └── transactions.html
├── static/
│   ├── css/style.css       # Complete stylesheet
│   └── js/app.js           # Client-side JavaScript
└── utils/
    └── helpers.py          # Decorators, formatters, generators
```

## Installation

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip

### Setup

1. **Clone and enter directory**
   ```bash
   cd Bank
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MySQL**
   - Start MySQL server
   - Run the schema file:
     ```bash
     mysql -u root -p < database/schema.sql
     ```
   - Or execute it from MySQL Workbench

5. **Configure environment**
   Edit `.env` with your MySQL credentials:
   ```
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=bank_management
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open browser**
   Navigate to `http://localhost:5000`

## Default Admin Account

- **Email:** admin@bank.com
- **Password:** admin123

## Security Features

- Bcrypt password hashing
- Session-based authentication
- Parameterized SQL queries (SQL injection prevention)
- Input validation on both client and server
- Protected routes with decorators
- Account freeze/deactivation controls
- Login attempt logging

## Future Improvements

- Email notifications (SMTP integration)
- PDF receipt generation
- Two-factor authentication
- Dark mode toggle
- QR code transfers
- Export transactions to CSV
- Real-time WebSocket notifications
