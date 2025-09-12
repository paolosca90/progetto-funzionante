#!/usr/bin/env python3
"""
Debug script per identificare la specifica inconsistenza SELL header vs HOLD description
"""
import asyncio
import sys
import logging
import re

# Add current directory to Python path  
sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO)

async def debug_hold_inconsistency():
    """Debug specifico per inconsistenza SELL vs HOLD description"""
    print("=== DEBUG SELL HEADER vs HOLD DESCRIPTION ===\n")
    
    # L'utente ha riportato questo testo specifico:
    user_reported_text = """
    📉 SELL
    Segnale di vendita
    70% Confidence
    Entry Price 46028.0500
    Stop Loss 45990.0500
    Take Profit 46066.0500
    Risk/Reward 1:1.00
    🤖 AI Analysis
    Il segnale "HOLD" per US30_USD deriva da un conflitto tra indicatori tecnici e aspettative di mercato.
    """
    
    print("PROBLEMA RIPORTATO:")
    print("- Header: 📉 SELL con 70% Confidence")  
    print("- AI Analysis: 'Il segnale \"HOLD\" per US30_USD'")
    print("- Questo indica che header e AI analysis usano dati diversi")
    
    print("\n1. Analizzando la logica di generazione...")
    
    try:
        from advanced_signal_analyzer import AdvancedSignalAnalyzer
        
        analyzer = AdvancedSignalAnalyzer(
            oanda_api_key='test_key',
            gemini_api_key='test_key'
        )
        
        # Check se il metodo _generate_ai_reasoning usa signal_data['direction']
        import inspect
        reasoning_source = inspect.getsource(analyzer._generate_ai_reasoning)
        
        # Find onde viene usato signal_data['direction']
        direction_usage = re.findall(r"signal_data\['direction'\]", reasoning_source)
        print(f"   signal_data['direction'] usage found: {len(direction_usage)} occurrences")
        
        # Check se c'è riferimento diretto a direction parameter
        if "signal_it = signal_translation.get(signal_data['direction']" in reasoning_source:
            print("   [OK] AI reasoning uses signal_data['direction'] for Italian translation")
        else:
            print("   [ERROR] AI reasoning might not be using signal_data['direction']")
        
        # Check se c'è testo che costruisce dinamicamente le frasi
        if 'Il segnale' in reasoning_source:
            print("   [WARNING] Found 'Il segnale' text construction in AI reasoning")
        else:
            print("   [OK] No hardcoded 'Il segnale' text found")
        
        print("\n2. Possibili cause del problema:")
        print("   A. signal_data['direction'] contiene 'HOLD' ma header mostra 'SELL'")
        print("   B. Due processi diversi determinano header vs description")  
        print("   C. Cache o dati obsoleti nella description")
        print("   D. Template AI che sovrascrive signal_data['direction']")
        
        print("\n3. Controllando il flusso di generazione...")
        
        # Check l'ordine delle operazioni nel analyze_symbol method
        analyze_source = inspect.getsource(analyzer.analyze_symbol)
        
        # Find dove viene creato signal_data e dove viene chiamato _generate_ai_reasoning
        if "_generate_signal_from_analysis" in analyze_source and "_generate_ai_reasoning" in analyze_source:
            print("   [OK] Both signal generation and AI reasoning are called in sequence")
            
            # Check l'ordine
            signal_gen_pos = analyze_source.find("_generate_signal_from_analysis")
            ai_reasoning_pos = analyze_source.find("_generate_ai_reasoning")
            
            if signal_gen_pos < ai_reasoning_pos:
                print("   [OK] signal_data is generated BEFORE AI reasoning")
            else:
                print("   [WARNING] AI reasoning might be called before signal_data generation")
        
        print("\n4. Raccomandazioni per il debug:")
        print("   1. Aggiungi logging per signal_data['direction'] prima di AI reasoning")
        print("   2. Verifica che non ci sia cache dei risultati AI")
        print("   3. Controlla se sentiment analysis sta modificando direction dopo AI generation")
        print("   4. Verifica che il template AI non contenga testo HOLD hardcoded")
        
        print("\n5. Fix suggerito:")
        print("   - Aggiungi logging dettagliato del signal_data['direction'] value")
        print("   - Assicurati che AI reasoning use sempre signal_data['direction']")
        print("   - Non generare mai testo AI con signal type hardcoded")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(debug_hold_inconsistency())