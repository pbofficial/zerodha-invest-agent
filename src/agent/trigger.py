
import os
import sys
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(project_root)

from src.utils.notifications import NotificationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Trigger")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        .container {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 20px auto; border: 1px solid #eee; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        .header {{ background: linear-gradient(135deg, #0f172a, #2563eb); color: #ffffff; padding: 45px 20px; text-align: center; }}
        .content {{ padding: 40px; line-height: 1.7; color: #334155; background-color: #ffffff; }}
        .button-container {{ text-align: center; margin: 35px 0; }}
        .button {{ background-color: #2563eb; color: #ffffff !important; padding: 16px 32px; text-decoration: none; border-radius: 10px; font-weight: 600; display: inline-block; font-size: 16px; border: none; }}
        .footer {{ background-color: #f8fafc; padding: 25px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #f1f5f9; }}
        .quote {{ font-style: italic; color: #475569; border-left: 4px solid #3b82f6; padding-left: 20px; margin: 25px 0; font-size: 1.05em; line-height: 1.5; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin:0;">Daily Market Pulse Ready</h1>
            <p style="margin:10px 0 0 0; opacity: 0.9;">Zerodha Invest Agent • Daily Investment Flow</p>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>Your daily investment cycle has been triggered. The market opens in less than 2 hours (9:15 AM IST).</p>
            
            <div class="quote">
                "The most important quality for an investor is temperament, not intellect." — Warren Buffett
            </div>

            <p>Please open your dashboard to run the AI analysis and queue your orders for today's market session.</p>
            
            <div class="button-container">
                <a href="{dashboard_url}" class="button">Open Portfolio Dashboard</a>
            </div>

            <p style="font-size: 0.9em; color: #666;">Note: Orders placed while market is closed will be queued for the next opening bell (9:15 AM IST).</p>
        </div>
        <div class="footer">
            © 2026 Zerodha Invest Agent (GCP Vertex AI) <br>
            Secure Financial Automation
        </div>
    </div>
</body>
</html>
"""

def run_trigger(request=None):
    """
    Called by Cloud Scheduler at 9 PM ET (7 AM IST).
    Checks if today is a trading day and sends a nudge.
    """
    import json
    force = False
    if request:
        try:
            request_json = request.get_json(silent=True)
            if request_json and request_json.get("force"):
                force = True
                logger.info("💪 Force flag detected. Bypassing market check.")
        except:
            pass

    from src.functions.market_data.main import is_trading_day
    if not is_trading_day() and not force:
        logger.info("Market is closed today (Holiday/Weekend). Skipping daily nudge.")
        return "Market Closed Today", 200

    notifier = NotificationManager()
    
    from src.utils.project import get_dashboard_url
    dashboard_url = get_dashboard_url()
    recipient_email = os.environ.get("RECIPIENT_EMAIL")

    plain_msg = f"🚀 Time to Rebalance!\n\nYour bi-monthly investment window is open. Please review your targets and execute the plan.\n\nDashboard: {dashboard_url}"
    html_msg = HTML_TEMPLATE.format(dashboard_url=dashboard_url)
    
    # Send Premium Email
    if recipient_email:
        notifier.send_gmail(
            recipient_email,
            "📈 [Personal Investment Agent] Daily Market Pulse",
            plain_msg,
            html_body=html_msg
        )
        return "Trigger Nudge Sent Successfully", 200
    else:
        logger.warning("RECIPIENT_EMAIL not set. Skipping email.")
        return "RECIPIENT_EMAIL not set", 200

if __name__ == "__main__":
    run_trigger()
