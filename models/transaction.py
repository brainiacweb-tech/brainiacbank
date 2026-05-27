from database.db import execute_query, get_connection
from utils.helpers import generate_reference
from models.notification import Notification


class Transaction:
    @staticmethod
    def deposit(user_id, amount):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT balance, is_frozen FROM users WHERE id = %s FOR UPDATE", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("Account not found.")
            if user["is_frozen"]:
                raise ValueError("Account is frozen.")

            new_balance = float(user["balance"]) + float(amount)
            ref = generate_reference()

            cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))
            cursor.execute(
                """INSERT INTO transactions
                   (user_id, transaction_type, amount, balance_after, description, reference_number)
                   VALUES (%s, 'deposit', %s, %s, %s, %s)""",
                (user_id, amount, new_balance, f"Deposit of GH₵ {amount:,.2f}", ref),
            )
            conn.commit()
            Notification.notify_transaction(user_id, "deposit", amount, ref)
            return new_balance, ref
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def withdraw(user_id, amount):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT balance, is_frozen FROM users WHERE id = %s FOR UPDATE", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("Account not found.")
            if user["is_frozen"]:
                raise ValueError("Account is frozen.")
            if float(user["balance"]) < float(amount):
                raise ValueError("Insufficient funds.")

            new_balance = float(user["balance"]) - float(amount)
            ref = generate_reference()

            cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))
            cursor.execute(
                """INSERT INTO transactions
                   (user_id, transaction_type, amount, balance_after, description, reference_number)
                   VALUES (%s, 'withdrawal', %s, %s, %s, %s)""",
                (user_id, amount, new_balance, f"Withdrawal of GH₵ {amount:,.2f}", ref),
            )
            conn.commit()
            Notification.notify_transaction(user_id, "withdrawal", amount, ref)
            return new_balance, ref
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def transfer(sender_id, receiver_account, amount, note=""):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, balance, is_frozen, account_number, full_name FROM users WHERE id = %s FOR UPDATE", (sender_id,))
            sender = cursor.fetchone()
            if not sender:
                raise ValueError("Sender account not found.")
            if sender["is_frozen"]:
                raise ValueError("Your account is frozen.")
            if float(sender["balance"]) < float(amount):
                raise ValueError("Insufficient funds.")

            cursor.execute("SELECT id, balance, is_frozen, account_number, full_name FROM users WHERE account_number = %s FOR UPDATE", (receiver_account,))
            receiver = cursor.fetchone()
            if not receiver:
                raise ValueError("Recipient account not found.")
            if receiver["is_frozen"]:
                raise ValueError("Recipient account is frozen.")
            if sender["id"] == receiver["id"]:
                raise ValueError("Cannot transfer to your own account.")

            sender_new = float(sender["balance"]) - float(amount)
            receiver_new = float(receiver["balance"]) + float(amount)
            ref = generate_reference()
            desc = note or f"Transfer to {receiver['full_name']}"

            cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (sender_new, sender_id))
            cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (receiver_new, receiver["id"]))

            cursor.execute(
                """INSERT INTO transactions
                   (user_id, transaction_type, amount, balance_after, description, reference_number, related_account)
                   VALUES (%s, 'transfer_out', %s, %s, %s, %s, %s)""",
                (sender_id, amount, sender_new, desc, ref, receiver_account),
            )
            cursor.execute(
                """INSERT INTO transactions
                   (user_id, transaction_type, amount, balance_after, description, reference_number, related_account)
                   VALUES (%s, 'transfer_in', %s, %s, %s, %s, %s)""",
                (receiver["id"], amount, receiver_new, f"Transfer from {sender['full_name']}", ref, sender["account_number"]),
            )
            cursor.execute(
                """INSERT INTO transfers (sender_id, receiver_id, amount, reference_number, status, note)
                   VALUES (%s, %s, %s, %s, 'completed', %s)""",
                (sender_id, receiver["id"], amount, ref, note),
            )
            conn.commit()
            Notification.notify_transaction(sender_id, "transfer_out", amount, ref)
            Notification.notify_transaction(receiver["id"], "transfer_in", amount, ref)
            return sender_new, ref, receiver["full_name"]
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_transactions(user_id, limit=50, offset=0, txn_type=None, search=None):
        query = "SELECT * FROM transactions WHERE user_id = %s"
        params = [user_id]
        if txn_type and txn_type != "all":
            query += " AND transaction_type = %s"
            params.append(txn_type)
        if search:
            query += " AND (description LIKE %s OR reference_number LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        return execute_query(query, tuple(params), fetch_all=True)

    @staticmethod
    def count_user_transactions(user_id, txn_type=None, search=None):
        query = "SELECT COUNT(*) as total FROM transactions WHERE user_id = %s"
        params = [user_id]
        if txn_type and txn_type != "all":
            query += " AND transaction_type = %s"
            params.append(txn_type)
        if search:
            query += " AND (description LIKE %s OR reference_number LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        result = execute_query(query, tuple(params), fetch_one=True)
        return result["total"] if result else 0

    @staticmethod
    def get_mini_statement(user_id, limit=10):
        return execute_query(
            "SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit), fetch_all=True
        )

    @staticmethod
    def get_monthly_summary(user_id):
        return execute_query(
            """SELECT
                 TO_CHAR(created_at, 'YYYY-MM') as month,
                 transaction_type,
                 SUM(amount) as total,
                 COUNT(*) as count
               FROM transactions
               WHERE user_id = %s
               GROUP BY TO_CHAR(created_at, 'YYYY-MM'), transaction_type
               ORDER BY month DESC
               LIMIT 24""",
            (user_id,), fetch_all=True
        )

    @staticmethod
    def get_all_transactions(limit=100):
        return execute_query(
            """SELECT t.*, u.full_name, u.account_number
               FROM transactions t
               JOIN users u ON t.user_id = u.id
               ORDER BY t.created_at DESC
               LIMIT %s""",
            (limit,), fetch_all=True
        )

    @staticmethod
    def get_for_export(user_id, txn_type=None):
        query = "SELECT * FROM transactions WHERE user_id = %s"
        params = [user_id]
        if txn_type and txn_type != "all":
            query += " AND transaction_type = %s"
            params.append(txn_type)
        query += " ORDER BY created_at DESC"
        return execute_query(query, tuple(params), fetch_all=True)
