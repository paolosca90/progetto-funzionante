"""
Unified Symbol Mapping Functions
Consistent symbol mappings between OANDA and frontend formats
"""

from typing import Dict, Tuple


def create_unified_symbol_mappings() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Create consistent symbol mappings between OANDA and frontend formats"""

    # OANDA format to Frontend format
    oanda_to_frontend = {
        # Major Forex Pairs
        'EUR_USD': 'EURUSD', 'GBP_USD': 'GBPUSD', 'USD_JPY': 'USDJPY',
        'AUD_USD': 'AUDUSD', 'USD_CAD': 'USDCAD', 'NZD_USD': 'NZDUSD',
        'EUR_GBP': 'EURGBP',

        # Cross Pairs
        'EUR_AUD': 'EURAUD', 'EUR_CHF': 'EURCHF', 'GBP_JPY': 'GBPJPY',
        'AUD_JPY': 'AUDJPY', 'EUR_JPY': 'EURJPY', 'GBP_AUD': 'GBPAUD',
        'USD_CHF': 'USDCHF', 'CHF_JPY': 'CHFJPY', 'AUD_CAD': 'AUDCAD',
        'CAD_JPY': 'CADJPY', 'EUR_CAD': 'EURCAD', 'GBP_CAD': 'GBPCAD',

        # Precious Metals
        'XAU_USD': 'GOLD', 'XAG_USD': 'SILVER',

        # Major Indices
        'US30_USD': 'US30', 'NAS100_USD': 'NAS100',
        'SPX500_USD': 'SPX500', 'DE30_EUR': 'DE30'
    }

    # Frontend format to OANDA format (reverse mapping)
    frontend_to_oanda = {v: k for k, v in oanda_to_frontend.items()}

    return oanda_to_frontend, frontend_to_oanda


def get_frontend_symbol(oanda_symbol: str) -> str:
    """Convert OANDA symbol to frontend format"""
    oanda_to_frontend, _ = create_unified_symbol_mappings()
    return oanda_to_frontend.get(oanda_symbol, oanda_symbol.replace("_", ""))


def get_oanda_symbol(frontend_symbol: str) -> str:
    """Convert frontend symbol to OANDA format"""
    _, frontend_to_oanda = create_unified_symbol_mappings()

    # First try direct mapping
    mapped = frontend_to_oanda.get(frontend_symbol.upper())
    if mapped:
        return mapped

    # Handle slash format (EUR/USD -> EUR_USD)
    upper_symbol = frontend_symbol.upper()
    if "/" in upper_symbol:
        upper_symbol = upper_symbol.replace("/", "")

    # Try mapping after removing slash
    mapped = frontend_to_oanda.get(upper_symbol)
    if mapped:
        return mapped

    # Fallback: Try to convert to OANDA format by adding underscore
    # Only for forex pairs (6 characters without underscore)
    if len(upper_symbol) == 6 and upper_symbol.isalpha():
        # Insert underscore after first 3 characters (EUR USD -> EUR_USD)
        return f"{upper_symbol[:3]}_{upper_symbol[3:]}"

    # For other cases, return as-is
    return upper_symbol


def is_valid_symbol(symbol: str) -> bool:
    """Check if symbol is valid and supported"""
    oanda_to_frontend, frontend_to_oanda = create_unified_symbol_mappings()

    # Check if it's a known frontend symbol
    if symbol.upper() in frontend_to_oanda:
        return True

    # Check if it's a known OANDA symbol
    if symbol.upper() in oanda_to_frontend:
        return True

    # Check if it looks like a valid forex pair
    clean_symbol = symbol.upper().replace("/", "").replace("_", "")
    if len(clean_symbol) == 6 and clean_symbol.isalpha():
        return True

    return False


def get_symbol_info(symbol: str) -> Dict[str, str]:
    """Get comprehensive symbol information"""
    frontend_symbol = get_frontend_symbol(symbol) if "_" in symbol else symbol.upper()
    oanda_symbol = get_oanda_symbol(symbol)

    return {
        "frontend_symbol": frontend_symbol,
        "oanda_symbol": oanda_symbol,
        "is_valid": is_valid_symbol(symbol),
        "symbol_type": _get_symbol_type(frontend_symbol)
    }


def _get_symbol_type(symbol: str) -> str:
    """Determine the type of trading symbol"""
    symbol = symbol.upper()

    if symbol in ['GOLD', 'SILVER', 'XAU_USD', 'XAG_USD']:
        return "METAL"
    elif symbol in ['US30', 'NAS100', 'SPX500', 'DE30']:
        return "INDEX"
    elif len(symbol.replace("/", "").replace("_", "")) == 6:
        return "FOREX"
    else:
        return "OTHER"