"""
FVG Runner Bot
Global Configuration
"""

# =========================
# Portfolio Settings
# =========================

DYNAMIC_EQUITY = True

STARTING_CAPITAL = 50000

RISK_PER_TRADE_PCT = 1.0

MAX_ACTIVE_TRADES = 10

MAX_NEW_TRADES_PER_DAY = 3

MAX_LONGS = 6

MAX_SHORTS = 6

MAX_HOLD_DAYS = 60

# =========================
# Trade Qualification
# =========================

MIN_SCORE = 85

BUY_ENABLED = True

SELL_ENABLED = True

# =========================
# Target Management
# =========================

T1_R = 2.0

T2_R = 4.0

T1_EXIT_PCT = 0.40

T2_EXIT_PCT = 0.30

RUNNER_EXIT_PCT = 0.30

# =========================
# FVG Filters
# =========================

MIN_FVG_ATR = 0.20

MIN_VOLUME_RATIO = 1.5

MIN_DISPLACEMENT = 0.55

# =========================
# Indicators
# =========================

ATR_PERIOD = 14

EMA_FAST = 21

EMA_MEDIUM = 50

EMA_SLOW = 200

# =========================
# Chandelier Exit
# =========================

CHANDELIER_PERIOD = 22

CHANDELIER_MULTIPLIER = 3.0

# =========================
# Universe Filters
# =========================

MIN_PRICE = 100

MIN_ATR_PERCENT = 2.0

# =========================
# Data
# =========================

DAILY_LOOKBACK = 180

HOUR_LOOKBACK = 90

M15_LOOKBACK = 45

# =========================
# Telegram
# =========================

import os

TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    ""
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    ""
)

# =========================
# Files
# =========================

ACTIVE_POSITIONS_FILE = "active_positions.csv"

TRADE_HISTORY_FILE = "trade_history.csv"

SIGNAL_DATASET_FILE = "signal_dataset.csv"

FNO_LIST_FILE = "fno_list.csv"
