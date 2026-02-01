
import smtplib
import requests
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.utils.secrets import get_secret

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        # Fetch secrets from Secret Manager (with ENV fallback inside get_secret)
        self.gmail_user = get_secret("GMAIL_USER")
        self.gmail_password = get_secret("GMAIL_APP_PASSWORD")

    def send_gmail(self, recipient, subject, body_text, html_body=None):
        if not self.gmail_user or not self.gmail_password:
            logger.warning("GMAIL_USER or GMAIL_APP_PASSWORD not set. Skipping Email.")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Zerodha Invest Agent <{self.gmail_user}>"
            msg['To'] = recipient
            msg['Subject'] = subject

            # Attach plain text version
            msg.attach(MIMEText(body_text, 'plain'))
            
            # Attach HTML version if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            logger.info("Gmail notification sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send Email: {e}")
            return False
