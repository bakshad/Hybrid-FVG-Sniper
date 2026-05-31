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

# COMPLETE PRODUCTION F&O UNIVERSE
SYMBOLS = [
    "^NSEI", "^NSEBANK", "360ONE.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS", 
    "ADANIENSOL.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANIPOWER.NS", "ALKEM.NS", 
    "AMBER.NS", "AMBUJACEM.NS", "ANGELONE.NS", "APLAPOLLO.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", 
    "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS", 
    "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", 
    "BANKBARODA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", 
    "BOSCHLTD.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS", "CAMPUS.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", 
    "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COCHINSHIP.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS", 
    "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "CYIENT.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", 
    "DELHIVERY.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", 
    "EXIDEIND.NS", "FEDERALBNK.NS", "FORTIS.NS", "GAIL.NS", "GLENMARK.NS", "GMRAIRPORT.NS", "GNFC.NS", 
    "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", 
    "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HFCL.NS", "HINDALCO.NS", "HINDCOPPER.NS", 
    "HINDPETRO.NS", "HINDUNILVR.NS", "HYUNDAI.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDFCFIRSTB.NS", 
    "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", 
    "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IRCTC.NS", "IRFC.NS", "ITC.NS", "JINDALSTEL.NS", "JSL.NS", 
    "JSWENERGY.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KAYNES.NS", "KOTAKBANK.NS", "L&TFH.NS", "LALPATHLAB.NS", 
    "LICHSGFIN.NS", "LICI.NS", "LT.NS", "LTIMINDRE.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", 
    "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MAXHEALTH.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", 
    "MGL.NS", "MOTHERSON.NS", "MOTILALOFS.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NAM-INDIA.NS", 
    "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NHPC.NS", "NMDC.NS", "NTPC.NS", "NYKAA.NS", 
    "OBEROIRLTY.NS", "OFSS.NS", "OIL.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", 
    "PFC.NS", "PHOENIXLTD.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERTGRID.NS", 
    "PVRINOX.NS", "RECLTD.NS", "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", 
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
    if c1['High'] < c3['Low']: return "BULLISH", float(c1['High']), float(c3['Low'])
    if c1['Low'] > c3['High']: return "BEARISH", float(c3['High']), float(c1['Low'])
    return None, 0, 0

def fetch_data(s, p, i):
    try:
        df = yf.download(s, period=p, interval=i, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['EMA33'] = df['Close'].ewm(span=33, adjust=False).mean()
        
        hl = df['High'] - df['Low']
        hcp = abs(df['High'] - df['Close'].shift())
        lcp = abs(df['Low'] - df['Close'].shift())
        df['ATR'] = pd.concat([hl, hcp, lcp], axis=1).max(axis=1).rolling(14).mean()
        return df
    except: return None

def process_symbol(s, positions):
    # Fetch data arrays
    df_d = fetch_data(s, "5d", "1d")
    df_htf = fetch_data(s, "10d", "60m")
    df_15 = fetch_data(s, "3d", "15m")
    
    if df_d is None or df_htf is None or df_15 is None or len(df_d) < 2: return None

    # REFINEMENT 1: STRICT NO-GAP OPEN FILTER
    # Evaluates the opening price of the current daily session against the prior day's close
    prev_close = float(df_d['Close'].iloc[-2])
    today_open = float(df_d['Open'].iloc[-1])
    if abs(today_open - prev_close) / prev_close > 0.0005:  # Filters out any open gap > 0.05%
        return None

    # Calculate Woodies Pivots on yesterday's completed daily candle for structural filtering
    y_high, y_low, y_close = float(df_d['High'].iloc[-2]), float(df_d['Low'].iloc[-2]), float(df_d['Close'].iloc[-2])
    w_pivot = (y_high + y_low + (2 * y_close)) / 4
    s2 = w_pivot - (y_high - y_low)
    s3 = y_low - 2 * (y_high - w_pivot)
    r2 = w_pivot + (y_high - y_low)
    r3 = y_high + 2 * (w_pivot - y_low)

    htf_fvg_type, htf_min, htf_max = get_fvg(df_htf)
    m15 = df_15.iloc[-1]
    cp, atr = float(m15['Close']), float(m15['ATR'])

    buffer = atr * 0.1
    
    # REFINEMENT 3: DOJI/CONTRACTION FILTER 
    # Ensures the candle body represents authentic price expansion, not static compression
    o, c, h, l = float(m15['Open']), float(m15['Close']), float(m15['High']), float(m15['Low'])
    total_range = (h - l) + 1e-9
    body = abs(o - c) + 1e-9
    
    if (body / total_range) < 0.10: # Requires candle body to make up at least 10% of the total range
        return None

    # WICK STRICTNESS RATIO AT 1.5x BODY
    has_bottom_wick = (min(o, c) - l) > (body * 1.5)
    has_top_wick = (h - max(o, c)) > (body * 1.5)

    is_buy = (htf_fvg_type == "BULLISH" and (m15['Low'] <= htf_max + buffer) and (cp > o) and has_bottom_wick)
    is_sell = (htf_fvg_type == "BEARISH" and (m15['High'] >= htf_min - buffer) and (cp < o) and has_top_wick)

    if (is_buy or is_sell) and s not in positions:
        side = "BUY" if is_buy else "SELL"
        
        # REFINEMENT 2: STRUCTURAL WOODIES PIOT "JACKPOT" ALLOCATION
        is_jackpot_buy = (side == "BUY" and cp < s2)
        is_jackpot_sell = (side == "SELL" and cp > r2)
        rank = "🔥 JACKPOT" if (is_jackpot_buy or is_jackpot_sell) else "💎 ELITE"
        
        risk = max(atr, cp * 0.003) 
        targets = [round(cp + (risk * r) if side == "BUY" else cp - (risk * r), 2) for r in [1.5, 3, 5]]
        sl = round(cp - risk if side == "BUY" else cp + risk, 2)

        msg = (f"{rank}: {s.replace('.NS','')}\n"
               f"---------------------------\n"
               f"📍 HTF: 60m {htf_fvg_type} FVG\n"
               f"🔥 {side} @ {cp:.2f}\n"
               f"🎯 T1: {targets[0]} | SL: {sl:.2f}")
        send_telegram(msg)
        return {s: {"Entry": cp, "Targets": targets, "T_Idx": 0, "SL": sl, "Side": side, "Rank": rank}}
    return None

def manage_exits(positions):
    updated = positions.copy()
    for s, d in positions.items():
        df = fetch_data(s, "1d", "1m")
        if df is None or df.empty: continue
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
    
    # REFINEMENT 4: THREAD-SAFE CONCURRENT RESULT COMPILATION
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda s: process_symbol(s, pos), SYMBOLS))
        
        # Thread-safe dictionary dictionary update executed sequentially on the main thread
        for r in results:
            if r: pos.update(r)
            
    with open(POSITIONS_FILE, 'w') as f: json.dump(pos, f, indent=4)
