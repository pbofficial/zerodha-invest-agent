import os
import sys
import logging
import time
from google.cloud import firestore
from kiteconnect import KiteConnect

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(project_root)

from src.functions.market_data.main import is_market_open
from src.utils.secrets import get_secret
from src.utils.notifications import NotificationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MorningRun")

def normalize_t(t): return t.split(":")[-1].upper() if ":" in t else t.upper()

def run_morning_execution(request=None, dry_run=False, force=False, api_key_override=None, access_token_override=None):
    """
    Runs at 9:15 AM to check for queued orders and execute them via Kite.
    """
    # If called via HTTP (GCP Cloud Function), parse the request body
    if request:
        try:
            req_data = request.get_json(silent=True) or {}
            force = req_data.get("force", force)
            dry_run = req_data.get("dry_run", dry_run)
            logger.info(f"📥 Received Request Params: force={force}, dry_run={dry_run}")
        except Exception as e:
            logger.warning(f"Could not parse request body: {e}")

    # Override via Env for safety
    if os.environ.get("DRY_RUN") == "true": dry_run = True
    
    is_open, _ = is_market_open()
    if not is_open and not dry_run and not force:
        logger.info("Market is still closed. Skipping morning run (Use --force to test).")
        return "Market Closed", 200

    project_id = os.environ.get("PROJECT_ID")
    db = firestore.Client(project=project_id)
    pending_ref = db.collection("pending_orders").document("latest")
    doc = pending_ref.get()

    if not doc.exists:
        logger.info("No pending orders document found.")
        return "No Pending Orders", 200

    data = doc.to_dict()
    if data.get("status") != "APPROVED" and not dry_run:
        logger.info(f"Status is {data.get('status')}. Waiting for final approval.")
        return f"Status: {data.get('status')}", 200

    # For Dry Run, we can force-execute even if status isn't APPROVED
    orders = data.get("orders", [])
    if dry_run and not orders:
        # Check if we have anything in QUEUED status for dry mapping
        if data.get("status") == "QUEUED": orders = data.get("orders", [])

    if not orders:
        logger.info("No orders found to execute.")
        return "No Orders", 200

    # Initialize Kite (Optional for Dry Run)
    it = None
    if not dry_run:
        import re
        def clean(s): return re.sub(r'[^\w\-]', '', s) if s else s
        
        api_key = clean(api_key_override or get_secret("KITE_API_KEY"))
        access_token = clean(access_token_override or get_secret("KITE_ACCESS_TOKEN"))
        
        source = "CLI_OVERRIDE" if (api_key_override or access_token_override) else "AUTO_RESOLVE"
        
        if not api_key or not access_token:
            logger.error(f"Missing KITE_API_KEY or KITE_ACCESS_TOKEN ({source}). Cannot execute.")
            return "Missing Credentials", 500
        
        # --- Credential Audit ---
        key_masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else api_key
        tok_masked = f"{access_token[:4]}...{access_token[-4:]}" if len(access_token) > 8 else access_token
        logger.info(f"🔑 Credential Audit ({source}): Key[{key_masked}] | Token[{tok_masked}]")
        
        it = KiteConnect(api_key=api_key)
        it.set_access_token(access_token)
        
        # --- SESSION VALIDITY CHECK ---
        try:
            profile = it.profile()
            logger.info(f"👤 Session Validated: Connected as {profile.get('user_name')} ({profile.get('user_id')})")
            
            # --- FUND VALIDATION ---
            margins = it.margins()
            cash = margins.get("equity", {}).get("net", 0)
            logger.info(f"💰 Available Cash: ₹{cash}")
            
            # If we're not in dry run, and cash is 0, we should probably stop or at least warn loudly
            if cash <= 0 and not dry_run:
                logger.error("🛑 ZERO FUNDS AVAILABLE. Aborting execution to avoid system errors.")
                return "Insufficient Funds", 400

        except Exception as e:
            logger.error(f"🚫 Session/Fund Validation Failed: {e}")
            logger.error("The Access Token may be expired or the API is unresponsive.")
            return "Auth/Fund Failure", 401

    execution_results = []
    logger.info(f"{'🧪 DRY RUN' if dry_run else '🚀'} Found {len(orders)} orders. Processing...")

    for order in orders:
        ticker = normalize_t(order['ticker'])
        qty = int(order['quantity'])
        
        try:
            if dry_run:
                logger.info(f"[DRY] Would Place: BUY {qty} {ticker} (CNC/MARKET)")
                execution_results.append({"ticker": ticker, "quantity": qty, "status": "DRY_SUCCESS"})
            else:
                logger.info(f"⚡ Placing Order: BUY {qty} {ticker} (CNC/MARKET)")
                
                # --- DETAILED AUDIT LOGGING (REQUEST) ---
                params = {
                    "variety": "regular", 
                    "exchange": "NSE", 
                    "tradingsymbol": ticker, 
                    "transaction_type": "BUY", 
                    "quantity": qty, 
                    "product": "CNC", 
                    "order_type": "MARKET"
                }
                logger.info(f"📡 API REQUEST [place_order]: {json.dumps(params)}")
                
                try:
                    order_id = it.place_order(**params)
                    logger.info(f"✅ Order Placed: {order_id}")
                    execution_results.append({"ticker": ticker, "quantity": qty, "status": "PLACED", "order_id": order_id})
                except Exception as api_err:
                    # Capture raw response if possible (KiteConnect exceptions often have .message)
                    logger.error(f"❌ API RESPONSE [ERROR]: {api_err}")
                    execution_results.append({"ticker": ticker, "quantity": qty, "status": "FAILED", "error": str(api_err)})
                
                time.sleep(0.5) 
        except Exception as e:
            logger.error(f"❌ unexpected error executing {ticker}: {e}")
            execution_results.append({"ticker": ticker, "quantity": qty, "status": "ERROR", "error": str(e)})

    # --- ORDER VERIFICATION LOOP ---
    if not dry_run and execution_results:
        logger.info("⏳ Waiting 10 seconds for order processing...")
        time.sleep(10)
        
        try:
            orders_book = it.orders()
            orders_map = {o['order_id']: o for o in orders_book}
            
            for res in execution_results:
                oid = res.get("order_id")
                if oid and oid in orders_map:
                    kite_order = orders_map[oid]
                    res["status"] = kite_order.get("status") # COMPLETE, REJECTED, etc.
                    res["reason"] = kite_order.get("status_message")
                    if res["status"] == "COMPLETE":
                        logger.info(f"🏁 {res['ticker']}: Order Fully Executed")
                    else:
                        logger.warning(f"⚠️ {res['ticker']}: Order {res['status']} - {res['reason']}")
        except Exception as e:
            logger.error(f"Failed to verify order status: {e}")

    # --- EXECUTION REPORT ---
    if not dry_run:
        try:
            nm = NotificationManager()
            recipient = get_secret("RECIPIENT_EMAIL")
            if recipient:
                subject = f"🚀 Execution Report - {time.strftime('%Y-%m-%d')}"
                report_lines = [f"Market Execution Summary for {time.strftime('%Y-%m-%d %H:%M:%S')}\n"]
                for r in execution_results:
                    status_str = r.get('status', 'UNKNOWN')
                    reason_str = f" ({r.get('reason') or r.get('error') or ''})" if r.get('status') != "COMPLETE" else ""
                    report_lines.append(f"- {r['ticker']}: {r['quantity']} Qty -> {status_str}{reason_str}")
                
                nm.send_gmail(recipient, subject, "\n".join(report_lines))
                logger.info("📧 Execution report email sent.")
        except Exception as e:
            logger.error(f"Failed to send execution report: {e}")

    # Move to History
    if not dry_run:
        # Move to History
        history_ref = db.collection("rebalance_history").document()
        history_ref.set({
            "executed_at": firestore.SERVER_TIMESTAMP,
            "orders": orders,
            "results": execution_results,
            "total_budget": data.get("budget", 0)
        })

        # Clear Pending Document (Automated Removal)
        pending_ref.update({
            "status": "COMPLETED",
            "last_executed": firestore.SERVER_TIMESTAMP
            # Keep ui_snapshot and orders for visual record
        })
        logger.info("✅ Morning execution complete. State archived.")
    else:
        logger.info("🧪 Dry run complete. No state changed.")

    return "Execution Complete", 200

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Force execution even if market is closed")
    parser.add_argument("--api-key", type=str, default=None, help="Manual Kite API Key override")
    parser.add_argument("--access-token", type=str, default=None, help="Manual Kite Access Token override")
    args = parser.parse_args()
    
    run_morning_execution(
        dry_run=args.dry_run, 
        force=args.force, 
        api_key_override=args.api_key, 
        access_token_override=args.access_token
    )
