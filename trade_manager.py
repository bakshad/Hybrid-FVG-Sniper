"""
trade_manager.py

Production Trade Management Engine

Handles:

- Position Creation
- Risk Sizing
- T1/T2 Allocation
- Chandelier Stops
- Trade Lifecycle

Part A
"""

import math
from datetime import datetime

from config import (
    STARTING_CAPITAL,
    RISK_PER_TRADE_PCT,
    T1_R,
    T2_R,
    T1_EXIT_PCT,
    T2_EXIT_PCT,
    CHANDELIER_PERIOD,
    CHANDELIER_MULTIPLIER
)


class TradeManager:

    def __init__(self):
        pass

    # ==================================================
    # Chandelier Long
    # ==================================================

    @staticmethod
    def calculate_chandelier_long(df_daily):

        atr = float(df_daily["ATR"].iloc[-1])

        highest_high = (
            df_daily["High"]
            .tail(CHANDELIER_PERIOD)
            .max()
        )

        stop = (
            highest_high
            -
            (atr * CHANDELIER_MULTIPLIER)
        )

        return round(stop, 2)

    # ==================================================
    # Chandelier Short
    # ==================================================

    @staticmethod
    def calculate_chandelier_short(df_daily):

        atr = float(df_daily["ATR"].iloc[-1])

        lowest_low = (
            df_daily["Low"]
            .tail(CHANDELIER_PERIOD)
            .min()
        )

        stop = (
            lowest_low
            +
            (atr * CHANDELIER_MULTIPLIER)
        )

        return round(stop, 2)

    # ==================================================
    # Risk Amount
    # ==================================================

    @staticmethod
    def calculate_risk_amount(capital):

        return (
            capital
            * RISK_PER_TRADE_PCT
            / 100
        )

    # ==================================================
    # Position Size
    # ==================================================

    @staticmethod
    def calculate_position_size(
        capital,
        risk_per_share
    ):

        if risk_per_share <= 0:
            return 0

        risk_amount = (
            capital
            * RISK_PER_TRADE_PCT
            / 100
        )

        qty = math.floor(
            risk_amount
            /
            risk_per_share
        )

        return max(qty, 0)

    # ==================================================
    # Quantity Split
    # ==================================================

    @staticmethod
    def calculate_exit_quantities(
        qty
    ):

        t1_qty = max(
            1,
            math.floor(
                qty * T1_EXIT_PCT
            )
        )

        t2_qty = max(
            1,
            math.floor(
                qty * T2_EXIT_PCT
            )
        )

        runner_qty = (
            qty
            - t1_qty
            - t2_qty
        )

        if runner_qty < 1:

            runner_qty = 1

            if t2_qty > 1:
                t2_qty -= 1

        return (
            t1_qty,
            t2_qty,
            runner_qty
        )

    # ==================================================
    # Create Position
    # ==================================================

    def create_position(
        self,
        symbol,
        side,
        entry,
        sweep_level,
        atr,
        score,
        grade,
        capital
    ):

        buffer = max(
            atr * 0.50,
            entry * 0.005
        )

        # ------------------
        # Structure Stop
        # ------------------

        if side == "BUY":

            sl = (
                sweep_level
                - buffer
            )

        else:

            sl = (
                sweep_level
                + buffer
            )

        risk_per_share = abs(
            entry - sl
        )

        # ------------------
        # Validation
        # ------------------

        if risk_per_share <= 0:

            return None

        if risk_per_share > (atr * 2):

            return None

        qty = self.calculate_position_size(
            capital,
            risk_per_share
        )

        if qty < 1:

            return None

        # ------------------
        # Targets
        # ------------------

        if side == "BUY":

            t1 = round(
                entry
                +
                (risk_per_share * T1_R),
                2
            )

            t2 = round(
                entry
                +
                (risk_per_share * T2_R),
                2
            )

        else:

            t1 = round(
                entry
                -
                (risk_per_share * T1_R),
                2
            )

            t2 = round(
                entry
                -
                (risk_per_share * T2_R),
                2
            )

        # ------------------
        # Quantity Split
        # ------------------

        (
            t1_qty,
            t2_qty,
            runner_qty
        ) = self.calculate_exit_quantities(
            qty
        )

        now = str(
            datetime.now()
        )

        # ------------------
        # Position Object
        # ------------------

        position = {

            "Symbol":
                symbol,

            "Side":
                side,

            "Entry":
                round(entry, 2),

            "SL":
                round(sl, 2),

            "SweepLevel":
                round(
                    sweep_level,
                    2
                ),

            "InitialRisk":
                round(
                    risk_per_share,
                    2
                ),

            "Qty":
                qty,

            "RemainingQty":
                qty,

            "T1Qty":
                t1_qty,

            "T2Qty":
                t2_qty,

            "RunnerQty":
                runner_qty,

            "RealizedPnL":
                0.0,

            "EntryCapital":
                round(
                    capital,
                    2
                ),

            "Score":
                score,

            "Grade":
                grade,

            "T1":
                t1,

            "T2":
                t2,

            "T1Hit":
                False,

            "T2Hit":
                False,

            "RunnerActive":
                True,

            "HighestPrice":
                entry,

            "LowestPrice":
                entry,

            "ChandelierStop":
                round(sl, 2),

            "EntryTime":
                now,

            "LastUpdateTime":
                now,

            "Status":
                "OPEN"
        }

        return position

    # ==================================================
    # PnL
    # ==================================================

    @staticmethod
    def calculate_pnl(
        side,
        entry,
        exit_price,
        qty
    ):

        if side == "BUY":

            pnl = (
                exit_price
                - entry
            ) * qty

        else:

            pnl = (
                entry
                - exit_price
            ) * qty

        return round(pnl, 2)
    # ==================================================
    # T1 Processing
    # ==================================================

    def process_t1(
        self,
        position,
        current_price
    ):

        if position["T1Hit"]:
            return None

        if position["Side"] == "BUY":

            hit = (
                current_price
                >=
                position["T1"]
            )

        else:

            hit = (
                current_price
                <=
                position["T1"]
            )

        if not hit:
            return None

        qty = int(
            position["T1Qty"]
        )

        pnl = self.calculate_pnl(
            position["Side"],
            float(position["Entry"]),
            current_price,
            qty
        )

        position["RemainingQty"] -= qty

        position["RealizedPnL"] += pnl

        position["T1Hit"] = True

        # Move stop to breakeven

        position["SL"] = position["Entry"]

        position["LastUpdateTime"] = str(
            datetime.now()
        )

        return "T1_HIT"

    # ==================================================
    # T2 Processing
    # ==================================================

    def process_t2(
        self,
        position,
        current_price
    ):

        if position["T2Hit"]:
            return None

        if not position["T1Hit"]:
            return None

        if position["Side"] == "BUY":

            hit = (
                current_price
                >=
                position["T2"]
            )

        else:

            hit = (
                current_price
                <=
                position["T2"]
            )

        if not hit:
            return None

        qty = int(
            position["T2Qty"]
        )

        pnl = self.calculate_pnl(
            position["Side"],
            float(position["Entry"]),
            current_price,
            qty
        )

        position["RemainingQty"] -= qty

        position["RealizedPnL"] += pnl

        position["T2Hit"] = True

        # Move stop to T1

        position["SL"] = position["T1"]

        position["LastUpdateTime"] = str(
            datetime.now()
        )

        return "T2_HIT"

    # ==================================================
    # Update High / Low
    # ==================================================

    def update_price_tracking(
        self,
        position,
        current_price
    ):

        position["HighestPrice"] = max(
            float(position["HighestPrice"]),
            current_price
        )

        position["LowestPrice"] = min(
            float(position["LowestPrice"]),
            current_price
        )

    # ==================================================
    # Update Chandelier
    # ==================================================

    def update_chandelier(
        self,
        position,
        df_daily
    ):

        if position["Side"] == "BUY":

            new_stop = (
                self.calculate_chandelier_long(
                    df_daily
                )
            )

            position["ChandelierStop"] = max(
                float(
                    position["ChandelierStop"]
                ),
                new_stop
            )

        else:

            new_stop = (
                self.calculate_chandelier_short(
                    df_daily
                )
            )

            position["ChandelierStop"] = min(
                float(
                    position["ChandelierStop"]
                ),
                new_stop
            )

        position["LastUpdateTime"] = str(
            datetime.now()
        )

    # ==================================================
    # Exit Detection
    # ==================================================

    def check_exit(
        self,
        position,
        current_price
    ):

        side = position["Side"]

        sl = float(
            position["SL"]
        )

        chandelier = float(
            position["ChandelierStop"]
        )

        # ------------------
        # BUY
        # ------------------

        if side == "BUY":

            if current_price <= sl:

                return "STOP_EXIT"

            if (
                position["T2Hit"]
                and
                current_price <= chandelier
            ):

                return "RUNNER_EXIT"

        # ------------------
        # SELL
        # ------------------

        else:

            if current_price >= sl:

                return "STOP_EXIT"

            if (
                position["T2Hit"]
                and
                current_price >= chandelier
            ):

                return "RUNNER_EXIT"

        return None

    # ==================================================
    # R Multiple
    # ==================================================

    @staticmethod
    def calculate_r_multiple(
        pnl,
        position
    ):

        risk = (
            float(
                position["InitialRisk"]
            )
            *
            int(
                position["Qty"]
            )
        )

        if risk <= 0:
            return 0

        return round(
            pnl / risk,
            2
        )

    # ==================================================
    # Days Held
    # ==================================================

    @staticmethod
    def calculate_days_held(
        position
    ):

        try:

            entry_time = datetime.fromisoformat(
                str(
                    position["EntryTime"]
                )
            )

            days = (
                datetime.now()
                -
                entry_time
            ).days

            return max(days, 0)

        except:

            return 0

    # ==================================================
    # Close Position
    # ==================================================

    def close_position(
        self,
        position,
        current_price,
        reason
    ):

        remaining_qty = int(
            position["RemainingQty"]
        )

        remaining_pnl = self.calculate_pnl(
            position["Side"],
            float(position["Entry"]),
            current_price,
            remaining_qty
        )

        total_pnl = round(
            float(
                position["RealizedPnL"]
            )
            +
            remaining_pnl,
            2
        )

        r_multiple = (
            self.calculate_r_multiple(
                total_pnl,
                position
            )
        )

        days_held = (
            self.calculate_days_held(
                position
            )
        )

        pnl_pct = round(
            (
                total_pnl
                /
                float(
                    position["EntryCapital"]
                )
            )
            * 100,
            2
        )

        trade_record = {

            "EntryTime":
                position["EntryTime"],

            "ExitTime":
                str(
                    datetime.now()
                ),

            "Symbol":
                position["Symbol"],

            "Side":
                position["Side"],

            "Score":
                position["Score"],

            "Grade":
                position["Grade"],

            "Entry":
                position["Entry"],

            "Exit":
                round(
                    current_price,
                    2
                ),

            "Qty":
                position["Qty"],

            "PnL":
                total_pnl,

            "PnLPct":
                pnl_pct,

            "RMultiple":
                r_multiple,

            "DaysHeld":
                days_held,

            "ExitReason":
                reason
        }

        return trade_record
