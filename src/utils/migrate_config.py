import os
import sys
import json

# Setup path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from src.utils.config_loader import config
from src.utils.project import get_project_id

def migrate_to_cloud():
    print(f"🔍 Working on Project: {get_project_id()}")
    
    # 1. Ask for inputs or read from local (if existing)
    print("\n--- Current Local Settings (Templates) ---")
    local_settings = config._load_local_json("agent_config.json")
    print(json.dumps(local_settings, indent=2))
    
    confirm = input("\nDo you want to push these settings to Firestore as your new Cloud Base? (y/n): ")
    if confirm.lower() == 'y':
        success = config.update_agent_settings(local_settings)
        if success:
            print("🚀 SUCCESS: agent_settings are now in the Cloud!")
            print("Action: You can now go to GCP Console to edit your real Budget/Model safely.")
        else:
            print("❌ FAILED to update Firestore.")
    else:
        print("⏭️ Migration skipped. Please provide your real settings manually in the scripts.")

if __name__ == "__main__":
    migrate_to_cloud()
