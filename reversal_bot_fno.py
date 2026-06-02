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
DAILY_TRADE_BUDGET = 50000  # Virtual capital allocation per signal slot

# COMPLETE PRODUCTION F&O UNIVERSE
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

def generate_weekly_summary():
    """Parses historical log file to aggregate virtual cash profit figures."""
    if not os.path.exists(LOG_FILE): return
    try:
        df = pd.read_csv(LOG_FILE)
        if df.empty: return
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        one_week_ago = datetime.now(IST) - pd.Timedelta(days=7)
        weekly_df = df[df['Timestamp'] >= pd.to_datetime(one_week_ago).tz_localize(IST)].copy()
        
        if weekly_df.empty:
            send_telegram("📊 *Weekly Engine Summary*\nNo algorithmic positions closed during this weekly series context.")
            return
            
        total_signals = len(weekly_df)
        wins = len(weekly_df[weekly_df['Points'] > 0])
        win_rate = round((wins / total_signals) * 100, 2)
        net_pct = round(weekly_df['Pct'].sum(), 2)
        
        # Coerce values to float to prevent mathematical string errors
        weekly_df['PnL'] = pd.to_numeric(weekly_df['PnL'], errors='coerce').fillna(0)
        total_pnl_cash = round(weekly_df['PnL'].sum(), 2)
        
        msg = (f"📊 *WEEKLY PAPER TRADING SUMMARY*\n"
               f"-----------------------------------\n"
               f"🏹 *Closed Positions:* {total_signals}\n"
               f"🎯 *Win Rate:* {win_rate}%\n"
               f"📈 *Net Return:* {net_pct:+.2f}%\n"
               f"💰 *Total Paper PnL:* ₹{total_pnl_cash:+,2f}\n\n"
               f"*Asset Performance Breakdown:*")
        
        for _, row in weekly_df.iterrows():
            ticker = row['Symbol'].replace('.NS','')
            sign = "+" if row['Points'] >= 0 else ""
            msg += (f"\n• *{ticker}* ({row['Side']}) | Qty: {int(row['Qty'])} "
                    f"\n  In: {row['Entry']:.2f} → Out: {row['Exit']:.2f}"
                    f"\n  Return: {sign}{row['Pct']:.2f}% (*₹{row['PnL']:+,2f}*)")
            
        send_telegram(msg)
    except Exception as e:
        print(f"Summary generation error: {e}")

def process_symbol(s, positions):
    df_d = fetch_data(s, "5d", "1d")
    df_htf = fetch_data(s, "10d", "60m")
    df_15 = fetch_data(s, "3d", "15m")
    
    if df_d is None or df_htf is None or df_15 is None or len(df_d) < 2: return None

    # STRICT NO-GAP OPEN FILTER
    prev_close = float(df_d['Close'].iloc[-2])
    today_open = float(df_d['Open'].iloc[-1])
    if abs(today_open - prev_close) / prev_close > 0.0005: return None

    # Woodies Structural Levels
    y_high, y_low, y_close = float(df_d['High'].iloc[-2]), float(df_d['Low'].iloc[-2]), float(df_d['Close'].iloc[-2])
    w_pivot = (y_high + y_low + (2 * y_close)) / 4
    s2 = w_pivot - (y_high - y_low)
    r2 = w_pivot + (y_high - y_low)

    htf_fvg_type, htf_min, htf_max = get_fvg(df_htf)
    m15 = df_15.iloc[-1]
    cp, atr = float(m15['Close']), float(m15['ATR'])
    buffer = atr * 0.1
    
    # DOJI/CONTRACTION FILTER 
    o, c, h, l = float(m15['Open']), float(m15['Close']), float(m15['High']), float(m15['Low'])
    total_range = (h - l) + 1e-9
    body = abs(o - c) + 1e-9
    if (body / total_range) < 0.10: return None

    # 1.5x REJECTION SHADOW RULE
    has_bottom_wick = (min(o, c) - l) > (body * 1.5)
    has_top_wick = (h - max(o, c)) > (body * 1.5)

    is_buy = (htf_fvg_type == "BULLISH" and (m15['Low'] <= htf_max + buffer) and (cp > o) and has_bottom_wick)
    is_sell = (htf_fvg_type == "BEARISH" and (m15['High'] >= htf_min - buffer) and (cp < o) and has_top_wick)

    if (is_buy or is_sell) and s not in positions:
        side = "BUY" if is_buy else "SELL"
        rank = "🔥 JACKPOT" if (side == "BUY" and cp < s2) or (side == "SELL" and cp > r2) else "💎 ELITE"
        
        # VIRTUAL PAPER POSITION SIZING CAP ENGINE
        qty = int(DAILY_TRADE_BUDGET // cp)
        if qty == 0: return None  # Prevents executing ultra-expensive equities beyond buffer limits
        
        risk = max(atr, cp * 0.003) 
        targets = [round(cp + (risk * r) if side == "BUY" else cp - (risk * r), 2) for r in [1.5, 3, 5]]
        sl = round(cp - risk if side == "BUY" else cp + risk, 2)

        msg = (f"{rank}: {s.replace('.NS','')}\n"
               f"---------------------------\n"
               f"📍 HTF: 60m {htf_fvg_type} FVG\n"
               f"🚀 PAPER {side} @ ₹{cp:.2f}\n"
               f"📦 Qty: {qty} shares (Allocated: ₹{qty*cp:,.2f})\n"
               f"🎯 T1: ₹{targets[0]} | SL: ₹{sl:.2f}")
        send_telegram(msg)
        return {s: {"Entry": cp, "Targets": targets, "T_Idx": 0, "SL": sl, "Side": side, "Rank": rank, "Qty": qty}}
    return None

def manage_exits(positions):
    updated = positions.copy()
    for s, d in positions.items():
        df = fetch_data(s, "1d", "1m")
        if df is None or df.empty: continue
        cp = float(df['Close'].iloc[-1])
        side, entry, targets, idx = d['Side'], d['Entry'], d['Targets'], d['T_Idx']
        qty = d.get('Qty', int(DAILY_TRADE_BUDGET // entry))
        
        pts = round(cp - entry if side == "BUY" else entry - cp, 2)
        pct = round((pts / entry) * 100, 2)
        pnl_cash = round(pts * qty, 2)

        if (side == "BUY" and cp >= targets[idx]) or (side == "SELL" and cp <= targets[idx]):
            if idx < 2:
                d['T_Idx'] += 1
                d['SL'] = entry 
                send_telegram(f"🎯 T{idx+1} HIT: {s.replace('.NS','')}\nCaptured: {pts} pts ({pct}%)\n💰 Running PnL: ₹{pnl_cash:+,2f}\n🛡️ SL trailing to cost.")
                updated[s] = d
            else:
                send_telegram(f"🏁 FINAL TARGET COMPLETED: {s.replace('.NS','')}\nTotal: {pts} pts ({pct}%)\n💸 Paper Profit: ₹{pnl_cash:+,2f}")
                with open(LOG_FILE, 'a') as f: f.write(f"{datetime.now(IST)},{s},{side},{d['Rank']},{entry},{cp},{pts},{pct},{qty},{pnl_cash}\n")
                del updated[s]
        elif (side == "BUY" and cp <= d['SL']) or (side == "SELL" and cp >= d['SL']):
            send_telegram(f"🛑 SL EXIT TRIGGERED: {s.replace('.NS','')}\nPnL: {pts:+.2f} pts ({pct}%)\n💸 Paper Loss: ₹{pnl_cash:+,.2f}")
            with open(LOG_FILE, 'a') as f: f.write(f"{datetime.now(IST)},{s},{side},{d['Rank']},{entry},{cp},{pts},{pct},{qty},{pnl_cash}\n")
            del updated[s]
    return updated

if __name__ == "__main__":
    # Synchronize performance CSV structure mapping
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f: 
            f.write("Timestamp,Symbol,Side,Rank,Entry,Exit,Points,Pct,Qty,PnL\n")
            
    if not os.path.exists(POSITIONS_FILE): 
        with open(POSITIONS_FILE, 'w') as f: json.dump({}, f)
        
    with open(POSITIONS_FILE, 'r') as f: pos = json.load(f)
    
    pos = manage_exits(pos)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda s: process_symbol(s, pos), SYMBOLS))
        for r in results:
            if r: pos.update(r)
            
    with open(POSITIONS_FILE, 'w') as f: json.dump(pos, f, indent=4)

    # FRIDAY POST-MARKET SNAP SUMMARY TRIGGER
    now = datetime.now(IST)
    if now.weekday() == 4 and (now.hour > 15 or (now.hour == 15 and now.minute >= 30)):
        flag_file = f"summary_sent_{now.strftime('%Y_%U')}.txt"
        if not os.path.exists(flag_file):
            generate_weekly_summary()
            with open(flag_file, 'w') as f: f.write("transmitted")
