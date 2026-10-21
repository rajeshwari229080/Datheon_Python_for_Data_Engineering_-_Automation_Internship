"""Currency and numeric compensation parser.
Extracts numeric salary ranges and preserves original currency codes without unauthorized FX conversion.
"""
import re
from typing import Any, Optional, Tuple


class CurrencyParser:
    """Parses raw salary and currency text into numeric ranges and ISO/symbol currency codes."""

    CURRENCY_SYMBOLS = {
        "$": "USD",
        "USD": "USD",
        "US$": "USD",
        "£": "GBP",
        "GBP": "GBP",
        "€": "EUR",
        "EUR": "EUR",
        "₹": "INR",
        "INR": "INR",
        "RS": "INR",
        "C$": "CAD",
        "CAD": "CAD",
        "A$": "AUD",
        "AUD": "AUD",
        "¥": "JPY",
        "JPY": "JPY"
    }

    @classmethod
    def detect_currency(cls, text: str) -> str:
        """Detect currency code from text, defaulting to USD."""
        if not text:
            return "USD"
        upper = text.upper()
        for symbol, code in cls.CURRENCY_SYMBOLS.items():
            if symbol.upper() in upper:
                return code
        return "USD"

    @classmethod
    def parse_salary_range(
        cls, salary_str: Any
    ) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Parse salary text into (salary_min, salary_max, currency).
        
        Examples:
            '$120,000 - $145,000' -> (120000.0, 145000.0, 'USD')
            'USD 110,000 - 130,000' -> (110000.0, 130000.0, 'USD')
            '£85,000 - £105,000' -> (85000.0, 105000.0, 'GBP')
            '₹2,500,000 - ₹3,500,000' -> (2500000.0, 3500000.0, 'INR')
            '$160,000+' -> (160000.0, 160000.0, 'USD')
            'Competitive' -> (None, None, None)
        """
        if salary_str is None or str(salary_str).strip() == "":
            return None, None, None

        raw = str(salary_str).strip()
        currency = cls.detect_currency(raw)

        # Remove currency symbols and word indicators
        clean_text = raw
        for sym in cls.CURRENCY_SYMBOLS.keys():
            clean_text = re.sub(re.escape(sym), "", clean_text, flags=re.IGNORECASE)

        # Handle 'k' notation (e.g. 120k -> 120000)
        def replace_k(match):
            val = float(match.group(1)) * 1000
            return str(int(val))

        clean_text = re.sub(r"(\d+(?:\.\d+)?)\s*[kK]\b", replace_k, clean_text)

        # Match all number groups (stripping commas/dots used as thousand separators)
        # Regex captures sequences of digits optionally separated by commas
        number_tokens = re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b|\b\d+\b", clean_text)
        numbers = []
        for token in number_tokens:
            token_clean = token.replace(",", "")
            try:
                num = float(token_clean)
                # Filter out unrealistic small years or tiny hourly rates if annual expected
                if num > 0:
                    numbers.append(num)
            except ValueError:
                continue

        if not numbers:
            return None, None, None

        if len(numbers) == 1:
            return numbers[0], numbers[0], currency
        else:
            return min(numbers[0], numbers[1]), max(numbers[0], numbers[1]), currency
