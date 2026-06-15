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

        buffer = atr * 0.10

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
