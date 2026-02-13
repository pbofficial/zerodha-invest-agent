import os
import json
import logging
import google.auth

logger = logging.getLogger(__name__)

def get_project_id():
    """
    Dynamically discovers the Google Cloud Project ID.
    Precedence:
    1. Environment Variable PROJECT_ID
    2. agent_config.json setting
    3. Google Application Default Credentials (ADC) discovery
    """
    # 1. Check Environment Variable
    project_id = os.environ.get("PROJECT_ID")
    if project_id:
        logger.info(f"✅ Using Project ID from Environment: {project_id}")
        return project_id

    # 2. Check agent_config.json
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.abspath(os.path.join(current_dir, "..", "config", "agent_config.json"))
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                project_id = config.get("agent_settings", {}).get("project_id")
                if project_id:
                    logger.info(f"📁 Using Project ID from agent_config.json: {project_id}")
                    os.environ["PROJECT_ID"] = project_id
                    return project_id
    except Exception as e:
        logger.warning(f"⚠️ Failed to load project_id from config: {e}")

    # 3. Fallback to Google Auth Discovery (ADC)
    try:
        logger.info("🔍 Attempting ADC Project Discovery...")
        credentials, discovered_project = google.auth.default()
        if discovered_project:
            logger.info(f"🛰️ Discovered Project ID via ADC: {discovered_project}")
            os.environ["PROJECT_ID"] = discovered_project
            return discovered_project
    except Exception as e:
        logger.error(f"❌ ADC discovery failed: {e}")

def get_project_number(project_id=None):
    """
    Retrieves the project number for a given project ID.
    Used for modern Cloud Run URL construction.
    """
    if not project_id:
        project_id = get_project_id()
    
    try:
        from google.cloud import resourcemanager_v3
        client = resourcemanager_v3.ProjectsClient()
        request = resourcemanager_v3.GetProjectRequest(name=f"projects/{project_id}")
        project = client.get_project(request=request)
        # Extract number from name: projects/NUMBER
        return project.name.split("/")[-1]
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch project number via API: {e}")
        # Secondary fallback: try to use the project ID as a substitute in some URLs 
        # but Cloud Run strictly wants the number for the modern format.
        return None

def get_dashboard_url():
    """
    Returns the modern Dashboard URL, constructed dynamically if not in env.
    """
    url = os.environ.get("DASHBOARD_URL")
    if url:
        return url
    
    project_id = get_project_id()
    project_num = get_project_number(project_id)
    region = os.environ.get("LOCATION", "us-east4")
    
    if project_num:
        return f"https://portfolio-dashboard-{project_num}.{region}.run.app"
    
    # Absolute last resort fallback
    return f"https://portfolio-dashboard-{project_id}.{region}.run.app"

def get_apigee_mcp_endpoint():
    """
    Returns the internal Apigee MCP endpoint.
    Defaulting to the user-provided internal IP for the private network.
    """
    endpoint = os.environ.get("APIGEE_MCP_ENDPOINT", "https://10.140.24.2")
    logger.debug(f"ℹ️ Apigee MCP Endpoint resolved: {endpoint}")
    return endpoint

def get_apigee_api_key():
    """
    Fetches the Apigee API Key from Secret Manager or Env.
    """
    from src.utils.secrets import get_secret
    return get_secret("APIGEE_API_KEY")

def get_location():
    """
    Resolves the GCP Location (Region) with precedence:
    1. Environment Variable: LOCATION
    2. Firestore Config: agent_settings.location
    3. Fallback: us-east4
    """
    loc = os.environ.get("LOCATION")
    if loc:
        logger.info(f"✅ Resolved Location from Env: {loc}")
        return loc
    
    try:
        from src.utils.config_loader import config
        settings = config.get_agent_settings().get("agent_settings", {})
        loc = settings.get("location")
        if loc:
            logger.info(f"✅ Resolved Location from Firestore: {loc}")
            return loc
    except Exception as e:
        logger.debug(f"ℹ️ Firestore location look-up skipped/failed: {e}")
        
    logger.info("ℹ️ Using Default Location: us-east4")
    return "us-east4"

def get_model_name():
    """
    Resolves the Vertex AI Model Name with precedence:
    1. Environment Variable: MODEL_NAME
    2. Firestore Config: agent_settings.model_name
    3. Fallback: gemini-2.0-flash
    """
    model = os.environ.get("MODEL_NAME")
    if model:
        logger.info(f"✅ Resolved Model from Env: {model}")
        return model
        
    try:
        from src.utils.config_loader import config
        settings = config.get_agent_settings().get("agent_settings", {})
        model = settings.get("model_name")
        if model:
            logger.info(f"✅ Resolved Model from Firestore: {model}")
            return model
    except Exception as e:
        logger.debug(f"ℹ️ Firestore model look-up skipped/failed: {e}")
        
    logger.info("ℹ️ Using Default Model: gemini-2.0-flash")
    return "gemini-2.0-flash"
