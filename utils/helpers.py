import random
import string
import uuid
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash


def generate_account_number():
    prefix = "BNK"
    digits = "".join(random.choices(string.digits, k=10))
    return f"{prefix}{digits}"


def generate_reference():
    return f"TXN{uuid.uuid4().hex[:12].upper()}"


def format_currency(amount):
    return f"GH₵ {amount:,.2f}"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        if not session.get("is_admin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated
