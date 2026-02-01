import os
import sys
import logging
import argparse
from kiteconnect import KiteConnect
from google.cloud import secretmanager

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(project_root)

from src.utils.secrets import get_secret

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KiteHelper")

def update_secret(secret_id, secret_value):
    """Updates a secret in Google Cloud Secret Manager (or prints if local)."""
    project_id = os.environ.get("PROJECT_ID")
    if not project_id:
        masked = secret_value[:4] + "*" * (max(0, len(secret_value)-8)) + secret_value[-4:] if len(secret_value) > 8 else "****"
        print(f"\n[LOCAL MODE] PROJECT_ID not set. Please manually update your environment:")
        print(f'$env:{secret_id}="{masked}" (Value hidden for security)')
        return True

    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}/secrets/{secret_id}"
    
    try:
        payload = secret_value.encode("UTF-8")
        client.add_secret_version(
            request={"parent": parent, "payload": {"data": payload}}
        )
        logger.info(f"Successfully updated secret {secret_id} in Secret Manager.")
        return True
    except Exception as e:
        logger.error(f"Failed to update secret {secret_id}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Kite API Authentication Helper")
    parser.add_argument("--login", action="store_true", help="Generate login URL")
    parser.add_argument("--exchange", type=str, help="Exchange request_token for access_token")
    
    args = parser.parse_args()

    api_key = get_secret("KITE_API_KEY")
    api_secret = get_secret("KITE_API_SECRET")

    if not api_key or (args.exchange and not api_secret):
        logger.error("Missing credentials in Secret Manager (KITE_API_KEY / KITE_API_SECRET)")
        print("\n[!] Please ensure placeholders in terraform/secrets.tf are replaced with real values.")
        return

    kite = KiteConnect(api_key=api_key)

    if args.login:
        print("\n--- Kite Login ---")
        print(f"Login URL: {kite.login_url()}")
        print("\n1. Open the URL above in your browser.")
        print("2. Log in with your Zerodha credentials.")
        print("3. After login, you will be redirected. Copy the 'request_token' from the URL.")
        print("4. Run this script again with: --exchange YOUR_REQUEST_TOKEN\n")

    elif args.exchange:
        try:
            data = kite.generate_session(args.exchange, api_secret=api_secret)
            access_token = data["access_token"]
            logger.info("Successfully generated access_token.")
            
            if update_secret("KITE_ACCESS_TOKEN", access_token):
                print("\n[v] KITE_ACCESS_TOKEN has been updated in Secret Manager.")
                print("[v] Your agent is now ready for 24 hours (or until token expiry).")
        except Exception as e:
            logger.error(f"Failed to generate session: {e}")

if __name__ == "__main__":
    main()
