CREATE DATABASE IF NOT EXISTS bank_management;
USE bank_management;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    account_type ENUM('savings', 'current', 'business') NOT NULL DEFAULT 'savings',
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    profile_picture VARCHAR(255) DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_frozen TINYINT(1) NOT NULL DEFAULT 0,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_account_number (account_number)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    transaction_type ENUM('deposit', 'withdrawal', 'transfer_in', 'transfer_out') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    balance_after DECIMAL(15, 2) NOT NULL,
    description VARCHAR(255) DEFAULT '',
    reference_number VARCHAR(30) NOT NULL UNIQUE,
    related_account VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_type (transaction_type)
);

CREATE TABLE IF NOT EXISTS transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    reference_number VARCHAR(30) NOT NULL UNIQUE,
    status ENUM('completed', 'failed', 'pending') NOT NULL DEFAULT 'completed',
    note VARCHAR(255) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_sender (sender_id),
    INDEX idx_receiver (receiver_id)
);

CREATE TABLE IF NOT EXISTS login_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent VARCHAR(255) DEFAULT NULL,
    status ENUM('success', 'failed') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_log (user_id)
);

CREATE TABLE IF NOT EXISTS virtual_cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    card_number VARCHAR(19) NOT NULL UNIQUE,
    card_holder VARCHAR(100) NOT NULL,
    expiry_month INT NOT NULL,
    expiry_year INT NOT NULL,
    cvv VARCHAR(4) NOT NULL,
    card_type ENUM('visa', 'mastercard') NOT NULL DEFAULT 'visa',
    card_style ENUM('emerald', 'dark', 'ocean', 'sunset') NOT NULL DEFAULT 'emerald',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    daily_limit DECIMAL(15, 2) NOT NULL DEFAULT 5000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_card (user_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    message VARCHAR(500) NOT NULL,
    notif_type ENUM('transaction', 'security', 'info', 'alert') NOT NULL DEFAULT 'info',
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_notif (user_id),
    INDEX idx_read (is_read)
);

-- Default admin account (password: admin123)
INSERT IGNORE INTO users (full_name, email, phone, password_hash, account_number, account_type, balance, is_admin)
VALUES ('System Admin', 'admin@brainiacbank.com', '+233000000000',
        '$2b$12$placeholder', 'ADMIN000000001', 'savings', 0.00, 1);

CREATE TABLE IF NOT EXISTS loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    interest_rate DECIMAL(5, 2) NOT NULL,
    duration_months INT NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'paid') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_loan_user (user_id)
);

CREATE TABLE IF NOT EXISTS fixed_deposits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    interest_rate DECIMAL(5, 2) NOT NULL,
    duration_months INT NOT NULL,
    maturity_date DATE NOT NULL,
    status ENUM('active', 'matured', 'withdrawn') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_deposit_user (user_id)
);

CREATE TABLE IF NOT EXISTS atm_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    card_type ENUM('visa', 'mastercard') NOT NULL,
    delivery_address VARCHAR(255) NOT NULL,
    status ENUM('pending', 'approved', 'dispatched', 'delivered') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_atm_user (user_id)
);

CREATE TABLE IF NOT EXISTS savings_goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    goal_name VARCHAR(100) NOT NULL,
    target_amount DECIMAL(15, 2) NOT NULL,
    current_amount DECIMAL(15, 2) DEFAULT 0.00,
    deadline DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_savings_user (user_id)
);

CREATE TABLE IF NOT EXISTS beneficiaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_beneficiary_user (user_id)
);

CREATE TABLE IF NOT EXISTS kyc_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    document_type ENUM('national_id', 'passport', 'voters_id', 'utility_bill') NOT NULL,
    document_path VARCHAR(255) NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_kyc_user (user_id)
);

