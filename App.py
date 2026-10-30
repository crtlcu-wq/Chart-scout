import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
import time

# Configurazione della pagina ottimizzata per mobile
st.set_page_config(
    page_title="Chart Scout MIB",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

warnings.simplefilter(action='ignore', category=FutureWarning)

# Lista completa dei titoli del FTSE MIB
tickers = [
    "A2A.MI", "AMP.MI", "AZM.MI", "BGN.MI", "BMED.MI", "BMPS.MI", "BAMI.MI", 
    "BPE.MI", "CPR.MI", "DIA.MI", "ENEL.MI", "ENI.MI", "ERG.MI", "RACE.MI", 
    "REC.MI", "G.MI", "HER.MI", "ISP.MI", "INW.MI", "IG.MI", "LDO.MI", 
    "MB.MI", "MONC.MI", "NEXI.MI", "PIRC.MI", "PST.MI", "PRY.MI", "SPM.MI", 
    "SRG.MI", "STLAM.MI", "STM.MI", "TIT.MI", "TEN.MI", "TRN.MI", "UCG.MI", 
    "UNI.MI", "IVG.MI"
]

def pulisci_colonne(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def scarica_storico(ticker, period, interval):
    """Funzione sicura con pausa anti-blocco e gestione ticker a singola lettera"""
    try:
        time.sleep(0.12) # Pausa di sicurezza per Yahoo Finance
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df is not None and not df.empty:
            return pulisci_colonne(df)
    except Exception:
        pass
    return pd.DataFrame()

def calcola_score_macro(df):
    if df is None or len(df) < 200:
        return 0.0
    df = df.dropna(subset=['Close'])
    mm9 = float(df['Close'].rolling(window=9).mean().iloc[-1])
    mm20 = float(df['Close'].rolling(window=20).mean().iloc[-1])
    mm50 = float(df['Close'].rolling(window=50).mean().iloc[-1])
    mm100 = float(df['Close'].rolling(window=100).mean().iloc[-1])
    mm200 = float(df['Close'].rolling(window=200).mean().iloc[-1])
    prezzo = float(df['Close'].iloc[-1])

    if prezzo >= mm200: return 100.0
    elif prezzo >= mm100: return 80.0
    elif prezzo >= mm50: return 40.0
    elif prezzo >= mm20: return 20.0
    elif prezzo >= mm9: return 20.0
    else: return 0.0

def calcola_score_intraday(df):
    if df is None or len(df) < 20: # Soglia flessibile per intraday
        return 0.0
    df = df.dropna(subset=['Close'])
    n = len(df)
    w9 = min(9, n // 5)
    w20 = min(20, n // 3)
    w50 = min(50, n // 2)
    mm9 = float(df['Close'].rolling(window=max(2, w9)).mean().iloc[-1])
    mm20 = float(df['Close'].rolling(window=max(3, w20)).mean().iloc[-1])
    mm50 = float(df['Close'].rolling(window=max(4, w50)).mean().iloc[-1])
    prezzo = float(df['Close'].iloc[-1])

    if prezzo >= mm50: return 100.0
    elif prezzo >= mm20: return 60.0
    elif prezzo >= mm9: return 30.0
    else: return 0.0

def colora_celle(val):
    if val == "100%":
        return 'background-color: #1b5e20; color: white; font-weight: bold;'
    elif val in ["80%", "60%"]:
        return 'background-color: #2e7d32; color: white;'
    elif val in ["40%", "30%"]:
        return 'background-color: #fbc02d; color: black;'
    elif val == "20%":
        return 'background-color: #e65100; color: white;'
    elif val == "0%":
        return 'background-color: #b71c1c; color: white;'
    return ''

# --- INTERFACCIA UTENTE MOBILE ---
st.title("🎯 Chart Scout MIB")
st.markdown("Plancia Tattica Operativa - Indice Completo (Weekly ➔ 15M)")

if st.button("🚀 Esegui Scansione Intero Indice", use_container_width=True):
    with st.spinner("Analisi in corso con connessione ottimizzata..."):
        report = []
        for ticker in tickers:
            ticker_pulito = ticker.replace('.MI', '')
            risultati = {"Ticker": ticker_pulito}
            try:
                # Gestione speciale per forzare il corretto recupero di Generali su Milano
                fetch_ticker = "IT0000062072.MI" if ticker == "G.MI" else ticker

                # 1. Weekly
                df_wk = scarica_storico(fetch_ticker, period="max", interval="1wk")
                risultati['Weekly'] = f"{int(calcola_score_macro(df_wk))}%"
                
                # 2. Daily
                df_d = scarica_storico(fetch_ticker, period="max", interval="1d")
                risultati['Daily'] = f"{int(calcola_score_macro(df_d))}%"
                
                # 3. Intraday (1H ridotto a 30d per stabilità)
                df_1h = scarica_storico(fetch_ticker, period="30d", interval="1h")
                if not df_1h.empty:
                    df_4h = df_1h.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
                    risultati['4H'] = f"{int(calcola_score_intraday(df_4h))}%"
                    risultati['1H'] = f"{int(calcola_score_intraday(df_1h))}%"
                else:
                    risultati['4H'] = "N/A"
                    risultati['1H'] = "N/A"
                    
                # 4. 15M (ridotto a 30d per stabilità)
                df_15m = scarica_storico(fetch_ticker, period="30d", interval="15m")
                risultati['15M'] = f"{int(calcola_score_intraday(df_15m))}%"
                
            except Exception:
                pass
            report.append(risultati)
        
        df_final = pd.DataFrame(report).set_index("Ticker")
        df_styled = df_final.style.map(colora_celle)
        
        st.success("Scansione completata con successo!")
        st.dataframe(df_styled, use_container_width=True)
else:
    st.info("Ticca il pulsante sopra per avviare la scansione di tutto il paniere FTSE MIB.")
