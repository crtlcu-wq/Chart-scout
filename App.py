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
    """Normalizza e pulisce le colonne di qualsiasi DataFrame yfinance"""
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(col[0]).strip() if isinstance(col, tuple) else str(col).strip() for col in df.columns]
    return df

def trova_colonna_close(df):
    """Trova la colonna 'Close' indipendentemente dalle maiuscole/minuscole"""
    for col in df.columns:
        if col.lower() == 'close':
            return col
    return None

def scarica_storico(ticker, period, interval):
    """Download ultra-robusto con gestione specifica per ticker difficili"""
    try:
        time.sleep(0.12) # Pausa di sicurezza anti-blocco Yahoo
        
        # Tentativo primario con yf.download (più stabile sui singoli ticker)
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        df = pulisci_colonne(df)
        
        c_col = trova_colonna_close(df)
        if df is not None and not df.empty and c_col is not None:
            return df
            
        # Fallback secondario tramite Ticker object se il primo fallisce
        t = yf.Ticker(ticker)
        df_alt = t.history(period=period, interval=interval, auto_adjust=True)
        df_alt = pulisci_colonne(df_alt)
        c_col_alt = trova_colonna_close(df_alt)
        if df_alt is not None and not df_alt.empty and c_col_alt is not None:
            return df_alt
            
    except Exception:
        pass
    return pd.DataFrame()

def calcola_score_macro(df):
    c_col = trova_colonna_close(df)
    if df is None or df.empty or c_col is None or len(df) < 200:
        return 0.0
    temp_df = df.dropna(subset=[c_col])
    if len(temp_df) < 200:
        return 0.0
        
    mm9 = float(temp_df[c_col].rolling(window=9).mean().iloc[-1])
    mm20 = float(temp_df[c_col].rolling(window=20).mean().iloc[-1])
    mm50 = float(temp_df[c_col].rolling(window=50).mean().iloc[-1])
    mm100 = float(temp_df[c_col].rolling(window=100).mean().iloc[-1])
    mm200 = float(temp_df[c_col].rolling(window=200).mean().iloc[-1])
    prezzo = float(temp_df[c_col].iloc[-1])

    if prezzo >= mm200: return 100.0
    elif prezzo >= mm100: return 80.0
    elif prezzo >= mm50: return 40.0
    elif prezzo >= mm20: return 20.0
    elif prezzo >= mm9: return 20.0
    else: return 0.0

def calcola_score_intraday(df):
    c_col = trova_colonna_close(df)
    if df is None or df.empty or c_col is None or len(df) < 20:
        return 0.0
    temp_df = df.dropna(subset=[c_col])
    if len(temp_df) < 20:
        return 0.0
        
    n = len(temp_df)
    w9 = min(9, n // 5)
    w20 = min(20, n // 3)
    w50 = min(50, n // 2)
    
    mm9 = float(temp_df[c_col].rolling(window=max(2, w9)).mean().iloc[-1])
    mm20 = float(temp_df[c_col].rolling(window=max(3, w20)).mean().iloc[-1])
    mm50 = float(temp_df[c_col].rolling(window=max(4, w50)).mean().iloc[-1])
    prezzo = float(temp_df[c_col].iloc[-1])

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
    with st.spinner("Analisi in corso con protocollo di sicurezza dati..."):
        report = []
        for ticker in tickers:
            ticker_pulito = ticker.replace('.MI', '')
            risultati = {"Ticker": ticker_pulito}
            try:
                # 1. Weekly
                df_wk = scarica_storico(ticker, period="max", interval="1wk")
                risultati['Weekly'] = f"{int(calcola_score_macro(df_wk))}%"
                
                # 2. Daily
                df_d = scarica_storico(ticker, period="max", interval="1d")
                risultati['Daily'] = f"{int(calcola_score_macro(df_d))}%"
                
                # 3. Intraday (1H e 4H)
                df_1h = scarica_storico(ticker, period="30d", interval="1h")
                c_1h = trova_colonna_close(df_1h)
                if df_1h is not None and not df_1h.empty and c_1h is not None:
                    # Resample sicuro per il 4H
                    df_4h = df_1h.resample('4h').agg({
                        df_1h.columns[0]: 'first', 
                        'High': 'max', 
                        'Low': 'min', 
                        c_1h: 'last'
                    }).dropna()
                    risultati['4H'] = f"{int(calcola_score_intraday(df_4h))}%"
                    risultati['1H'] = f"{int(calcola_score_intraday(df_1h))}%"
                else:
                    risultati['4H'] = "N/A"
                    risultati['1H'] = "N/A"
                    
                # 4. 15M
                df_15m = scarica_storico(ticker, period="30d", interval="15m")
                risultati['15M'] = f"{int(calcola_score_intraday(df_15m))}%"
                
            except Exception:
                pass
            report.append(risultati)
        
        df_final = pd.DataFrame(report).set_index("Ticker")
        df_styled = df_final.style.map(colora_celle)
        
        st.success("Scansione completata con successo!")
        st.dataframe(df_styled, use_container_width=True)
else:
    st.info("Clicca il pulsante sopra per avviare la scansione di tutto il paniere FTSE MIB.")
