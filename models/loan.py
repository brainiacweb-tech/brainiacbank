from database.db import execute_query, execute_transaction
from datetime import datetime

class Loan:
    @staticmethod
    def create(user_id, amount, duration_months, interest_rate=12.5):
        # Initial status is pending
        return execute_query(
            """INSERT INTO loans (user_id, amount, interest_rate, duration_months, status)
               VALUES (%s, %s, %s, %s, 'pending')""",
            (user_id, amount, interest_rate, duration_months),
            commit=True
        )

    @staticmethod
    def get_user_loans(user_id):
        return execute_query(
            "SELECT * FROM loans WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,), fetch_all=True
        )

    @staticmethod
    def get_all_loans():
        return execute_query(
            """SELECT l.*, u.full_name, u.account_number 
               FROM loans l JOIN users u ON l.user_id = u.id 
               ORDER BY l.created_at DESC""",
            fetch_all=True
        )

    @staticmethod
    def approve(loan_id):
        # Update status and deposit amount into user account balance
        loan = execute_query("SELECT * FROM loans WHERE id = %s", (loan_id,), fetch_one=True)
        if not loan or loan['status'] != 'pending':
            return False

        queries_and_params = [
            ("UPDATE loans SET status = 'approved' WHERE id = %s", (loan_id,)),
            ("UPDATE users SET balance = balance + %s WHERE id = %s", (loan['amount'], loan['user_id'])),
            ("INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description, reference_number) "
             "VALUES (%s, 'deposit', %s, (SELECT balance FROM users WHERE id = %s), %s, %s)",
             (loan['user_id'], loan['amount'], loan['user_id'], f"Loan Disbursement: #{loan_id}", f"LN{loan_id}DISB"))
        ]
        return execute_transaction(queries_and_params)

    @staticmethod
    def reject(loan_id):
        return execute_query(
            "UPDATE loans SET status = 'rejected' WHERE id = %s",
            (loan_id,), commit=True
        )

    @staticmethod
    def pay_loan(loan_id, user_id):
        loan = execute_query("SELECT * FROM loans WHERE id = %s AND user_id = %s", (loan_id, user_id), fetch_one=True)
        if not loan or loan['status'] != 'approved':
            raise ValueError("No approved loan found.")

        user = execute_query("SELECT balance FROM users WHERE id = %s", (user_id,), fetch_one=True)
        total_repayable = float(loan['amount']) * (1 + float(loan['interest_rate']) / 100)
        
        if float(user['balance']) < total_repayable:
            raise ValueError("Insufficient balance to pay off loan.")

        queries_and_params = [
            ("UPDATE loans SET status = 'paid' WHERE id = %s", (loan_id,)),
            ("UPDATE users SET balance = balance - %s WHERE id = %s", (total_repayable, user_id)),
            ("INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description, reference_number) "
             "VALUES (%s, 'withdrawal', %s, (SELECT balance FROM users WHERE id = %s), %s, %s)",
             (user_id, total_repayable, user_id, f"Repaid Loan: #{loan_id}", f"LN{loan_id}PAY"))
        ]
        return execute_transaction(queries_and_params)
