import requests
import os
import sys
import json
import argparse

def verify_mcp(api_key, project_id, env="eval"):
    base_url = f"https://{project_id}-{env}.apigee.net/mcp"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    print(f"🔹 Verifying MCP Endpoint: {base_url}")

    # 1. Test List Tools
    print("\n1️⃣ Testing /v1/list_tools...")
    try:
        resp = requests.post(f"{base_url}/v1/list_tools", headers=headers, json={}) # Some MCP implementations utilize POST for everything
        # Try GET if POST fails or as per standard
        if resp.status_code == 404 or resp.status_code == 405:
             resp = requests.get(f"{base_url}/v1/list_tools", headers=headers)
             
        if resp.status_code == 200:
            print("✅ Success! Tools list received.")
            tools = resp.json().get("tools", [])
            print(f"   Found {len(tools)} tools:")
            for t in tools:
                print(f"   - {t.get('name')}")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

    # 2. Test Call Tool (Calculate Orders - Dry Run)
    print("\n2️⃣ Testing /v1/call_tool (calculate_orders)...")
    payload = {
        "method": "tools/call",
        "params": {
            "name": "calculate_orders",
            "arguments": {
                "budget": 10000,
                "portfolio": [],
                "prices": {"TCS": 3500},
                "targets": {"TCS": 1.0}
            }
        }
    }
    
    try:
        resp = requests.post(f"{base_url}", headers=headers, json=payload)
        # Note: The proxy might route based on path suffix /calculate_orders OR intercept the JSON-RPC body at root
        # My implementation routes via /mcp/calculate_orders OR JSON-RPC interception.
        # Let's try the root endpoint first as a true "MCP Server"
        
        if resp.status_code != 200:
             # Fallback to direct path generic MCP style if the root router isn't matching
             print("   (Retrying with specific path...)")
             resp = requests.post(f"{base_url}/calculate_orders", headers=headers, json=payload["params"]["arguments"])

        if resp.status_code == 200:
            print("✅ Success! Tool execution completed.")
            print(f"   Response: {resp.text[:100]}...")
        else:
             print(f"❌ Failed: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True, help="Apigee API Key")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    args = parser.parse_args()
    
    verify_mcp(args.key, args.project)
