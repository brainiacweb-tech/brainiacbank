from database.db import execute_query, execute_transaction
from datetime import datetime, timedelta

class FixedDeposit:
    @staticmethod
    def create(user_id, amount, duration_months, interest_rate=15.0):
        user = execute_query("SELECT balance FROM users WHERE id = %s", (user_id,), fetch_one=True)
        if not user or float(user['balance']) < float(amount):
            raise ValueError("Insufficient balance to open fixed deposit.")

        maturity_date = datetime.now() + timedelta(days=duration_months * 30)

        queries_and_params = [
            ("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, user_id)),
            ("INSERT INTO fixed_deposits (user_id, amount, interest_rate, duration_months, maturity_date, status) "
             "VALUES (%s, %s, %s, %s, %s, 'active')",
             (user_id, amount, interest_rate, duration_months, maturity_date.date())),
            ("INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description, reference_number) "
             "VALUES (%s, 'withdrawal', %s, (SELECT balance FROM users WHERE id = %s), %s, %s)",
             (user_id, amount, user_id, f"Opened Fixed Deposit: {duration_months} mo", f"FD{datetime.now().strftime('%M%S%f')[:10]}"))
        ]
        return execute_transaction(queries_and_params)

    @staticmethod
    def get_user_deposits(user_id):
        return execute_query(
            "SELECT * FROM fixed_deposits WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,), fetch_all=True
        )

    @staticmethod
    def withdraw_matured(fd_id, user_id):
        fd = execute_query("SELECT * FROM fixed_deposits WHERE id = %s AND user_id = %s", (fd_id, user_id), fetch_one=True)
        if not fd or fd['status'] != 'active':
            raise ValueError("Active deposit not found.")

        # Calculate standard payout
        amount = float(fd['amount'])
        interest_rate = float(fd['interest_rate'])
        duration_months = int(fd['duration_months'])
        
        interest_earned = amount * (interest_rate / 100) * (duration_months / 12)
        total_payout = amount + interest_earned

        queries_and_params = [
            ("UPDATE fixed_deposits SET status = 'matured' WHERE id = %s", (fd_id,)),
            ("UPDATE users SET balance = balance + %s WHERE id = %s", (total_payout, user_id)),
            ("INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description, reference_number) "
             "VALUES (%s, 'deposit', %s, (SELECT balance FROM users WHERE id = %s), %s, %s)",
             (user_id, total_payout, user_id, f"Matured FD Payout: Interest GH₵{interest_earned:.2f}", f"FD{fd_id}MAT"))
        ]
        return execute_transaction(queries_and_params)
