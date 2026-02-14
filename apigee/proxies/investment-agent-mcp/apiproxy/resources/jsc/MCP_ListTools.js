// MCP Tool Discovery Logic (Enterprise Pattern)
// Pulls from API Hub ServiceCallout 'apihubResponse'
var apihubResContent = context.getVariable("apihubResponse.content");
var apihubData = JSON.parse(apihubResContent);
var hubApis = apihubData.apis || [];

// Static Schema Mapping (In Enterprise, these could also be fetched from Hub Specs)
var SCHEMAS = {
    "get-market-snapshot": { "type": "object", "properties": { "tickers": { "type": "array", "items": { "type": "string" }, "description": "NSE symbols, uppercase (e.g., 'TCS'). Use ['ALL'] to get full portfolio." } }, "required": ["tickers"] },
    "check-financial-health": { "type": "object", "properties": { "tickers": { "type": "array", "items": { "type": "string" }, "description": "List of NSE Ticker symbols to audit." } }, "required": ["tickers"] },
    "calculate-allocations": { "type": "object", "properties": { "budget": { "type": "number", "description": "Total cash available." }, "portfolio": { "type": "array", "description": "Current holdings list." }, "prices": { "type": "object", "description": "Current LTP map." }, "targets": { "type": "object", "description": "Map of Ticker -> Target %." } }, "required": ["budget", "portfolio", "prices", "targets"] },
    "get-market-news": { "type": "object", "properties": { "tickers": { "type": "array", "items": { "type": "string" }, "description": "List of ticker symbols to audit." } }, "required": ["tickers"] }
};

var tools = [];

hubApis.forEach(function (api) {
    var toolId = api.name.split("/").pop(); // e.g. "get-market-snapshot"

    // Enterprise Enforcement: Must have "mcp-api" badge
    var hasMcpBadge = false;
    try {
        if (api.apiStyle &&
            api.apiStyle.enumValues &&
            api.apiStyle.enumValues.values &&
            api.apiStyle.enumValues.values.length > 0) {

            // Robust check: Handle both Object (standard JSON) and String (edge cases)
            var styleVal = api.apiStyle.enumValues.values[0];
            var styleStr = (typeof styleVal === 'object') ? JSON.stringify(styleVal) : String(styleVal);

            if (styleStr.indexOf("mcp-api") !== -1) {
                hasMcpBadge = true;
            }
        }
    } catch (e) {
        print("Error checking badge for " + toolId + ": " + e);
    }

    // Strict Filter: Only allow if it has the badge AND we have a schema
    if (hasMcpBadge && SCHEMAS[toolId]) {
        var mcpName = toolId.replace(/\-/g, "_"); // e.g. "get_market_snapshot"

        tools.push({
            "name": mcpName,
            "description": api.description || api.displayName,
            "inputSchema": SCHEMAS[toolId]
        });
    } else {
        print("Skipping tool " + toolId + " (Badge: " + hasMcpBadge + ", Schema: " + !!SCHEMAS[toolId] + ")");
    }
});

var toolsResponse = { "tools": tools };
context.setVariable("response.content", JSON.stringify(toolsResponse));
context.setVariable("response.header.Content-Type", "application/json");
