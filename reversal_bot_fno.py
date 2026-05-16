import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
import json
import pytz
from datetime import datetime
import concurrent.futures

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
LOG_FILE = "trade_performance_log.csv"
POSITIONS_FILE = "active_positions_reversal.json"
IST = pytz.timezone('Asia/Kolkata')

# UPDATED F&O UNIVERSE (MAY 2026) - Fixed Ticker Mismatches
SYMBOLS = [
    "^NSEI", "^NSEBANK", "360ONE.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS", 
    "ADANIENSOL.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANIPOWER.NS", "ALKEM.NS", 
    "AMBER.NS", "AMBUJACEM.NS", "ANGELONE.NS", "APLAPOLLO.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", 
    "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", 
    "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", 
    "BANKBARODA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", 
    "BOSCHLTD.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CAMPUS.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", 
    "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS", 
    "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "CYIENT.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", 
    "DELHIVERY.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", 
    "EXIDEIND.NS", "FEDERALBNK.NS", "FORTIS.NS", "GAIL.NS", "GLENMARK.NS", "GMRAIRPORT.NS", 
    "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", 
    "HAVELLS.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HFCL.NS", "HINDALCO.NS", 
    "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", 
    "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", 
    "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IRCTC.NS", "IRFC.NS", "ITC.NS", 
    "JINDALSTEL.NS", "JSL.NS", "JSWENERGY.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KAYNES.NS", "KOTAKBANK.NS", 
    "L&TFH.NS", "LALPATHLAB.NS", "LICHSGFIN.NS", "LICI.NS", "LT.NS", "LTIMINDRE.NS", "LTTS.NS", "LUPIN.NS", 
    "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MAXHEALTH.NS", "MCX.NS", "METROPOLIS.NS", 
    "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", 
    "NAVINFLUOR.NS", "NESTLEIND.NS", "NHPC.NS", "NMDC.NS", "NTPC.NS", "NYKAA.NS", "OBEROIRLTY.NS", 
    "OFSS.NS", "OIL.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", 
    "PHOENIXLTD.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERTGRID.NS", "PVRINOX.NS", 
    "RECLTD.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", 
    "SHRIRAMFIN.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS", "TATACHEM.NS", 
    "TATACOMM.NS", "TATACONSUM.NS", "TATAELXSI.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", 
    "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TRIDENT.NS", "TVSMOTOR.NS", 
    "UBL.NS", "ULTRACEMCO.NS", "UNITDSPR.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "YESBANK.NS", "ZEEL.NS"
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_fvg(df):
    if len(df) < 3: return None, 0, 0
    c1, c3 = df.iloc[-3], df.iloc[-1]
    # Fixed FVG logic: checks for price gaps between C1 and C3
    if c1['High'] < c3['Low']: return "BULLISH", c1['High'], c3['Low']
    if c1['Low'] > c3['High']: return "BEARISH", c3['High'], c1['Low']
    return None, 0, 0

def fetch_data(s, p, i):
    try:
        df = yf.download(s, period=p, interval=i, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['EMA33'] = df['Close'].ewm(span=33, adjust=False).mean()
        # ATR Calculation for Volatility-based Exit
        hl = df['High'] - df['Low']
        hcp = abs(df['High'] - df['Close'].shift())
        lcp = abs(df['Low'] - df['Close'].shift())
        df['ATR'] = pd.concat([hl, hcp, lcp], axis=1).max(axis=1).rolling(14).mean()
        return df
    except: return None

def process_symbol(s, positions):
    df_d = fetch_data(s, "10d", "1d")
    df_15 = fetch_data(s, "3d", "15m")
    if df_d is None or df_15 is None: return None

    d_fvg_type, d_min, d_max = get_fvg(df_d)
    m15, m15p = df_15.iloc[-1], df_15.iloc[-2]
    cp, ema33, atr = float(m15['Close']), float(m15['EMA33']), float(m15['ATR'])

    is_buy = (d_fvg_type == "BULLISH" and m15['Low'] <= d_max and cp > m15p['High'])
    is_sell = (d_fvg_type == "BEARISH" and m15['High'] >= d_min and cp < m15p['Low'])

    if (is_buy or is_sell) and s not in positions:
        side = "BUY" if is_buy else "SELL"
        rank = "🔥 JACKPOT" if (side == "BUY" and cp < ema33) or (side == "SELL" and cp > ema33) else "💎 ELITE"
        
        # Risk management using ATR (min 0.3% move)
        risk = max(atr, cp * 0.003) 
        targets = [round(cp + (risk * r) if side == "BUY" else cp - (risk * r), 2) for r in [1.5, 3, 5]]
        sl = round(cp - risk if side == "BUY" else cp + risk, 2)

        msg = (f"{rank}: {s.replace('.NS','')}\n"
               f"---------------------------\n"
               f"📍 HTF: Daily {d_fvg_type} FVG\n"
               f"🔥 {side} @ {cp:.2f}\n"
               f"🎯 T1: {targets[0]} | SL: {sl:.2f}")
        send_telegram(msg)
        return {s: {"Entry": cp, "Targets": targets, "T_Idx": 0, "SL": sl, "Side": side, "Rank": rank}}
    return None

def manage_exits(positions):
    updated = positions.copy()
    for s, d in positions.items():
        df = fetch_data(s, "1d", "1m")
        if df is None: continue
        cp = float(df['Close'].iloc[-1])
        side, entry, targets, idx = d['Side'], d['Entry'], d['Targets'], d['T_Idx']
        pts = round(cp - entry if side == "BUY" else entry - cp, 2)
        pct = round((pts / entry) * 100, 2)

        if (side == "BUY" and cp >= targets[idx]) or (side == "SELL" and cp <= targets[idx]):
            if idx < 2:
                d['T_Idx'] += 1
                d['SL'] = entry 
                send_telegram(f"🎯 T{idx+1} HIT: {s}\nCaptured: {pts} pts ({pct}%)\n🛡️ SL at Entry.")
                updated[s] = d
            else:
                send_telegram(f"🏁 FINAL TARGET: {s}\nTotal: {pts} pts ({pct}%)")
                with open(LOG_FILE, 'a') as f: f.write(f"{datetime.now(IST)},{s},{side},{d['Rank']},{entry},{cp},{pts},{pct}\n")
                del updated[s]
        elif (side == "BUY" and cp <= d['SL']) or (side == "SELL" and cp >= d['SL']):
            send_telegram(f"🛑 EXIT: {s}\nPoints: {pts:+.2f} ({pct}%)")
            with open(LOG_FILE, 'a') as f: f.write(f"{datetime.now(IST)},{s},{side},{d['Rank']},{entry},{cp},{pts},{pct}\n")
            del updated[s]
    return updated

if __name__ == "__main__":
    if not os.path.exists(POSITIONS_FILE): 
        with open(POSITIONS_FILE, 'w') as f: json.dump({}, f)
    with open(POSITIONS_FILE, 'r') as f: pos = json.load(f)
    
    pos = manage_exits(pos)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda s: process_symbol(s, pos), SYMBOLS))
        for r in results:
            if r: pos.update(r)
    with open(POSITIONS_FILE, 'w') as f: json.dump(pos, f, indent=4)
