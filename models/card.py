import random
from database.db import execute_query


class VirtualCard:
    @staticmethod
    def generate_card_number():
        prefix = random.choice(["4", "5"])
        number = prefix + "".join([str(random.randint(0, 9)) for _ in range(15)])
        formatted = " ".join([number[i:i+4] for i in range(0, 16, 4)])
        return formatted

    @staticmethod
    def generate_cvv():
        return str(random.randint(100, 999))

    @staticmethod
    def create(user_id, card_holder, card_type="visa", card_style="emerald"):
        card_number = VirtualCard.generate_card_number()
        while VirtualCard.find_by_number(card_number.replace(" ", "")):
            card_number = VirtualCard.generate_card_number()

        cvv = VirtualCard.generate_cvv()
        from datetime import datetime
        now = datetime.now()
        expiry_month = now.month
        expiry_year = now.year + 3

        return execute_query(
            """INSERT INTO virtual_cards
               (user_id, card_number, card_holder, expiry_month, expiry_year, cvv, card_type, card_style)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, card_number, card_holder, expiry_month, expiry_year, cvv, card_type, card_style),
            commit=True,
        )

    @staticmethod
    def find_by_number(card_number):
        return execute_query(
            "SELECT * FROM virtual_cards WHERE REPLACE(card_number, ' ', '') = %s",
            (card_number,), fetch_one=True
        )

    @staticmethod
    def get_user_cards(user_id):
        return execute_query(
            "SELECT * FROM virtual_cards WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,), fetch_all=True
        )

    @staticmethod
    def get_by_id(card_id, user_id):
        return execute_query(
            "SELECT * FROM virtual_cards WHERE id = %s AND user_id = %s",
            (card_id, user_id), fetch_one=True
        )

    @staticmethod
    def toggle_active(card_id, user_id, active):
        execute_query(
            "UPDATE virtual_cards SET is_active = %s WHERE id = %s AND user_id = %s",
            (1 if active else 0, card_id, user_id), commit=True
        )

    @staticmethod
    def delete(card_id, user_id):
        execute_query(
            "DELETE FROM virtual_cards WHERE id = %s AND user_id = %s",
            (card_id, user_id), commit=True
        )

    @staticmethod
    def update_limit(card_id, user_id, limit_amount):
        execute_query(
            "UPDATE virtual_cards SET daily_limit = %s WHERE id = %s AND user_id = %s",
            (limit_amount, card_id, user_id), commit=True
        )
