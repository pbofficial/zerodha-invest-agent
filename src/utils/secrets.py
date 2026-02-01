
import os
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

def get_secret(secret_id, version_id="latest"):
    """
    Fetches a secret from Google Cloud Secret Manager.
    
    Args:
        secret_id (str): The ID of the secret (e.g., 'GMAIL_APP_PASSWORD')
        version_id (str): The version of the secret. Defaults to 'latest'.
        
    Returns:
        str: The secret payload, or None if failed.
    """
    # Priority Logic:
    # 1. Local environment variables (Fastest for local dev/testing)
    env_val = os.environ.get(secret_id)
    if env_val:
        logger.info(f"🗝️ Using Local Var for {secret_id} [..{env_val.strip()[-4:]}]")
        val = env_val.strip()
        if secret_id == "GMAIL_APP_PASSWORD": return val.replace(" ", "")
        return val

    # 2. Check for Project ID to reach Cloud Secret Manager
    from src.utils.project import get_project_id
    project_id = get_project_id()

    if not project_id:
        logger.error("❌ Could not discover Project ID. Cannot reach Secret Manager.")
        return None

    logger.info(f"☁️ Fetching {secret_id} from Secret Manager (Project: {project_id})...")

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        val = response.payload.data.decode("UTF-8").strip()
        if secret_id == "GMAIL_APP_PASSWORD":
             return val.replace(" ", "")
        return val
    except Exception as e:
        logger.error(f"❌ Failed to fetch secret {secret_id} from Secret Manager: {str(e)}")
        return None
def save_secret(secret_id, payload):
    """
    Updates a secret in Google Cloud Secret Manager by adding a new version.
    """
    from src.utils.project import get_project_id
    project_id = get_project_id()

    if not project_id:
        logger.error("Could not discover Project ID. Cannot save secret.")
        return False

    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{project_id}/secrets/{secret_id}"
        
        # Payload must be bytes
        payload_bytes = payload.encode("UTF-8")
        
        response = client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": payload_bytes}
            }
        )
        logger.info(f"Successfully updated secret {secret_id}: {response.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to update secret {secret_id}: {e}")
        return False
