import os
import json
import logging
from google.cloud import firestore
from src.utils.project import get_project_id

logger = logging.getLogger("ConfigLoader")

class ConfigLoader:
    _instance = None
    _config_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def _get_db(self):
        project_id = get_project_id()
        return firestore.Client(project=project_id)

    def get_agent_settings(self, force_refresh=False):
        """Fetches agent settings (budget, model, risk) from Firestore."""
        if "agent_settings" in self._config_cache and not force_refresh:
            return self._config_cache["agent_settings"]

        try:
            db = self._get_db()
            doc = db.collection("config").document("agent_settings").get()
            if doc.exists:
                settings = doc.to_dict()
                self._config_cache["agent_settings"] = settings
                logger.info("✅ Agent settings loaded from Firestore.")
                return settings
        except Exception as e:
            logger.warning(f"⚠️ Failed to load agent_settings from Firestore: {e}")

        # Fallback to local
        return self._load_local_json("agent_config.json")

    def get_universe(self, force_refresh=False):
        """Fetches the stock universe from Firestore."""
        if "universe" in self._config_cache and not force_refresh:
            return self._config_cache["universe"]

        try:
            db = self._get_db()
            doc = db.collection("config").document("universe").get()
            if doc.exists:
                universe = doc.to_dict()
                self._config_cache["universe"] = universe
                logger.info("✅ Universe loaded from Firestore.")
                return universe
        except Exception as e:
            logger.warning(f"⚠️ Failed to load universe from Firestore: {e}")

        # Fallback to local
        return self._load_local_json("universe.json")

    def _load_local_json(self, filename):
        """Helper to load local JSON templates."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.abspath(os.path.join(current_dir, "..", "config", filename))
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ Critical failure loading local {filename}: {e}")
        return {}

    def update_agent_settings(self, settings_dict):
        """Saves new settings to Firestore."""
        try:
            db = self._get_db()
            db.collection("config").document("agent_settings").set(settings_dict)
            self._config_cache["agent_settings"] = settings_dict
            logger.info("🚀 Agent settings updated in Firestore.")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update agent_settings: {e}")
            return False

# Global instance for easy access
config = ConfigLoader()
