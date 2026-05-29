import os
import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, Response, current_app
from models.user import User
from models.transaction import Transaction
from models.card import VirtualCard
from models.notification import Notification
from models.loan import Loan
from models.deposit_mgmt import FixedDeposit
from models.atm import AtmRequest
from models.extra import Beneficiary, SavingsGoal
from database.db import execute_query, execute_transaction
from utils.helpers import login_required, format_currency, client_required
from werkzeug.utils import secure_filename


main_bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.route("/health")
def health():
    """Health check — shows DB connection status."""
    import traceback
    status = {}
    url = os.getenv("DATABASE_URL", "")
    status["env"] = {
        "DATABASE_URL": f"postgresql://...{url[-20:]}" if url else "(not set)",
        "PORT": os.getenv("PORT", "(not set)"),
    }
    try:
        from database.db import get_connection, release_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        cur.close()
        release_connection(conn)
        status["db"] = "Connected"
        status["pg_version"] = version
    except Exception as e:
        status["db"] = f"FAILED: {e}"
        status["traceback"] = traceback.format_exc()
    return jsonify(status)


@main_bp.route("/")
def index():
    if "user_id" in session:
        if session.get("is_admin"):
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main_bp.route("/landing")
def landing_preview():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = User.find_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    if user.get("is_admin"):
        return redirect(url_for("admin.dashboard"))

    recent = Transaction.get_mini_statement(user["id"], 5)
    monthly = Transaction.get_monthly_summary(user["id"])
    notif_count = Notification.get_unread_count(user["id"])
    cards = VirtualCard.get_user_cards(user["id"])

    total_deposits = sum(
        float(t["total"]) for t in monthly if t["transaction_type"] in ("deposit", "transfer_in")
    )
    total_withdrawals = sum(
        float(t["total"]) for t in monthly if t["transaction_type"] in ("withdrawal", "transfer_out")
    )

    return render_template(
        "dashboard.html",
        user=user,
        recent_transactions=recent,
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        monthly_data=monthly,
        notif_count=notif_count,
        cards=cards,
    )


@main_bp.route("/deposit", methods=["GET", "POST"])
@client_required
def deposit():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            if amount <= 0:
                flash("Amount must be positive.", "danger")
                return render_template("deposit.html", user=user, notif_count=notif_count)
            if amount > 1000000:
                flash("Maximum single deposit is GH₵ 1,000,000.", "danger")
                return render_template("deposit.html", user=user, notif_count=notif_count)

            new_balance, ref = Transaction.deposit(user["id"], amount)
            flash(f"Deposited GH₵ {amount:,.2f} successfully. Ref: {ref}", "success")
            return redirect(url_for("main.dashboard"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Deposit failed. Please try again.", "danger")

    return render_template("deposit.html", user=user, notif_count=notif_count)


@main_bp.route("/withdraw", methods=["GET", "POST"])
@client_required
def withdraw():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            if amount <= 0:
                flash("Amount must be positive.", "danger")
                return render_template("withdraw.html", user=user, notif_count=notif_count)

            new_balance, ref = Transaction.withdraw(user["id"], amount)
            flash(f"Withdrew GH₵ {amount:,.2f} successfully. Ref: {ref}", "success")
            return redirect(url_for("main.dashboard"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Withdrawal failed. Please try again.", "danger")

    return render_template("withdraw.html", user=user, notif_count=notif_count)


@main_bp.route("/transfer", methods=["GET", "POST"])
@client_required
def transfer():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    if request.method == "POST":
        try:
            receiver_account = request.form.get("receiver_account", "").strip()
            amount = float(request.form.get("amount", 0))
            note = request.form.get("note", "").strip()

            if amount <= 0:
                flash("Amount must be positive.", "danger")
                return render_template("transfer.html", user=user, notif_count=notif_count)

            new_balance, ref, receiver_name = Transaction.transfer(
                user["id"], receiver_account, amount, note
            )
            flash(f"Transferred GH₵ {amount:,.2f} to {receiver_name}. Ref: {ref}", "success")
            return redirect(url_for("main.dashboard"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Transfer failed. Please try again.", "danger")

    return render_template("transfer.html", user=user, notif_count=notif_count)


@main_bp.route("/transactions")
@login_required
def transactions():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    page = request.args.get("page", 1, type=int)
    txn_type = request.args.get("type", "all")
    search = request.args.get("search", "").strip()
    per_page = 15

    total = Transaction.count_user_transactions(user["id"], txn_type, search)
    txns = Transaction.get_user_transactions(
        user["id"], per_page, (page - 1) * per_page, txn_type, search
    )
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "transactions.html",
        user=user,
        transactions=txns,
        page=page,
        total_pages=total_pages,
        txn_type=txn_type,
        search=search,
        notif_count=notif_count,
    )


@main_bp.route("/transactions/download")
@login_required
def download_transactions():
    user = User.find_by_id(session["user_id"])
    txn_type = request.args.get("type", "all")
    txns = Transaction.get_for_export(user["id"], txn_type)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Description", "Amount (GH₵)", "Balance After (GH₵)", "Reference"])
    for t in txns:
        writer.writerow([
            t["created_at"].strftime("%Y-%m-%d"),
            t["transaction_type"].upper().replace('_', ' '),
            t["description"],
            f"{t['amount']:.2f}",
            f"{t['balance_after']:.2f}",
            t["reference_number"],
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=transactions_{user['account_number']}.csv"}
    )


@main_bp.route("/transactions/download-excel")
@login_required
def download_transactions_excel():
    from datetime import datetime
    user = User.find_by_id(session["user_id"])
    txn_type = request.args.get("type", "all")
    txns = Transaction.get_for_export(user["id"], txn_type)

    html = f"""<html xmlns:o="urn:schemas-microsoft-xml-office:office" xmlns:x="urn:schemas-microsoft-xml-office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<!--[if gte mso 9]>
<xml>
 <x:ExcelWorkbook>
  <x:ExcelWorksheets>
   <x:ExcelWorksheet>
    <x:Name>BrainiacBank Statement</x:Name>
    <x:WorksheetOptions>
     <x:DisplayGridlines/>
    </x:WorksheetOptions>
   </x:ExcelWorksheet>
  </x:ExcelWorksheets>
 </x:ExcelWorkbook>
</xml>
<![endif]-->
<style>
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background-color: #0b0f19;
    color: #e5e7eb;
    margin: 0;
    padding: 20px;
  }}
  .logo {{
    font-size: 18pt;
    font-weight: bold;
    color: #9CF027;
    font-family: 'Montserrat', sans-serif;
  }}
  .brand-sub {{
    font-size: 10pt;
    color: #9ca3af;
  }}
  .info-table td {{
    padding: 4px 10px;
    font-size: 10pt;
    border: none !important;
  }}
  .info-label {{
    font-weight: bold;
    color: #9ca3af;
  }}
  .info-value {{
    color: #ffffff;
  }}
  .statement-table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 15px;
  }}
  .statement-table th {{
    background-color: #0b0f19;
    color: #9CF027;
    font-weight: bold;
    border: 1.5px solid #1f2937;
    padding: 10px 12px;
    font-size: 10pt;
    text-align: left;
  }}
  .statement-table td {{
    border: 1.5px solid #1f2937;
    padding: 8px 12px;
    font-size: 10pt;
    color: #d1d5db;
    vertical-align: middle;
  }}
  .badge-deposit {{
    color: #10b981;
    font-weight: bold;
  }}
  .badge-withdrawal {{
    color: #f43f5e;
    font-weight: bold;
  }}
  .number-format {{
    mso-number-format: "GH₵\\ \\#\\,\\#\\#0\\.00";
    text-align: right;
  }}
  .date-format {{
    mso-number-format: "YYYY\\-MM\\-DD";
    text-align: left;
  }}
  .ref-format {{
    font-family: monospace;
    color: #9ca3af;
  }}
</style>
</head>
<body>

  <table>
    <tr>
      <td colspan="6" style="border:none; padding: 0;"><div class="logo">BRAINIAC BANK</div></td>
    </tr>
    <tr>
      <td colspan="6" style="border:none; padding: 0;"><div class="brand-sub">Premium Statement Ledger &bull; Secure Banking Experience</div></td>
    </tr>
  </table>

  <br>

  <table class="info-table">
    <tr>
      <td class="info-label">Account Holder:</td>
      <td class="info-value">{user['full_name']}</td>
      <td class="info-label">Account Number:</td>
      <td class="info-value" style="mso-number-format:'@';">{user['account_number']}</td>
    </tr>
    <tr>
      <td class="info-label">Current Balance:</td>
      <td class="info-value" style="font-weight:bold; color:#9CF027; mso-number-format:'GH₵\\ \\#\\,\\#\\#0\\.00';">{user['balance']}</td>
      <td class="info-label">Export Date:</td>
      <td class="info-value">{datetime.now().strftime('%Y-%m-%d')}</td>
    </tr>
  </table>

  <br>

  <table class="statement-table">
    <thead>
      <tr>
        <th width="120" style="width:120px;">DATE</th>
        <th width="140" style="width:140px;">REFERENCE</th>
        <th width="120" style="width:120px;">TYPE</th>
        <th width="240" style="width:240px;">DESCRIPTION</th>
        <th width="130" style="width:130px; text-align: right;">AMOUNT</th>
        <th width="150" style="width:150px; text-align: right;">BALANCE AFTER</th>
      </tr>
    </thead>
    <tbody>"""

    for t in txns:
        is_credit = t["transaction_type"] in ["deposit", "transfer_in"]
        badge_class = "badge-deposit" if is_credit else "badge-withdrawal"
        txn_type_display = t["transaction_type"].upper().replace('_', ' ')
        formatted_date = t["created_at"].strftime("%Y-%m-%d")
        amount_prefix = "+" if is_credit else "-"
        
        html += f"""
      <tr>
        <td class="date-format" style="width:120px;">{formatted_date}</td>
        <td class="ref-format" style="width:140px; mso-number-format:'@';">{t['reference_number']}</td>
        <td class="{badge_class}" style="width:120px;">{txn_type_display}</td>
        <td style="width:240px;">{t['description']}</td>
        <td class="number-format" style="width:130px; text-align: right; color: {'#10b981' if is_credit else '#f43f5e'};">{amount_prefix}{t['amount']:.2f}</td>
        <td class="number-format" style="width:150px; text-align: right; font-weight: bold;">{t['balance_after']:.2f}</td>
      </tr>"""

    html += f"""
    </tbody>
  </table>

  <br>
  <table>
    <tr>
      <td colspan="6" style="border:none; text-align:center; color:#9ca3af; font-size:9pt; padding-top:20px;">
        Developed by Francis Kusi &bull; Secure Financial Ledger
      </td>
    </tr>
  </table>

</body>
</html>"""

    return Response(
        html,
        mimetype="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=transactions_{user['account_number']}.xls"}
    )


@main_bp.route("/cards")
@login_required
def cards():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    user_cards = VirtualCard.get_user_cards(user["id"])
    return render_template("cards.html", user=user, cards=user_cards, notif_count=notif_count)


@main_bp.route("/cards/create", methods=["POST"])
@login_required
def create_card():
    user = User.find_by_id(session["user_id"])
    card_type = request.form.get("card_type", "visa")
    card_style = request.form.get("card_style", "emerald")

    existing = VirtualCard.get_user_cards(user["id"])
    if len(existing) >= 3:
        flash("Maximum 3 virtual cards allowed.", "danger")
        return redirect(url_for("main.cards"))

    VirtualCard.create(user["id"], user["full_name"], card_type, card_style)
    Notification.notify_card(user["id"], f"New {card_type.title()} virtual card created.")
    flash("Virtual card created successfully!", "success")
    return redirect(url_for("main.cards"))


@main_bp.route("/cards/<int:card_id>/toggle", methods=["POST"])
@login_required
def toggle_card(card_id):
    card = VirtualCard.get_by_id(card_id, session["user_id"])
    if card:
        new_state = not card["is_active"]
        VirtualCard.toggle_active(card_id, session["user_id"], new_state)
        state_text = "activated" if new_state else "frozen"
        flash(f"Card {state_text}.", "success")
    return redirect(url_for("main.cards"))


@main_bp.route("/cards/<int:card_id>/delete", methods=["POST"])
@login_required
def delete_card(card_id):
    VirtualCard.delete(card_id, session["user_id"])
    flash("Card deleted.", "success")
    return redirect(url_for("main.cards"))


@main_bp.route("/notifications")
@login_required
def notifications():
    user = User.find_by_id(session["user_id"])
    notifs = Notification.get_user_notifications(user["id"], 50)
    notif_count = Notification.get_unread_count(user["id"])
    return render_template("notifications.html", user=user, notifications=notifs, notif_count=notif_count)


@main_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def read_all_notifications():
    Notification.mark_all_read(session["user_id"])
    return redirect(url_for("main.notifications"))


@main_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def read_notification(notif_id):
    Notification.mark_read(notif_id, session["user_id"])
    return jsonify({"ok": True})


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            full_name = request.form.get("full_name", "").strip()
            phone = request.form.get("phone", "").strip()
            if full_name and phone:
                User.update_profile(user["id"], full_name, phone)
                session["user_name"] = full_name
                flash("Profile updated.", "success")
            else:
                flash("Name and phone are required.", "danger")

        elif action == "change_password":
            current = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")

            if not User.verify_password(user["password_hash"], current):
                flash("Current password is incorrect.", "danger")
            elif len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "danger")
            elif new_pw != confirm:
                flash("New passwords do not match.", "danger")
            else:
                User.change_password(user["id"], new_pw)
                Notification.notify_security(user["id"], "Your password was changed.")
                flash("Password changed successfully.", "success")

        elif action == "upload_photo":
            file = request.files.get("profile_pic")
            if file and allowed_file(file.filename):
                upload_dir = os.path.join(current_app.root_path, "static", "uploads")
                os.makedirs(upload_dir, exist_ok=True)
                filename = f"user_{user['id']}_{secure_filename(file.filename)}"
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                User.update_profile_picture(user["id"], filename)
                flash("Profile photo updated.", "success")
            else:
                flash("Invalid file. Use PNG, JPG, or GIF.", "danger")

        return redirect(url_for("main.profile"))

    return render_template("profile.html", user=user, notif_count=notif_count)


@main_bp.route("/api/verify-account/<account_number>")
@login_required
def verify_account(account_number):
    user = User.find_by_account(account_number)
    if user and user["is_active"] and not user["is_frozen"]:
        return jsonify({"found": True, "name": user["full_name"]})
    return jsonify({"found": False})


@main_bp.route("/api/chart-data")
@login_required
def chart_data():
    monthly = Transaction.get_monthly_summary(session["user_id"])
    labels = sorted(set(m["month"] for m in monthly))[-6:]
    deposits = []
    withdrawals = []
    for label in labels:
        dep = sum(float(m["total"]) for m in monthly if m["month"] == label and m["transaction_type"] in ("deposit", "transfer_in"))
        wit = sum(float(m["total"]) for m in monthly if m["month"] == label and m["transaction_type"] in ("withdrawal", "transfer_out"))
        deposits.append(dep)
        withdrawals.append(wit)
    return jsonify({"labels": labels, "deposits": deposits, "withdrawals": withdrawals})


@main_bp.route("/api/notifications")
@login_required
def api_notifications():
    notifs = Notification.get_user_notifications(session["user_id"], 10)
    count = Notification.get_unread_count(session["user_id"])
    return jsonify({
        "count": count,
        "notifications": [{
            "id": n["id"],
            "title": n["title"],
            "message": n["message"],
            "type": n["notif_type"],
            "is_read": n["is_read"],
            "created_at": n["created_at"].strftime("%b %d, %H:%M"),
        } for n in notifs]
    })


# ==========================================
# ADVANCED SERVICES: LOAN APPLICATION SYSTEM
# ==========================================
@main_bp.route("/loans", methods=["GET", "POST"])
@login_required
def loans():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    user_loans = Loan.get_user_loans(user["id"])
    
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            duration = int(request.form.get("duration", 6))
            if amount <= 100 or amount > 100000:
                flash("Loan amount must be between GH₵ 100 and GH₵ 100,000.", "danger")
                return redirect(url_for("main.loans"))
            
            Loan.create(user["id"], amount, duration)
            Notification.notify_info(user["id"], f"Your loan request for GH₵ {amount:,.2f} is submitted for KYC approval.")
            flash("Loan application submitted successfully! Pending Admin KYC review.", "success")
            return redirect(url_for("main.loans"))
        except Exception as e:
            flash(f"Loan application failed: {str(e)}", "danger")

    return render_template("loans.html", user=user, loans=user_loans, notif_count=notif_count)


@main_bp.route("/loans/<int:loan_id>/pay", methods=["POST"])
@login_required
def pay_loan(loan_id):
    try:
        Loan.pay_loan(loan_id, session["user_id"])
        flash("Loan paid off successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Could not process repayment. Try again.", "danger")
    return redirect(url_for("main.loans"))


# ==========================================
# FIXED DEPOSIT INVESTMENT SYSTEM
# ==========================================
@main_bp.route("/fixed-deposits", methods=["GET", "POST"])
@login_required
def fixed_deposits():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    user_fds = FixedDeposit.get_user_deposits(user["id"])

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            duration = int(request.form.get("duration", 3))
            
            if amount <= 50:
                flash("Minimum investment is GH₵ 50.00.", "danger")
                return redirect(url_for("main.fixed_deposits"))
            
            FixedDeposit.create(user["id"], amount, duration)
            Notification.notify_info(user["id"], f"Fixed Deposit of GH₵ {amount:,.2f} created successfully.")
            flash("Fixed Deposit account opened successfully!", "success")
            return redirect(url_for("main.fixed_deposits"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Failed to open investment account. Try again.", "danger")

    return render_template("fixed_deposits.html", user=user, fixed_deposits=user_fds, notif_count=notif_count)


@main_bp.route("/fixed-deposits/<int:fd_id>/withdraw", methods=["POST"])
@login_required
def withdraw_fd(fd_id):
    try:
        FixedDeposit.withdraw_matured(fd_id, session["user_id"])
        flash("Investment funds withdrawn successfully with high-yield interest!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Could not withdraw. Try again.", "danger")
    return redirect(url_for("main.fixed_deposits"))


# ==========================================
# ATM CARD REQUEST SYSTEM
# ==========================================
@main_bp.route("/atm-request", methods=["GET", "POST"])
@login_required
def atm_request():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    reqs = AtmRequest.get_user_requests(user["id"])

    if request.method == "POST":
        card_type = request.form.get("card_type", "visa")
        address = request.form.get("address", "").strip()
        if not address:
            flash("Delivery address is required.", "danger")
            return redirect(url_for("main.atm_request"))

        AtmRequest.create(user["id"], card_type, address)
        Notification.notify_info(user["id"], f"Requested physical {card_type.upper()} card for home delivery.")
        flash("Physical ATM card request submitted! Handled by GCB Courier.", "success")
        return redirect(url_for("main.atm_request"))

    return render_template("atm_request.html", user=user, requests=reqs, notif_count=notif_count)


# ==========================================
# AIRTIME, DATA, & UTILITY BILLS MODULE
# ==========================================
@main_bp.route("/payments", methods=["GET", "POST"])
@login_required
def payments():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])

    if request.method == "POST":
        pay_type = request.form.get("pay_type") # "airtime" or "utility"
        amount = float(request.form.get("amount", 0))

        if amount <= 0:
            flash("Amount must be positive.", "danger")
            return redirect(url_for("main.payments"))

        if float(user["balance"]) < amount:
            flash("Insufficient balance to complete payment.", "danger")
            return redirect(url_for("main.payments"))

        try:
            # Deduct balance via simulated withdrawal transaction
            import uuid
            ref = f"PAY{uuid.uuid4().hex[:12].upper()}"
            desc = ""
            if pay_type == "airtime":
                provider = request.form.get("provider", "MTN")
                phone = request.form.get("phone", "")
                desc = f"Airtime Purchase: {provider} to {phone}"
            else:
                utility = request.form.get("utility", "GWCL")
                meter = request.form.get("meter_number", "")
                desc = f"Utility Bill: {utility} (Meter: {meter})"

            queries = [
                ("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, user["id"])),
                ("INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description, reference_number) "
                 "VALUES (%s, 'withdrawal', %s, (SELECT balance FROM users WHERE id = %s), %s, %s)",
                 (user["id"], amount, user["id"], desc, ref))
            ]
            execute_transaction(queries)
            Notification.notify_transaction(user["id"], "withdrawal", amount, ref)
            flash(f"Payment of GH₵ {amount:,.2f} completed successfully!", "success")
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            flash(f"Payment failed: {str(e)}", "danger")

    return render_template("payments.html", user=user, notif_count=notif_count)


# ==========================================
# SAVINGS GOALS & BENEFICIARIES TRACKER
# ==========================================
@main_bp.route("/savings-goals", methods=["GET", "POST"])
@login_required
def savings_goals():
    user = User.find_by_id(session["user_id"])
    notif_count = Notification.get_unread_count(user["id"])
    goals = SavingsGoal.get_user_goals(user["id"])
    benefs = Beneficiary.get_user_beneficiaries(user["id"])

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_goal":
            name = request.form.get("goal_name", "").strip()
            target = float(request.form.get("target_amount", 0))
            deadline = request.form.get("deadline") or None
            
            if name and target > 0:
                SavingsGoal.create(user["id"], name, target, deadline)
                flash("Savings Goal created successfully!", "success")
            else:
                flash("Goal name and target are required.", "danger")
            return redirect(url_for("main.savings_goals"))

    return render_template("savings_goals.html", user=user, goals=goals, beneficiaries=benefs, notif_count=notif_count)


@main_bp.route("/savings-goals/<int:goal_id>/save", methods=["POST"])
@login_required
def save_goal(goal_id):
    try:
        amount = float(request.form.get("amount", 0))
        if amount <= 0:
            flash("Enter a valid amount.", "danger")
            return redirect(url_for("main.savings_goals"))
        
        SavingsGoal.save_towards(goal_id, session["user_id"], amount)
        flash("Saved successfully toward your goal!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Transaction failed.", "danger")
    return redirect(url_for("main.savings_goals"))


@main_bp.route("/beneficiary/add", methods=["POST"])
@login_required
def add_beneficiary():
    account = request.form.get("account_number", "").strip()
    nickname = request.form.get("nickname", "").strip()
    try:
        if account and nickname:
            Beneficiary.create(session["user_id"], account, nickname)
            flash("Beneficiary saved successfully!", "success")
        else:
            flash("Beneficiary details are required.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("main.savings_goals"))


@main_bp.route("/beneficiary/<int:b_id>/delete", methods=["POST"])
@login_required
def delete_beneficiary(b_id):
    Beneficiary.delete(b_id, session["user_id"])
    flash("Beneficiary removed.", "success")
    return redirect(url_for("main.savings_goals"))


# ==========================================
# PRINT STATEMENT VIEW (PDF/PRINTER STYLED)
# ==========================================
@main_bp.route("/statement/download-pdf")
@login_required
def download_statement_pdf():
    user = User.find_by_id(session["user_id"])
    txns = Transaction.get_user_transactions(user["id"], 100, 0)
    return render_template("statement_pdf.html", user=user, transactions=txns)


# Upgrade profile route to accept KYC submissions as well
@main_bp.route("/profile/kyc", methods=["POST"])
@login_required
def submit_kyc():
    doc_type = request.form.get("document_type")
    file = request.files.get("kyc_file")
    if file and allowed_file(file.filename):
        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"kyc_{session['user_id']}_{secure_filename(file.filename)}"
        file.save(os.path.join(upload_dir, filename))
        
        # Insert document record
        execute_query(
            "INSERT INTO kyc_documents (user_id, document_type, document_path, status) VALUES (%s, %s, %s, 'pending')",
            (session["user_id"], doc_type, filename), commit=True
        )
        flash("KYC document uploaded successfully! Pending Admin verification.", "success")
    else:
        flash("Invalid file. Please upload an image or PDF document.", "danger")
    return redirect(url_for("main.profile"))


# ==========================================
# POLICY, TERMS, CONTACT & SUPPORT ENDPOINTS
# ==========================================
@main_bp.route("/privacy-policy")
def privacy():
    user = User.find_by_id(session["user_id"]) if "user_id" in session else None
    notif_count = Notification.get_unread_count(user["id"]) if user else 0
    return render_template("privacy.html", user=user, notif_count=notif_count)


@main_bp.route("/terms-of-service")
def terms():
    user = User.find_by_id(session["user_id"]) if "user_id" in session else None
    notif_count = Notification.get_unread_count(user["id"]) if user else 0
    return render_template("terms.html", user=user, notif_count=notif_count)


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    user = User.find_by_id(session["user_id"]) if "user_id" in session else None
    notif_count = Notification.get_unread_count(user["id"]) if user else 0
    if request.method == "POST":
        flash("Your support message has been sent successfully. We will contact you soon!", "success")
        return redirect(url_for("main.dashboard" if user else "main.index"))
    return render_template("contact.html", user=user, notif_count=notif_count)


@main_bp.route("/support", methods=["GET", "POST"])
def support():
    user = User.find_by_id(session["user_id"]) if "user_id" in session else None
    notif_count = Notification.get_unread_count(user["id"]) if user else 0
    if request.method == "POST":
        flash("Your support ticket has been opened successfully. Status: Pending.", "success")
        return redirect(url_for("main.dashboard" if user else "main.index"))
    return render_template("support.html", user=user, notif_count=notif_count)

