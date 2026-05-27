from database.db import execute_query


class Notification:
    @staticmethod
    def create(user_id, title, message, notif_type="info"):
        return execute_query(
            """INSERT INTO notifications (user_id, title, message, notif_type)
               VALUES (%s, %s, %s, %s)""",
            (user_id, title, message, notif_type),
            commit=True,
        )

    @staticmethod
    def get_user_notifications(user_id, limit=20):
        return execute_query(
            "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit), fetch_all=True
        )

    @staticmethod
    def get_unread_count(user_id):
        result = execute_query(
            "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,), fetch_one=True
        )
        return result["count"] if result else 0

    @staticmethod
    def mark_read(notif_id, user_id):
        execute_query(
            "UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notif_id, user_id), commit=True
        )

    @staticmethod
    def mark_all_read(user_id):
        execute_query(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s",
            (user_id,), commit=True
        )

    @staticmethod
    def notify_transaction(user_id, txn_type, amount, ref):
        titles = {
            "deposit": "Deposit Received",
            "withdrawal": "Withdrawal Processed",
            "transfer_in": "Money Received",
            "transfer_out": "Transfer Sent",
        }
        title = titles.get(txn_type, "Transaction")
        message = f"GH₵ {amount:,.2f} — Ref: {ref}"
        Notification.create(user_id, title, message, "transaction")

    @staticmethod
    def notify_security(user_id, message):
        Notification.create(user_id, "Security Alert", message, "security")

    @staticmethod
    def notify_card(user_id, message):
        Notification.create(user_id, "Virtual Card", message, "info")
