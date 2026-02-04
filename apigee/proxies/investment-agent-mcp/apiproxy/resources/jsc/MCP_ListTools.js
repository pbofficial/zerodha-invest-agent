// MCP Tool Definition (Matches API Hub Spec)
var toolsResponse = {
    "tools": [
        {
            "name": "get_market_snapshot",
            "description": "Get live market prices and user holdings. Use this as the first step for ANY portfolio analysis to check gaps between target and actual allocations.",
            "inputSchema": { "type": "object", "properties": { "tickers": { "type": "array", "items": { "type": "string" }, "description": "NSE symbols, uppercase (e.g., 'TCS'). Use ['ALL'] to get full portfolio." } }, "required": ["tickers"] }
        },
        {
            "name": "check_financial_health",
            "description": "Audit stock for profit declines. Analyzes quarterly profit trends and returns WARNING if profits have dropped for 2 consecutive quarters.",
            "inputSchema": { "type": "object", "properties": { "ticker": { "type": "string", "description": "NSE Ticker symbol." } }, "required": ["ticker"] }
        },
        {
            "name": "calculate_orders",
            "description": "Finalize trade quantities based on budget. Mathematical engine to convert 'Target Allocations' into 'Order Quantities'.",
            "inputSchema": { "type": "object", "properties": { "budget": { "type": "number", "description": "Total cash available." }, "portfolio": { "type": "array", "description": "Current holdings list." }, "prices": { "type": "object", "description": "Current LTP map." }, "targets": { "type": "object", "description": "Map of Ticker -> Target %." } }, "required": ["budget", "portfolio", "prices", "targets"] }
        },
        {
            "name": "get_market_news",
            "description": "Scour the web for regulatory or fraud risks. Fetches cynical news focusing on fraud and management exits.",
            "inputSchema": { "type": "object", "properties": { "tickers": { "type": "array", "items": { "type": "string" }, "description": "List of ticker symbols to audit." } }, "required": ["tickers"] }
        }
    ]
};
context.setVariable("response.content", JSON.stringify(toolsResponse));
context.setVariable("response.header.Content-Type", "application/json");
