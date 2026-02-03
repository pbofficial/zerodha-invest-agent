var path = context.getVariable("proxy.pathsuffix");

var mapping = {
    "/get_market_snapshot": "https://get-portfolio-tanlcp3fpq-uk.a.run.app/",
    "/calculate_orders": "https://calculate-allocations-tanlcp3fpq-uk.a.run.app/",
    "/check_financial_health": "https://check-financial-health-tanlcp3fpq-uk.a.run.app/",
    "/get_market_news": "https://get-market-news-tanlcp3fpq-uk.a.run.app/"
};

if (mapping[path]) {
    context.setVariable("target.url", mapping[path]);
    context.setVariable("target.copy.pathsuffix", false);
    context.setVariable("target.copy.path.suffix", false);
}
