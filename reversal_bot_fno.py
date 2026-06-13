import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
import json
import pytz
from datetime import datetime
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
LOG_FILE = "trade_performance_log.csv"
POSITIONS_FILE = "active_positions_reversal.json"
HISTORY_FILE = "reversal_candle_history.json"
IST = pytz.timezone('Asia/Kolkata')
DAILY_TRADE_BUDGET = 50000  

# --- HIGH PROBABILITY FILTER GATEKEEPER ---
ONLY_TAKE_JACKPOTS = True  # Set to True to completely filter out non-extreme trades

SYMBOLS = [
    "360ONE.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS", 
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

def get_institutional_fvg(df):
    if len(df) < 4: return None, 0, 0
    c1, c2, c3 = df.iloc[-4], df.iloc[-3], df.iloc[-2]
    
    c2_range = (c2['High'] - c2['Low']) + 1e-9
    c2_body = abs(c2['Open'] - c2['Close'])
    is_displaced = (c2_body / c2_range) >= 0.55
    is_high_volume = float(c2['Volume']) > float(df['Vol_SMA'].iloc[-3])
    
    if is_displaced and is_high_volume:
        if c1['High'] < c3['Low']: return "BULLISH", float(c1['High']), float(c3['Low'])
        if c1['Low'] > c3['High']: return "BEARISH", float(c3['High']), float(c1['Low'])
    return None, 0, 0

def generate_weekly_summary():
    if not os.path.exists(LOG_FILE): return
    try:
        df = pd.read_csv(LOG_FILE)
        if df.empty: return
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        one_week_ago = datetime.now(IST) - pd.Timedelta(days=7)
        weekly_df = df[df['Timestamp'] >= pd.to_datetime(one_week_ago).tz_localize(IST)].copy()
        if weekly_df.empty: return
            
        total_signals = len(weekly_df)
        wins = len(weekly_df[weekly_df['Points'] > 0])
        win_rate = round((wins / total_signals) * 100, 2)
        net_pct = round(weekly_df['Pct'].sum(), 2)
        weekly_df['PnL'] = pd.to_numeric(weekly_df['PnL'], errors='coerce').fillna(0)
        total_pnl_cash = round(weekly_df['PnL'].sum(), 2)
        
        msg = (f"📊 *WEEKLY SWING ENGINE SUMMARY*\n-----------------------------------\n"
               f"🏹 *Closed Positions:* {total_signals}\n🎯 *Win Rate:* {win_rate}%\n"
               f"📈 *Net Return:* {net_pct:+.2f}%\n💰 *Total Paper PnL:* ₹{total_pnl_cash:+,.2f}")
        send_telegram(msg)
    except: pass

def manage_exits(positions, session):
    if not positions: return positions
    active_symbols = list(positions.keys())
    try:
        df_all_live = yf.download(active_symbols, period="1d", interval="5m", group_by='ticker', progress=False, session=session)
        if df_all_live.empty: return positions
    except: return positions
        
    updated = positions.copy()
    for s, d in positions.items():
        try:
            if isinstance(df_all_live.columns, pd.MultiIndex):
                if s in df_all_live.columns.levels[0]: df_s = df_all_live[s].dropna(how='all')
                else: continue
            else: df_s = df_all_live.dropna(how='all')
                
            if df_s.empty: continue
            cp = float(df_s['Close'].iloc[-1])
            side, entry, targets, idx = d['Side'], d['Entry'], d['Targets'], d['T_Idx']
            qty = d.get('Qty', int(DAILY_TRADE_BUDGET // entry))
            
            pts = round(cp - entry if side == "BUY" else entry - cp, 2)
            pct = round((pts / entry) * 100, 2)
            pnl_cash = round(pts * qty, 2)

            if (side == "BUY" and cp >= targets[idx]) or (side == "SELL" and cp <= targets[idx]):
                if idx < 2:
                    d['T_Idx'] += 1
                    d['SL'] = round(entry * 1.001 if side == "BUY" else entry * 0.999, 2)
                    send_telegram(f"🏹 Swing Position Update:\n🎯 T{idx+1} HIT: {s.replace('.NS','')}\nCaptured: {pts} pts ({pct}%)\n🛡️ SL trailing to cost layer.")
                    updated[s] = d
                else:
                    send_telegram(f"🏹 Swing Position Update:\n🏁 FINAL TARGET COMPLETED: {s.replace('.NS','')}\nTotal: {pts} pts ({pct}%)\n💸 Paper Profit: ₹{pnl_cash:+,.2f}")
                    with open(LOG_FILE, 'a') as f: f.write(f"{datetime.now(IST)},{s},{side},{d['Rank']},{entry},{cp},{pts},{pct},{qty},{pnl_cash}\n")
                    del updated[s]
            elif (side == "BUY" and cp <= d['SL']) or (side == "SELL" and cp >= d['SL']):
                send_telegram(f"🏹 Swing Position Update:\n🛑 SL EXIT TRIGGERED: {s.replace('.NS','')}\nPnL: {pts:+.2f} pts ({pct}%)\n💸 Paper Loss: ₹{pnl_cash:+,.2f}")
                with open(LOG_FILE, 'a') as f: f.write(f"{datetime.now(IST)},{s},{side},{d['Rank']},{entry},{cp},{pts},{pct},{qty},{pnl_cash}\n")
                del updated[s]
        except: pass
    return updated

def process_macro_strategy(s, df_d, df_60m, positions, history):
    now_time = datetime.now(IST).time()
    if now_time < datetime.strptime("10:00", "%H:%M").time() or now_time > datetime.strptime("15:00", "%H:%M").time(): return None

    if len(df_d) < 15 or len(df_60m) < 10: return None
    
    m60 = df_60m.iloc[-2]
    candle_id = str(m60.name)
    if s in history and candle_id in history[s]: return None

    macro_fvg, fvg_min, fvg_max = get_institutional_fvg(df_d)
    if not macro_fvg: return None

    cp = float(df_60m['Close'].iloc[-1])
    daily_atr = float(df_d['ATR'].iloc[-2])
    buffer = daily_atr * 0.05

    y_high = float(df_d['High'].iloc[-3])
    y_low = float(df_d['Low'].iloc[-3])

    o, c, h, l = float(m60['Open']), float(m60['Close']), float(m60['High']), float(m60['Low'])
    body = abs(o - c) + 1e-9

    has_swept_low = (l <= y_low or l <= fvg_max + buffer)
    # Applied 1.2x shadow validation rule to the candle structure evaluation
    is_buy_reclaim = (macro_fvg == "BULLISH" and has_swept_low and c > o and (min(o,c) - l) > (body * 1.2))

    has_swept_high = (h >= y_high or h >= fvg_min - buffer)
    is_sell_reclaim = (macro_fvg == "BEARISH" and has_swept_high and c < o and (h - max(o,c)) > (body * 1.2))

    # --- HIGH PROBABILITY STRATIFICATION FILTER (WOODIES LEVEL ANALYSIS) ---
    y_high_pivot, y_low_pivot, y_close_pivot = float(df_d['High'].iloc[-2]), float(df_d['Low'].iloc[-2]), float(df_d['Close'].iloc[-2])
    w_pivot = (y_high_pivot + y_low_pivot + (2 * y_close_pivot)) / 4
    s2 = w_pivot - (y_high_pivot - y_low_pivot)
    r2 = w_pivot + (y_high_pivot - y_low_pivot)

    htf_cp = float(df_60m['Close'].iloc[-1])
    htf_ema = float(df_60m['EMA33'].iloc[-1])

    if is_buy_reclaim and htf_cp > htf_ema and s not in positions:
        side = "BUY"
        # Dynamic Rank Upgrade: Upgraded to Jackpot if trade executes near/below S2
        rank = "🔥 JACKPOT SWING" if cp <= (s2 + buffer) else "💎 ELITE SWING"
        if ONLY_TAKE_JACKPOTS and rank != "🔥 JACKPOT SWING": return None
        
        risk = max(daily_atr * 0.35, cp * 0.01) 
        targets = [round(cp + (risk * r), 2) for r in [1.5, 3, 5]]
        sl = round(cp - risk, 2)
        
    elif is_sell_reclaim and htf_cp < htf_ema and s not in positions:
        side = "SELL"
        # Dynamic Rank Upgrade: Upgraded to Jackpot if trade executes near/above R2
        rank = "🔥 JACKPOT SWING" if cp >= (r2 - buffer) else "💎 ELITE SWING"
        if ONLY_TAKE_JACKPOTS and rank != "🔥 JACKPOT SWING": return None
        
        risk = max(daily_atr * 0.35, cp * 0.01)
        targets = [round(cp - (risk * r), 2) for r in [1.5, 3, 5]]
        sl = round(cp + risk, 2)
    else:
        return None

    qty = int(DAILY_TRADE_BUDGET // cp)
    if qty == 0: return None

    msg = (f"📈 *{rank} ACTIVATED* - {s.replace('.NS','')}\n"
           f"----------------------------------------\n"
           f"📍 Anchor: DAILY {macro_fvg} Zone\n"
           f"🎯 Sweep: Confirmed Structural Raid\n"
           f"🚀 INITIALIZING POSITION {side} @ ₹{cp:.2f}\n"
           f"🏹 T1: ₹{targets[0]} | T2: ₹{targets[1]} | SL: ₹{sl:.2f}")
    send_telegram(msg)
    return {s: {"Entry": cp, "Targets": targets, "T_Idx": 0, "SL": sl, "Side": side, "Rank": rank, "Qty": qty, "Candle_Time": candle_id}}

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f: f.write("Timestamp,Symbol,Side,Rank,Entry,Exit,Points,Pct,Qty,PnL\n")
    if not os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'w') as f: json.dump({}, f)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f: json.dump({}, f)
        
    with open(POSITIONS_FILE, 'r') as f: pos = json.load(f)
    with open(HISTORY_FILE, 'r') as f: hist = json.load(f)
    
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retry))
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'})
    
    pos = manage_exits(pos, session)
    
    try:
        df_all_d = yf.download(SYMBOLS, period="100d", interval="1d", group_by='ticker', progress=False, session=session)
        df_all_60m = yf.download(SYMBOLS, period="15d", interval="60m", group_by='ticker', progress=False, session=session)
    except:
        df_all_d = df_all_60m = pd.DataFrame()

    if not df_all_d.empty and not df_all_60m.empty:
        for s in SYMBOLS:
            try:
                if s not in df_all_d.columns.levels[0] or s not in df_all_60m.columns.levels[0]: continue
                
                df_d = df_all_d[s].dropna(how='all').copy()
                df_60m = df_all_60m[s].dropna(how='all').copy()
                if df_d.empty or df_60m.empty: continue
                    
                hl = df_d['High'] - df_d['Low']
                hcp = abs(df_d['High'] - df_d['Close'].shift())
                lcp = abs(df_d['Low'] - df_d['Close'].shift())
                df_d['ATR'] = pd.concat([hl, hcp, lcp], axis=1).max(axis=1).rolling(14).mean()
                df_d['Vol_SMA'] = df_d['Volume'].rolling(10).mean()
                
                df_60m['EMA33'] = df_60m['Close'].ewm(span=33, adjust=False).mean()
                
                res = process_macro_strategy(s, df_d, df_60m, pos, hist)
                if res:
                    pos.update(res)
                    if s not in hist: hist[s] = []
                    hist[s].append(res[s]['Candle_Time'])
            except: pass
            
    with open(POSITIONS_FILE, 'w') as f: json.dump(pos, f, indent=4)
    with open(HISTORY_FILE, 'w') as f: json.dump(hist, f, indent=4)

    # --- AUTOMATED WEEKEND MAINTENANCE WINDOW ---
    now = datetime.now(IST)
    if now.weekday() == 4 and (now.hour > 15 or (now.hour == 15 and now.minute >= 30)):
        flag_file = f"summary_sent_{now.strftime('%Y_%U')}.txt"
        if not os.path.exists(flag_file):
            generate_weekly_summary()
            
            # Maintenance Trigger: Clears candle tracking memory for a fresh start next week
            with open(HISTORY_FILE, 'w') as f: 
                json.dump({}, f)
            print("🧹 Weekend Maintenance: Candle history registry reset successful.")
            
            with open(flag_file, 'w') as f: f.write("transmitted")
