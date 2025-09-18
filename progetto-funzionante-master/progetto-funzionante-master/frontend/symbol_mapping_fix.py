#!/usr/bin/env python3
"""
Unified symbol mapping between OANDA and frontend formats
"""

def create_unified_symbol_mappings():
    """Create consistent symbol mappings"""
    
    # OANDA format to Frontend format
    oanda_to_frontend = {
        # Major Forex Pairs
        'EUR_USD': 'EURUSD',
        'GBP_USD': 'GBPUSD', 
        'USD_JPY': 'USDJPY',
        'AUD_USD': 'AUDUSD',
        'USD_CAD': 'USDCAD',
        'NZD_USD': 'NZDUSD',
        'EUR_GBP': 'EURGBP',
        
        # Cross Pairs
        'EUR_AUD': 'EURAUD',
        'EUR_CHF': 'EURCHF',
        'GBP_JPY': 'GBPJPY',
        'AUD_JPY': 'AUDJPY',
        'EUR_JPY': 'EURJPY',
        'GBP_AUD': 'GBPAUD',
        'USD_CHF': 'USDCHF',
        'CHF_JPY': 'CHFJPY',
        'AUD_CAD': 'AUDCAD',
        'CAD_JPY': 'CADJPY',
        'EUR_CAD': 'EURCAD',
        'GBP_CAD': 'GBPCAD',
        
        # Precious Metals
        'XAU_USD': 'GOLD',
        'XAG_USD': 'SILVER',
        
        # Major Indices
        'US30_USD': 'US30',
        'NAS100_USD': 'NAS100',
        'SPX500_USD': 'SPX500',
        'DE30_EUR': 'DE30'
    }
    
    # Frontend format to OANDA format (reverse mapping)
    frontend_to_oanda = {v: k for k, v in oanda_to_frontend.items()}
    
    return oanda_to_frontend, frontend_to_oanda

def get_frontend_symbol(oanda_symbol):
    """Convert OANDA symbol to frontend format"""
    oanda_to_frontend, _ = create_unified_symbol_mappings()
    return oanda_to_frontend.get(oanda_symbol, oanda_symbol.replace("_", ""))

def get_oanda_symbol(frontend_symbol):
    """Convert frontend symbol to OANDA format"""
    _, frontend_to_oanda = create_unified_symbol_mappings()
    return frontend_to_oanda.get(frontend_symbol.upper(), frontend_symbol.upper())

def test_symbol_mappings():
    """Test the symbol mapping functions"""
    print("TESTING SYMBOL MAPPINGS")
    print("="*50)
    
    test_oanda_symbols = [
        'EUR_USD', 'GBP_JPY', 'XAU_USD', 'US30_USD', 'NAS100_USD'
    ]
    
    test_frontend_symbols = [
        'EURUSD', 'GBPJPY', 'GOLD', 'US30', 'NAS100'
    ]
    
    print("OANDA -> Frontend:")
    for symbol in test_oanda_symbols:
        frontend = get_frontend_symbol(symbol)
        print(f"  {symbol} -> {frontend}")
    
    print("\nFrontend -> OANDA:")
    for symbol in test_frontend_symbols:
        oanda = get_oanda_symbol(symbol)
        print(f"  {symbol} -> {oanda}")
    
    print("\nRound-trip test:")
    for symbol in test_oanda_symbols:
        frontend = get_frontend_symbol(symbol)
        back_to_oanda = get_oanda_symbol(frontend)
        match = "OK" if back_to_oanda == symbol else "FAIL"
        print(f"  {symbol} -> {frontend} -> {back_to_oanda} {match}")

if __name__ == "__main__":
    test_symbol_mappings()
