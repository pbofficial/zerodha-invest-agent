import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.agent.mcp_advisor import MCPInvestmentAdvisor

def test_mcp_discovery_logic():
    print("Testing MCP Discovery Logic...")
    advisor = MCPInvestmentAdvisor(mcp_endpoint="http://10.140.24.2", api_key="test-key")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "tools": [
            {
                "name": "get_market_snapshot",
                "description": "Test tool",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
    }
    
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response
        tools = advisor._discover_tools()
        
        # Verify call parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "http://10.140.24.2/mcp/v1/list_tools"
        assert kwargs["headers"]["x-api-key"] == "test-key"
        
        assert len(tools) == 1
        # Vertex AI objects often use protos, but to_dict is reliable for testing
        tool_dict = tools[0].to_dict()
        assert tool_dict["name"] == "get_market_snapshot"
        print("✅ Discovery Logic Verified")

def test_mcp_execution_logic():
    print("\nTesting MCP Execution Logic...")
    advisor = MCPInvestmentAdvisor(mcp_endpoint="http://10.140.24.2", api_key="test-key")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success", "data": "mock_data"}
    
    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_response
        res = advisor._execute_tool("calculate_orders", {"budget": 1000})
        
        # Verify call parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://10.140.24.2/mcp/calculate_orders"
        assert kwargs["headers"]["x-api-key"] == "test-key"
        assert kwargs["json"] == {"budget": 1000}
        
        assert res["status"] == "success"
        print("✅ Execution Logic Verified")

if __name__ == "__main__":
    try:
        test_mcp_discovery_logic()
        test_mcp_execution_logic()
        print("\n✨ All MCP Logic Tests Passed Locally!")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        sys.exit(1)
