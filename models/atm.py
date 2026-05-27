from database.db import execute_query

class AtmRequest:
    @staticmethod
    def create(user_id, card_type, delivery_address):
        return execute_query(
            """INSERT INTO atm_requests (user_id, card_type, delivery_address, status)
               VALUES (%s, %s, %s, 'pending')""",
            (user_id, card_type, delivery_address),
            commit=True
        )

    @staticmethod
    def get_user_requests(user_id):
        return execute_query(
            "SELECT * FROM atm_requests WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,), fetch_all=True
        )

    @staticmethod
    def get_all_requests():
        return execute_query(
            """SELECT a.*, u.full_name, u.account_number 
               FROM atm_requests a JOIN users u ON a.user_id = u.id 
               ORDER BY a.created_at DESC""",
            fetch_all=True
        )

    @staticmethod
    def update_status(req_id, status):
        return execute_query(
            "UPDATE atm_requests SET status = %s WHERE id = %s",
            (status, req_id), commit=True
        )
