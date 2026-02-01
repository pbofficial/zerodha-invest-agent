
import os
import sys
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from src.utils.notifications import NotificationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyLocal")

def test_notifications():
    notifier = NotificationManager()
    
    print("\n--- Testing Notifications ---")
    
    # 1. Test Email
    recipient = os.environ.get("RECIPIENT_EMAIL")
    if recipient:
        print(f"Testing Gmail to {recipient}...")
        success_email = notifier.send_gmail(
            recipient,
            "Zerodha Agent Link Test",
            "This is a local verification test of the notification system."
        )
        if success_email:
            print("✅ Email successful!")
        else:
            print("❌ Email failed. Check GMAIL_USER and GMAIL_APP_PASSWORD.")
    else:
        print("⚠️ RECIPIENT_EMAIL not set. Skipping email test.")

if __name__ == "__main__":
    test_notifications()
