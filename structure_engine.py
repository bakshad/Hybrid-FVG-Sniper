"""
structure_engine.py

Liquidity Sweep
Market Structure Shift
15m Trigger

Score Range:
    0 - 40
"""

import pandas as pd


class StructureEngine:

    # =========================
    # Bullish Sweep
    # =========================

    def detect_bullish_sweep(
        self,
        df_60m
    ):
    
        if len(df_60m) < 25:
            return None
    
        trigger = df_60m.iloc[-2]
    
        confirm = df_60m.iloc[-1]
    
        previous_lows = (
            df_60m["Low"]
            .iloc[-20:-2]
        )
    
        sweep_level = (
            previous_lows.min()
        )
    
        swept = (
            trigger["Low"]
            < sweep_level
        )
    
        reclaimed = (
            confirm["Close"]
            > sweep_level
        )
    
        print(
            f"[{df_60m.index[-1]}] "
            f"BULL SWEEP | "
            f"Swept={swept} "
            f"Reclaimed={reclaimed}"
        )
    
        if not (swept and reclaimed):
            return None
    
        depth_pct = round(
            (
                abs(
                    trigger["Low"]
                    - sweep_level
                )
                /
                sweep_level
            )
            * 100,
            2
        )
    
        return {
            "valid": True,
            "sweep_level": float(
                sweep_level
            ),
            "depth_pct": depth_pct
        }

    # =========================
    # Bearish Sweep
    # =========================
    
    def detect_bearish_sweep(
        self,
        df_60m
    ):
    
        if len(df_60m) < 25:
            return None
    
        trigger = df_60m.iloc[-2]
    
        confirm = df_60m.iloc[-1]
    
        previous_highs = (
            df_60m["High"]
            .iloc[-20:-2]
        )
    
        sweep_level = (
            previous_highs.max()
        )
    
        swept = (
            trigger["High"]
            > sweep_level
        )
    
        reclaimed = (
            confirm["Close"]
            < sweep_level
        )
    
        print(
            f"[{df_60m.index[-1]}] "
            f"BULL SWEEP | "
            f"Swept={swept} "
            f"Reclaimed={reclaimed}"
        )
    
        if not (swept and reclaimed):
            return None
    
        depth_pct = round(
            (
                abs(
                    trigger["High"]
                    - sweep_level
                )
                /
                sweep_level
            )
            * 100,
            2
        )
    
        return {
            "valid": True,
            "sweep_level": float(
                sweep_level
            ),
            "depth_pct": depth_pct
        }
    # =========================
    # Bullish MSS
    # =========================

    def bullish_mss(
        self,
        df_60m
    ):

        recent_close = (
            df_60m["Close"]
            .iloc[-2]
        )

        previous_high = (
            df_60m["High"]
            .iloc[-5:-2]
            .max()
        )

        return recent_close > previous_high

    # =========================
    # Bearish MSS
    # =========================

    def bearish_mss(
        self,
        df_60m
    ):

        recent_close = (
            df_60m["Close"]
            .iloc[-2]
        )

        previous_low = (
            df_60m["Low"]
            .iloc[-5:-2]
            .min()
        )

        return recent_close < previous_low

    # =========================
    # Bullish Trigger
    # =========================

    def bullish_trigger(
        self,
        df_15m
    ):

        if len(df_15m) < 3:
            return False

        prev = df_15m.iloc[-3]

        curr = df_15m.iloc[-2]

        engulfing = (

            curr["Close"] >
            curr["Open"]

            and

            curr["Open"] <
            prev["Close"]

            and

            curr["Close"] >
            prev["Open"]
        )

        body = abs(
            curr["Close"]
            - curr["Open"]
        )

        rng = max(
            curr["High"]
            - curr["Low"],
            0.01
        )

        body_ratio = (
            body / rng
        )

        return (
            engulfing
            or
            body_ratio >= 0.60
        )

    # =========================
    # Bearish Trigger
    # =========================

    def bearish_trigger(
        self,
        df_15m
    ):

        if len(df_15m) < 3:
            return False

        prev = df_15m.iloc[-3]

        curr = df_15m.iloc[-2]

        engulfing = (

            curr["Close"] <
            curr["Open"]

            and

            curr["Open"] >
            prev["Close"]

            and

            curr["Close"] <
            prev["Open"]
        )

        body = abs(
            curr["Close"]
            - curr["Open"]
        )

        rng = max(
            curr["High"]
            - curr["Low"],
            0.01
        )

        body_ratio = (
            body / rng
        )

        return (
            engulfing
            or
            body_ratio >= 0.60
        )

    # =========================
    # Score
    # =========================

    def calculate_score(
        self,
        sweep_depth,
        mss,
        trigger
    ):
        """
        Max = 40
        """

        score = 0

        # Sweep
        if sweep_depth >= 1.0:
            score += 20

        elif sweep_depth >= 0.5:
            score += 15

        else:
            score += 10

        # MSS

        if mss:
            score += 10

        # Trigger

        if trigger:
            score += 10

        return score

    # =========================
    # Main Evaluation
    # =========================

    def evaluate(
        self,
        side,
        df_60m,
        df_15m
    ):

        if side == "BUY":

            sweep = (
                self.detect_bullish_sweep(
                    df_60m
                )
            )

            if not sweep:
                return None

            mss = (
                self.bullish_mss(
                    df_60m
                )
            )

            trigger = (
                self.bullish_trigger(
                    df_15m
                )
            )

        else:

            sweep = (
                self.detect_bearish_sweep(
                    df_60m
                )
            )

            if not sweep:
                return None

            mss = (
                self.bearish_mss(
                    df_60m
                )
            )

            trigger = (
                self.bearish_trigger(
                    df_15m
                )
            )

        print(
            f"MSS={mss} "
            f"Trigger={trigger}"
        )
            
        if not mss:
            return None

        if not trigger:
            return None

        score = self.calculate_score(
            sweep["depth_pct"],
            mss,
            trigger
        )

        return {

            "score":
                score,

            "sweep":
                True,

            "mss":
                mss,

            "trigger":
                trigger,

            "sweep_level":
                sweep["sweep_level"],

            "sweep_depth":
                sweep["depth_pct"]
        }
