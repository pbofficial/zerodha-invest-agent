
import os
import sys
import logging
import time
from google.cloud import firestore

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(project_root)

from src.functions.market_data.main import is_trading_day
from src.utils.notifications import NotificationManager
from src.utils.secrets import get_secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MorningApproval")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #0f172a; padding: 30px; border-radius: 12px 12px 0 0; text-align: center; color: white;">
        <h1 style="margin: 0; font-size: 22px;">⚡ Final Approval Required</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.8;">Market Opens In ~25 Minutes</p>
    </div>
    
    <div style="padding: 30px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; background: white;">
        <p>Hello,</p>
        <p>You have <strong>{count}</strong> orders queued for execution. Please provide final confirmation to release them to the exchange.</p>
        
        <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <ul style="margin: 0; padding-left: 20px;">
                {order_list}
            </ul>
        </div>

        <div style="text-align: center; margin: 35px 0;">
            <a href="{approve_url}" style="background-color: #15803d; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block; margin-right: 15px;">🚀 Confirm & Execute</a>
            <a href="{reject_url}" style="background-color: #b91c1c; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">🛑 Abort Batch</a>
        </div>

        <p style="font-size: 0.85em; color: #64748b; text-align: center;">Orders will NOT be placed unless you click 'Confirm'.</p>
    </div>
    <div style="text-align: center; margin-top: 20px; font-size: 11px; color: #94a3b8;">
        © 2026 Zerodha Invest Agent • Secure Execution Layer
    </div>
</body>
</html>
"""

def run_approval_nudge(request=None):
    """
    Runs at 8:50 AM IST. Checks for QUEUED orders and sends a final confirmation email.
    """
    if not is_trading_day():
        return "Not a trading day", 200

    db = firestore.Client(project=os.environ.get("PROJECT_ID"))
    pending_ref = db.collection("pending_orders").document("latest")
    doc = pending_ref.get()

    if not doc.exists:
        return "No pending orders", 200

    data = doc.to_dict()
    if data.get("status") != "QUEUED":
        return f"Status is {data.get('status')}", 200

    orders = data.get("orders", [])
    if not orders:
        return "No orders in queue", 200

    # Prepare Email
    notifier = NotificationManager()
    recipient = os.environ.get("RECIPIENT_EMAIL")
    
    from src.utils.project import get_dashboard_url
    dashboard_url = get_dashboard_url()
    
    # Generate Links
    # We use query params that the dashboard will handle
    approve_url = f"{dashboard_url}?action=approve_batch"
    reject_url = f"{dashboard_url}?action=reject_batch"

    order_items = ""
    for o in orders:
        order_items += f"<li><b>{o['ticker']}</b>: BUY {o['quantity']}</li>"

    html_body = HTML_TEMPLATE.format(
        count=len(orders),
        order_list=order_items,
        approve_url=approve_url,
        reject_url=reject_url
    )

    if recipient:
        notifier.send_gmail(
            recipient,
            "📈 [Personal Investment Agent] Final Trade Approval Required",
            f"You have {len(orders)} orders waiting. Approve via dashboard.",
            html_body=html_body
        )
        return "Approval Nudge Sent", 200
    
    return "Recipient not set", 200

if __name__ == "__main__":
    run_approval_nudge()
