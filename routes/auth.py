import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from database.db import execute_query

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        account_type = request.form.get("account_type", "savings")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not full_name or len(full_name) < 2:
            errors.append("Full name is required.")
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Valid email is required.")
        clean_phone = phone.strip().replace(" ", "").replace("-", "")
        if clean_phone.startswith("0"):
            clean_phone = "+233" + clean_phone[1:]
        elif not clean_phone.startswith("+"):
            clean_phone = "+233" + clean_phone

        if not re.match(r"^\+233\d{9}$", clean_phone):
            errors.append("Valid Ghanaian phone number (+233 followed by 9 digits) is required.")

        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if User.find_by_email(email):
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html")

        try:
            User.create(full_name, email, clean_phone, password, account_type)
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.find_by_email(email)

        if not user or not User.verify_password(user["password_hash"], password):
            try:
                if user:
                    execute_query(
                        "INSERT INTO login_logs (user_id, ip_address, user_agent, status) VALUES (%s, %s, %s, 'failed')",
                        (user["id"], request.remote_addr, str(request.user_agent)[:255]),
                        commit=True,
                    )
            except Exception:
                pass
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        if not user["is_active"]:
            flash("This account has been deactivated.", "danger")
            return render_template("login.html")

        if user["is_frozen"]:
            flash("This account is frozen. Contact support.", "warning")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        session["is_admin"] = bool(user["is_admin"])
        session["account_number"] = user["account_number"]

        try:
            execute_query(
                "INSERT INTO login_logs (user_id, ip_address, user_agent, status) VALUES (%s, %s, %s, 'success')",
                (user["id"], request.remote_addr, str(request.user_agent)[:255]),
                commit=True,
            )
        except Exception:
            pass

        if user["is_admin"]:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))
