from database.db import execute_query, execute_transaction
from datetime import datetime

class Beneficiary:
    @staticmethod
    def create(user_id, account_number, nickname):
        # Validate account number exists
        receiver = execute_query("SELECT id FROM users WHERE account_number = %s", (account_number,), fetch_one=True)
        if not receiver:
            raise ValueError("Target account number does not exist.")
        
        return execute_query(
            "INSERT INTO beneficiaries (user_id, account_number, nickname) VALUES (%s, %s, %s)",
            (user_id, account_number, nickname), commit=True
        )

    @staticmethod
    def get_user_beneficiaries(user_id):
        return execute_query(
            "SELECT * FROM beneficiaries WHERE user_id = %s ORDER BY nickname ASC",
            (user_id,), fetch_all=True
        )

    @staticmethod
    def delete(b_id, user_id):
        return execute_query(
            "DELETE FROM beneficiaries WHERE id = %s AND user_id = %s",
            (b_id, user_id), commit=True
        )


class SavingsGoal:
    @staticmethod
    def create(user_id, goal_name, target_amount, deadline=None):
        return execute_query(
            "INSERT INTO savings_goals (user_id, goal_name, target_amount, deadline) VALUES (%s, %s, %s, %s)",
            (user_id, goal_name, target_amount, deadline), commit=True
        )

    @staticmethod
    def get_user_goals(user_id):
        return execute_query(
            "SELECT * FROM savings_goals WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,), fetch_all=True
        )

    @staticmethod
    def save_towards(goal_id, user_id, amount):
        user = execute_query("SELECT balance FROM users WHERE id = %s", (user_id,), fetch_one=True)
        if not user or float(user['balance']) < float(amount):
            raise ValueError("Insufficient balance to transfer to savings goal.")

        queries_and_params = [
            ("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, user_id)),
            ("UPDATE savings_goals SET current_amount = current_amount + %s WHERE id = %s AND user_id = %s", (amount, goal_id, user_id)),
            ("INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description, reference_number) "
             "VALUES (%s, 'withdrawal', %s, (SELECT balance FROM users WHERE id = %s), %s, %s)",
             (user_id, amount, user_id, f"Saved toward Savings Goal: #{goal_id}", f"SG{goal_id}ADD"))
        ]
        return execute_transaction(queries_and_params)
