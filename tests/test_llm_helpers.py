import unittest
from src.utils.llm_helpers import extract_json_from_text

class TestLLMHelpers(unittest.TestCase):
    
    def test_simple_json(self):
        text = '{"key": "value"}'
        result = extract_json_from_text(text)
        self.assertEqual(result, {"key": "value"})

    def test_simple_list(self):
        text = '[{"key": "value"}]'
        result = extract_json_from_text(text)
        self.assertEqual(result, [{"key": "value"}])

    def test_markdown_block(self):
        text = """
        Here is the data:
        ```json
        {"data": [1, 2, 3]}
        ```
        """
        result = extract_json_from_text(text)
        self.assertEqual(result, {"data": [1, 2, 3]})

    def test_markdown_no_lang(self):
        text = """
        ```
        {"a": 1}
        ```
        """
        result = extract_json_from_text(text)
        self.assertEqual(result, {"a": 1})

    def test_mixed_text(self):
        text = """
        Step 1: Analyze [ticker]
        Step 2: Decide
        
        Output:
        [
            {"ticker": "ABC", "signal": "BUY"}
        ]
        
        Final thought.
        """
        result = extract_json_from_text(text)
        self.assertEqual(result, [{"ticker": "ABC", "signal": "BUY"}])

    def test_nested_brackets_text(self):
        # This is the case that failed the regex
        text = """
        Analysis for [XYZ]: Good.
        Using tool [get_prices].
        
        [
            {"id": 1}
        ]
        """
        result = extract_json_from_text(text)
        self.assertEqual(result, [{"id": 1}])
        
    def test_malformed_json_ignored(self):
        text = """
        [This is not json]
        But this is:
        {"valid": true}
        """
        result = extract_json_from_text(text)
        self.assertEqual(result, {"valid": True})

    def test_fallback_parsing(self):
        from src.utils.llm_helpers import parse_structured_text
        text = """
        Investment Agent Run - Executive Summary

        BAJFINANCE

        📰 News: No significant negative news identified; governance risk below 8.
        📊 Financials: Profits stable; 48753600000.0, 46996100000.0, 44795700000.0.
        ✅ Decision: Approved for allocation.

        TATAELXSI

        📰 News: No significant negative news identified; governance risk below 8.
        📊 Financials: Declining profits for two consecutive quarters; 1088922000.0, 1443677000.0, 1724185000.0.
        ❌ Decision: Excluded from allocation due to declining profits.
        """
        results = parse_structured_text(text)
        self.assertEqual(len(results), 2)
        
        self.assertEqual(results[0]['ticker'], 'BAJFINANCE')
        self.assertEqual(results[0]['signal'], 'BUY')
        self.assertIn("Profits stable", results[0]['reason'])
        
        self.assertEqual(results[1]['ticker'], 'TATAELXSI')
        self.assertEqual(results[1]['signal'], 'SELL')
        self.assertIn("Declining profits", results[1]['reason'])

if __name__ == '__main__':
    unittest.main()
