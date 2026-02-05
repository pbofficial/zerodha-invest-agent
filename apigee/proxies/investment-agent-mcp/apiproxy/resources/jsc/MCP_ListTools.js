// MCP Tool Discovery Logic (Enterprise Pattern)
// Pulls from API Hub ServiceCallout 'apihubResponse'
var apihubResContent = context.getVariable("apihubResponse.content");
var apihubData = JSON.parse(apihubResContent);
var hubApis = apihubData.apis || [];

// Static Schema Mapping (In Enterprise, these could also be fetched from Hub Specs)
var SCHEMAS = {
    "get-market-snapshot": { "type": "object", "properties": { "tickers": { "type": "array", "items": { "type": "string" }, "description": "NSE symbols, uppercase (e.g., 'TCS'). Use ['ALL'] to get full portfolio." } }, "required": ["tickers"] },
    "check-financial-health": { "type": "object", "properties": { "ticker": { "type": "string", "description": "NSE Ticker symbol." } }, "required": ["ticker"] },
    "calculate-allocations": { "type": "object", "properties": { "budget": { "type": "number", "description": "Total cash available." }, "portfolio": { "type": "array", "description": "Current holdings list." }, "prices": { "type": "object", "description": "Current LTP map." }, "targets": { "type": "object", "description": "Map of Ticker -> Target %." } }, "required": ["budget", "portfolio", "prices", "targets"] },
    "get-market-news": { "type": "object", "properties": { "tickers": { "type": "array", "items": { "type": "string" }, "description": "List of ticker symbols to audit." } }, "required": ["tickers"] }
};

var tools = [];

hubApis.forEach(function (api) {
    var toolId = api.name.split("/").pop(); // e.g. "get-market-snapshot"

    // Fallback: If mcp_type attribute is missing, check if we have a schema for it
    // This allows discovery to work even if the registry tags are missing.
    if (SCHEMAS[toolId]) {
        var mcpName = toolId.replace(/\-/g, "_"); // e.g. "get_market_snapshot"

        tools.push({
            "name": mcpName,
            "description": api.description || api.displayName,
            "inputSchema": SCHEMAS[toolId]
        });
    }
});

var toolsResponse = { "tools": tools };
context.setVariable("response.content", JSON.stringify(toolsResponse));
context.setVariable("response.header.Content-Type", "application/json");
