
import os
import sys
import subprocess
import time
import logging
import socket

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("PipelineTest")

def run_step(name, cmd):
    logger.info(f"\n▶️ Running Step: {name}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Step '{name}' Failed!")
        print(e.stdout)
        print(e.stderr)
        return False

def check_dashboard_running(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect(("127.0.0.1", int(port)))
        s.close()
        return True
    except:
        return False

def main():
    logger.info("🧪 Starting LOCAL Portfolio Agent System Test")
    
    dashboard_port = "8501"
    local_url = f"http://localhost:{dashboard_port}"
    os.environ["DASHBOARD_URL"] = local_url
    
    # 1. Start/Check Dashboard
    if not check_dashboard_running(dashboard_port):
        logger.info(f"🚀 Dashboard not found on {local_url}. Starting locally...")
        cmd = [sys.executable, "-m", "streamlit", "run", "src/dashboard/app.py", "--server.port", dashboard_port, "--server.headless", "true"]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("⏳ Waiting for dashboard to initialize (10s)...")
        time.sleep(10)
    else:
        logger.info(f"✅ Dashboard already running on {local_url}")

    # 2. Trigger Nudge (Simulate 9 PM ET)
    if not run_step("Trigger Nudge", "python src/agent/trigger.py"):
        return

    logger.info(f"\n📝 [MANUAL STEP]: Open the LOCAL Dashboard: {local_url}")
    logger.info("1. 'Run Analysis'")
    logger.info("2. Click 'Execute Trades' to move from DRAFT -> QUEUED.")
    input("\nPress Enter once you have 'QUEUED' orders in the LOCAL Dashboard...")

    # 3. Morning Approval (Simulate 8:50 AM IST)
    if not run_step("Morning Approval Nudge", "python src/agent/morning_approval.py"):
        return

    logger.info("\n📧 [MANUAL STEP]: Open your Gmail and click 'Confirm & Execute' (Points to LOCAL).")
    input("\nPress Enter once status is 'APPROVED' in the LOCAL Dashboard...")

    # 4. Final Execution (Simulate 9:15 AM IST - DRY RUN)
    if not run_step("Morning Execution (Dry Run)", "python src/agent/morning_run.py --dry-run"):
        return

    logger.info("\n✅ Local System Test Complete!")
    logger.info("The entire pipeline is validated and ready for production.")

if __name__ == "__main__":
    main()
