import re
import json
import logging

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str):
    """
    Robustly extracts the largest valid JSON object or array from a string.
    Handles:
    - Markdown code blocks (```json ... ```)
    - Mixed text and JSON
    - Nested brackets
    """
    if not text:
        return None

    # 1. Try to find JSON within markdown code blocks first
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    code_blocks = re.findall(code_block_pattern, text)
    
    candidates = []
    
    # Add code block contents as candidates
    for block in code_blocks:
        candidates.append(block)
        
    # Add the raw text as a candidate (in case no code blocks or loose JSON)
    candidates.append(text)
    
    best_candidate = None
    max_len = 0
    
    for candidate in candidates:
        # Find potential JSON boundaries
        # We look for the outer-most brackets
        stack = []
        start_index = -1
        
        for i, char in enumerate(candidate):
            if char == '{' or char == '[':
                if len(stack) == 0:
                   start_index = i
                stack.append(char)
            elif char == '}' or char == ']':
                if len(stack) > 0:
                    last = stack[-1]
                    if (char == '}' and last == '{') or (char == ']' and last == '['):
                        stack.pop()
                        if len(stack) == 0:
                            # Potential Complete JSON
                            json_str = candidate[start_index : i+1]
                            try:
                                # Validate
                                parsed = json.loads(json_str)
                                # We prefer the longest valid JSON found (likely the main payload)
                                if len(json_str) > max_len:
                                    max_len = len(json_str)
                                    best_candidate = parsed
                            except json.JSONDecodeError:
                                pass # Continue searching
                    else:
                        # Mismatched, reset (simple heuristic)
                        stack = []
                        start_index = -1
    
    return best_candidate

def normalize_ticker(t: str):
    """Consistent ticker normalization across Agent and Tools."""
    if not t: return ""
    # Standard: Remove exchange prefix (NSE:), uppercase, remove markdown/AI artifacts
    t = t.split(":")[-1].upper()
    # Strip common AI formatting artifacts: *, `, [, ], ', "
    t = re.sub(r"[\*`\[\]\'\"]", "", t)
    return t.strip()

def parse_structured_text(text: str) -> list:
    """
    Fallback: Scrapes structured decision text if JSON extraction fails.
    Handles various AI summary formats seen in logs.
    """
    if not text: return []
    
    results = []
    
    # Improved Pattern:
    # 1. Newline or start of string
    # 2. Optional bullet/star/bolding
    # 3. Ticker (Caps + possible numbers/dashes, 3-15 chars)
    # 4. Optional bolding/colon
    # 5. Rationale/Decision text until next ticker or end of line
    
    pattern = r"(?:^|\n)[ \t]*(?:\*|-)*\s*(?:\*\*)?\s*([A-Z0-9\-\:]{3,15})\s*(?:\*\*)?\s*:?\s*(.*?)(?=\n\s*(?:\*|-|(?:\*\*)?[A-Z0-9]{3,})|$)"
    
    matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
    
    for m in matches:
        raw_ticker = m.group(1).upper()
        ticker = normalize_ticker(raw_ticker)
        raw_decision = m.group(2).lower()
        
        # Filter noise words that look like tickers
        if ticker in ["NEWS", "FINANCIALS", "DECISION", "EXECUTIVE", "SUMMARY", "AGENT", "RUN", "LOGIC", "ANALYSIS", "REPORT"]:
            continue
            
        signal = "HOLD"
        # Extract signal from text
        if any(k in raw_decision for k in ["strong buy", "strong_buy", "🌟"]):
            signal = "STRONG_BUY"
        elif any(k in raw_decision for k in ["approved", "buy", "✅", "include"]):
            signal = "BUY"
        elif any(k in raw_decision for k in ["accumulate", "add", "➕"]):
            signal = "ACCUMULATE"
        elif any(k in raw_decision for k in ["exclude", "sell", "warning", "⚠️", "risk", "🔴"]):
            signal = "SELL"
        elif any(k in raw_decision for k in ["hold", "safe", "stable", "wait", "⏸️", "⚪"]):
            signal = "HOLD"
            
        # Clean up reason
        reason = m.group(2).strip()
        # Remove common bullet prefix artifacts if any
        reason = re.sub(r"^[ \t]*[\[\(\']?.*?[\]\)\']?\s*", "", reason) 
        if len(reason) > 300: reason = reason[:297] + "..."
            
        results.append({
            "ticker": raw_ticker, # Keep raw for specific matching, main logic will normalize again
            "signal": signal,
            "reason": reason,
            "quantity": 0 
        })
            
    return results
