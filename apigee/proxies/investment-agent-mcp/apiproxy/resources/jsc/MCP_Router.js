var requestContent = context.getVariable("request.content");
if (requestContent) {
    var reqObj = JSON.parse(requestContent);
    if (reqObj.method === "tools/call" && reqObj.params && reqObj.params.name) {
        context.setVariable("mcp.tool_name", reqObj.params.name);
        context.setVariable("request.content", JSON.stringify(reqObj.params.arguments));
        print("MCP Routing to: " + reqObj.params.name);
    }
}
