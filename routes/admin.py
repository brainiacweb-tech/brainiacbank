from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.user import User
from models.transaction import Transaction
from models.loan import Loan
from models.atm import AtmRequest
from utils.helpers import admin_required
from database.db import execute_query

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_required
def dashboard():
    users = User.get_all_users()
    total_balance = sum(float(u["balance"]) for u in users)
    active_count = sum(1 for u in users if u["is_active"] and not u["is_frozen"])
    frozen_count = sum(1 for u in users if u["is_frozen"])
    total_users = len(users)

    recent_txns = Transaction.get_all_transactions(20)
    
    # Advanced admin features loading
    loans = Loan.get_all_loans()
    atm_reqs = AtmRequest.get_all_requests()
    kyc_docs = execute_query(
        """SELECT k.*, u.full_name, u.account_number 
           FROM kyc_documents k JOIN users u ON k.user_id = u.id 
           ORDER BY k.created_at DESC""",
        fetch_all=True
    )
    
    # Calculate bank revenue from simulated transfer fees (1.5% fee on all transfer_out transactions)
    revenue_result = execute_query(
        "SELECT SUM(amount) as total_transferred FROM transactions WHERE transaction_type = 'transfer_out'",
        fetch_one=True
    )
    total_transferred = float(revenue_result["total_transferred"] or 0)
    total_revenue = total_transferred * 0.015

    return render_template(
        "admin/dashboard.html",
        users=users,
        total_balance=total_balance,
        active_count=active_count,
        frozen_count=frozen_count,
        total_users=total_users,
        recent_transactions=recent_txns,
        loans=loans,
        atm_requests=atm_reqs,
        kyc_documents=kyc_docs,
        total_revenue=total_revenue
    )


@admin_bp.route("/freeze/<int:user_id>", methods=["POST"])
@admin_required
def freeze_account(user_id):
    User.toggle_freeze(user_id, True)
    flash("Account frozen.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/unfreeze/<int:user_id>", methods=["POST"])
@admin_required
def unfreeze_account(user_id):
    User.toggle_freeze(user_id, False)
    flash("Account unfrozen.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/deactivate/<int:user_id>", methods=["POST"])
@admin_required
def deactivate_account(user_id):
    User.soft_delete(user_id)
    flash("Account deactivated.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/activate/<int:user_id>", methods=["POST"])
@admin_required
def activate_account(user_id):
    User.activate(user_id)
    flash("Account activated.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/loans/<int:loan_id>/approve", methods=["POST"])
@admin_required
def approve_loan(loan_id):
    if Loan.approve(loan_id):
        flash("Loan approved and funds disbursed successfully!", "success")
    else:
        flash("Could not approve loan request.", "danger")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/loans/<int:loan_id>/reject", methods=["POST"])
@admin_required
def reject_loan(loan_id):
    Loan.reject(loan_id)
    flash("Loan request rejected.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/kyc/<int:doc_id>/approve", methods=["POST"])
@admin_required
def approve_kyc(doc_id):
    execute_query("UPDATE kyc_documents SET status = 'approved' WHERE id = %s", (doc_id,), commit=True)
    
    # Notify user of KYC approval
    doc = execute_query("SELECT user_id FROM kyc_documents WHERE id = %s", (doc_id,), fetch_one=True)
    if doc:
        from models.notification import Notification
        Notification.notify_security(doc["user_id"], "Your KYC Identity verification has been APPROVED.")
        
    flash("KYC Document approved.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/kyc/<int:doc_id>/reject", methods=["POST"])
@admin_required
def reject_kyc(doc_id):
    execute_query("UPDATE kyc_documents SET status = 'rejected' WHERE id = %s", (doc_id,), commit=True)
    
    doc = execute_query("SELECT user_id FROM kyc_documents WHERE id = %s", (doc_id,), fetch_one=True)
    if doc:
        from models.notification import Notification
        Notification.notify_security(doc["user_id"], "Your KYC Identity verification has been REJECTED. Please re-upload.")
        
    flash("KYC Document rejected.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/atm/<int:req_id>/status", methods=["POST"])
@admin_required
def update_atm_status(req_id):
    status = request.form.get("status", "pending")
    AtmRequest.update_status(req_id, status)
    
    req = execute_query("SELECT user_id, card_type FROM atm_requests WHERE id = %s", (req_id,), fetch_one=True)
    if req:
        from models.notification import Notification
        Notification.notify_info(req["user_id"], f"Your physical {req['card_type'].upper()} ATM Card delivery status updated to: {status.upper()}.")
        
    flash("ATM card request status updated.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/transactions")
@admin_required
def all_transactions():
    txns = Transaction.get_all_transactions(200)
    return render_template("admin/transactions.html", transactions=txns)


@admin_bp.route("/api/stats")
@admin_required
def stats():
    users = User.get_all_users()
    result = execute_query(
        """SELECT TO_CHAR(created_at, 'YYYY-MM') as month, COUNT(*) as count
           FROM users WHERE is_admin = 0
           GROUP BY TO_CHAR(created_at, 'YYYY-MM') ORDER BY month DESC LIMIT 6""",
        fetch_all=True,
    )
    return jsonify({
        "total_users": len(users),
        "total_balance": sum(float(u["balance"]) for u in users),
        "monthly_signups": result or [],
    })
