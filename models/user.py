import bcrypt
from database.db import execute_query, execute_transaction
from utils.helpers import generate_account_number


class User:
    @staticmethod
    def create(full_name, email, phone, password, account_type="savings"):
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        account_number = generate_account_number()

        while User.find_by_account(account_number):
            account_number = generate_account_number()

        query = """
            INSERT INTO users (full_name, email, phone, password_hash, account_number, account_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        user_id = execute_query(
            query,
            (full_name, email, phone, password_hash, account_number, account_type),
            commit=True,
        )
        return user_id

    @staticmethod
    def find_by_email(email):
        return execute_query(
            "SELECT * FROM users WHERE email = %s", (email,), fetch_one=True
        )

    @staticmethod
    def find_by_id(user_id):
        return execute_query(
            "SELECT * FROM users WHERE id = %s", (user_id,), fetch_one=True
        )

    @staticmethod
    def find_by_account(account_number):
        return execute_query(
            "SELECT * FROM users WHERE account_number = %s",
            (account_number,),
            fetch_one=True,
        )

    @staticmethod
    def verify_password(stored_hash, password):
        return bcrypt.checkpw(password.encode(), stored_hash.encode())

    @staticmethod
    def update_balance(user_id, new_balance):
        execute_query(
            "UPDATE users SET balance = %s WHERE id = %s",
            (new_balance, user_id),
            commit=True,
        )

    @staticmethod
    def update_profile(user_id, full_name, phone):
        execute_query(
            "UPDATE users SET full_name = %s, phone = %s WHERE id = %s",
            (full_name, phone, user_id),
            commit=True,
        )

    @staticmethod
    def update_profile_picture(user_id, filename):
        execute_query(
            "UPDATE users SET profile_picture = %s WHERE id = %s",
            (filename, user_id), commit=True
        )

    @staticmethod
    def change_password(user_id, new_password):
        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        execute_query(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user_id),
            commit=True,
        )

    @staticmethod
    def get_all_users():
        return execute_query(
            "SELECT id, full_name, email, phone, account_number, account_type, balance, is_active, is_frozen, created_at FROM users WHERE is_admin = 0",
            fetch_all=True,
        )

    @staticmethod
    def toggle_freeze(user_id, freeze):
        execute_query(
            "UPDATE users SET is_frozen = %s WHERE id = %s",
            (1 if freeze else 0, user_id),
            commit=True,
        )

    @staticmethod
    def soft_delete(user_id):
        execute_query(
            "UPDATE users SET is_active = 0 WHERE id = %s", (user_id,), commit=True
        )

    @staticmethod
    def activate(user_id):
        execute_query(
            "UPDATE users SET is_active = 1 WHERE id = %s", (user_id,), commit=True
        )
