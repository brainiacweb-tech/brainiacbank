# <img src="static/images/logo.png" align="center" width="40" height="40" /> BrainiacBank

[![Python Flask](https://img.shields.io/badge/Backend-Flask%203.1-blue?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-gold.svg)](#license)
[![Mobile Responsive](https://img.shields.io/badge/Design-KNUST%20System-teal)](static/css/style.css)

BrainiacBank is a high-fidelity, simulated digital banking and financial technology platform built to demonstrate advanced full-stack software engineering, secure transaction persistence, multi-role audit logging, and modern web application development. 

This platform showcases responsive web layout standards inspired by the **KNUST Student Portal / AIM Design System**, offering a clean, high-performance UI/UX optimized for all mobile viewports, including notch displays and safe-area constraints.

> [!NOTE]
> **Educational Simulated Platform Disclaimer**
> BrainiacBank is strictly a simulated portfolio project built for demonstration and software research. It is **not** a real commercial bank or financial institution. No real monetary transactions, credit allocations, or actual banking activities are supported.

---

## 🚀 System Architecture & Key Features

BrainiacBank is split into two core workspaces: the **Client Portal** for financial management and the **Admin Control Center** for audit, regulation, and logistics tracking.

### 👤 Client Portal Features
* **Smart Account Overview**: Interactive dashboard rendering real-time balance metrics, total deposits, and withdrawals with high-contrast statistical metrics.
* **Smart Financial Analytics**: Visual analytics powered by **Chart.js** displaying monthly cashflow (deposits vs. withdrawals).
* **AI Financial Assistant**: A responsive, self-contained AI-powered chat helper (`initAIChatbot()`) that provides simulated expense predictions, transaction scans, and saving advice.
* **Virtual Card Management**: Dynamic virtual card creation (Visa / Mastercard) with customized aesthetic templates (Emerald, Sunset, Ocean, Dark). Supports instant freeze/unfreeze controls.
* **Order ATM Card**: Multi-channel physical card shipping logistics tracker with customizable networks (Visa/Mastercard) and delivery addresses.
* **KYC Document Center**: Document submission module supporting interactive drag-and-drop photo uploads and profile updates.
* **Fixed Deposit Portfolios**: Secure investment vaults with custom durations and standard simulated **12.5% p.a. guaranteed interest**.
* **Utilities & Airtime**: Simulated top-ups for major networks (MTN, Telecel, AT) and bills (DSTV, ECG, GWCL).
* **Atomic Transactions**: Instant transfers to other BrainiacBank clients using secure receiver verification to avoid false transfers.

### 🛡️ Admin Control Center Features
* **Account Moderation**: Freeze or unfreeze customer accounts instantly to prevent unauthorized access or system abuse.
* **Credit & Loan Disbursements**: Review, approve, or reject loan applications with flat-rate interest calculations.
* **KYC Validation Panel**: Integrated file viewer to verify customer-submitted government identity documents before system upgrade.
* **ATM Logistics Dispatch**: Manage physical debit card shipping pipelines (Processing, Approved, Dispatched, Delivered).
* **Global Audit Logs**: Live transaction ledger monitoring every cashflow event across the entire system.

---

## 🔒 Hardened Security Architecture

The platform implements industry-standard "secure-by-design" practices to protect user sessions and transactional integrity:

1. **Atomic Database Transactions**: All transfers utilize multi-query transactions with rollback mechanisms. If a receiver credit fails, the sender debit is rolled back, preventing system balance drift.
2. **Cryptographic Protection**: Standard user authentication uses secure passwords hashed using **bcrypt** (12 work factors).
3. **MIME-Sniffing Prevention**: Blocks browsers from executing custom scripts uploaded as images or files.
4. **Anti-Clickjacking Barriers**: Employs `X-Frame-Options: DENY` headers to completely prevent framing.
5. **Anti-Cross-Site Scripting (XSS)**: Active `X-XSS-Protection` filters and strict Content Security Policies (CSP) to restrict scripts and fonts only to whitelisted sources.
6. **CSRF & Safe Session Policies**: Secure HTTP-only cookies with `SameSite=Lax` policies to shield cookies from cross-site access.

---

## 🛠️ Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Frontend** | HTML5, CSS3, Vanilla ES6+ | Premium aesthetics, glassmorphism, responsive grid systems, safe-area-insets, and notch support. |
| **Backend** | Python Flask 3.1 | Modular Blueprints, custom decorators for role access (`auth_required`, `admin_required`), context processors. |
| **Database** | PostgreSQL | Supabase-hosted cloud PostgreSQL cluster utilizing the `psycopg2` Threaded Connection Pool. |
| **Analytics** | Chart.js 4.4 | Smooth visual canvas charts rendering deposits/withdrawals cashflows. |
| **Security** | bcrypt & Secure Headers | Session security with HTTP-only parameters and hardened CSP headers. |

---

## 📁 Repository Structure

```
Bank/
├── app.py                  # Entry point (Flask application server)
├── config.py               # Application configurations (database & security settings)
├── .env                    # Local environment secrets and variables
├── requirements.txt        # Python package dependencies
├── Procfile                # Heroku/Render production execution script
├── database/
│   ├── db.py               # Threaded Connection pool manager & sql execute functions
│   └── schema.sql          # PostgreSQL database schema tables & migrations
├── models/
│   ├── user.py             # User accounts authentication & profiles CRUD
│   └── transaction.py      # Transactions processing, transfers, & fixed deposits
├── routes/
│   ├── auth.py             # Security gateways: Login, Signup, Logout
│   ├── main.py             # Client services, virtual cards, chatbot, profile configurations
│   └── admin.py            # Administrative logs, KYC updates, ATM dispatches, account freezing
├── templates/
│   ├── base.html           # Base layout containing unified mobile nav, sidebar, & safe areas
│   ├── index.html          # Public landing page with credit card graphics
│   ├── dashboard.html      # Client overview dashboard
│   ├── cards.html          # Virtual debit card creations
│   ├── fixed_deposits.html # Savings portfolios
│   └── admin/
│       ├── dashboard.html  # Administrative command deck
│       └── ...             
├── static/
│   ├── css/style.css       # Complete vanilla responsive design stylesheet
│   └── js/app.js           # Interactive triggers, drag-and-drop handlers, & chatbot core
```

---

## 💻 Database Schema Design

The system runs on five core tables designed with cascading foreign keys to secure data integrity:

```mermaid
erDiagram
    users ||--o{ transactions : owns
    users ||--o{ virtual_cards : manages
    users ||--o{ loans : applies
    users ||--o{ kyc_documents : submits
    users ||--o{ atm_requests : orders

    users {
        int id PK
        string full_name
        string email UK
        string password_hash
        string phone
        string account_number UK
        string account_type
        decimal balance
        boolean is_admin
        boolean is_frozen
        timestamp created_at
    }

    transactions {
        int id PK
        int user_id FK
        string transaction_type
        decimal amount
        string reference_number UK
        timestamp created_at
    }

    virtual_cards {
        int id PK
        int user_id FK
        string card_number UK
        string card_holder
        string expiry_date
        string cvv
        string card_type
        string design_theme
        boolean is_active
        timestamp created_at
    }

    loans {
        int id PK
        int user_id FK
        decimal amount
        decimal interest_rate
        int duration_months
        string status
        timestamp created_at
    }

    kyc_documents {
        int id PK
        int user_id FK
        string document_type
        string document_path
        string status
        timestamp created_at
    }
```

---

## ⚙️ Installation & Local Setup

### 📋 Prerequisites
* **Python 3.10+**
* **Git**
* Cloud or local **PostgreSQL** instance

### 🛠️ Execution Pipeline

1. **Clone the Repository**
   ```bash
   git clone https://github.com/brainiacweb-tech/brainiacbank.git
   cd brainiacbank
   ```

2. **Configure Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Core Requirements**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables Configuration**
   Create a `.env` file in the root directory and add the following connection keys:
   ```env
   SECRET_KEY=generate-a-strong-secret-key-string
   DATABASE_URL=postgresql://user:password@host:port/dbname
   ```
   *(Migrations are automatically applied on server initialization via `run_migrations()` inside `db.py`)*

5. **Start Dev Server**
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://127.0.0.1:5000`.

---

## 🔑 Administrative Access

To test the **Admin Control Center** capabilities, log in with these default administrative credentials:

* **Email**: `admin@bank.com`
* **Password**: `admin123`

---

## 📄 License
This project is licensed under the **MIT License**. Feel free to use, modify, and distribute for portfolio and educational goals.

*Developed with passion by **Francis Kusi** — Ghana.*
