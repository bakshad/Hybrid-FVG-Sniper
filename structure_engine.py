import pandas as pd
import numpy as np


class StructureEngine:

    # -----------------------------------
    # Liquidity Sweep Detection
    # -----------------------------------

    def detect_bullish_sweep(self, df_60m):

        if len(df_60m) < 10:
            return None

        trigger = df_60m.iloc[-2]

        previous_lows = df_60m['Low'].iloc[-8:-2]

        sweep_low = previous_lows.min()

        swept = float(trigger['Low']) < float(sweep_low)

        reclaimed = float(trigger['Close']) > float(sweep_low)

        if swept and reclaimed:

            depth = (
                abs(float(trigger['Low']) - float(sweep_low))
                / float(sweep_low)
            ) * 100

            return {
                "valid": True,
                "depth_pct": round(depth, 2)
            }

        return None

    def detect_bearish_sweep(self, df_60m):

        if len(df_60m) < 10:
            return None

        trigger = df_60m.iloc[-2]

        previous_highs = df_60m['High'].iloc[-8:-2]

        sweep_high = previous_highs.max()

        swept = float(trigger['High']) > float(sweep_high)

        reclaimed = float(trigger['Close']) < float(sweep_high)

        if swept and reclaimed:

            depth = (
                abs(float(trigger['High']) - float(sweep_high))
                / float(sweep_high)
            ) * 100

            return {
                "valid": True,
                "depth_pct": round(depth, 2)
            }

        return None

    # -----------------------------------
    # Market Structure Shift
    # -----------------------------------

    def bullish_mss(self, df_60m):

        if len(df_60m) < 8:
            return False

        recent_high = float(df_60m['High'].iloc[-2])

        prior_high = float(
            df_60m['High'].iloc[-8:-2].max()
        )

        return recent_high > prior_high

    def bearish_mss(self, df_60m):

        if len(df_60m) < 8:
            return False

        recent_low = float(df_60m['Low'].iloc[-2])

        prior_low = float(
            df_60m['Low'].iloc[-8:-2].min()
        )

        return recent_low < prior_low

    # -----------------------------------
    # 15m Trigger
    # -----------------------------------

    def bullish_trigger(self, df_15m):

        if len(df_15m) < 3:
            return False

        prev = df_15m.iloc[-3]
        curr = df_15m.iloc[-2]

        engulfing = (
            curr['Close'] > curr['Open']
            and curr['Open'] < prev['Close']
            and curr['Close'] > prev['Open']
        )

        body = abs(
            float(curr['Close'])
            - float(curr['Open'])
        )

        rng = max(
            float(curr['High'])
            - float(curr['Low']),
            0.0001
        )

        body_ratio = body / rng

        strong_body = body_ratio >= 0.60

        return engulfing or strong_body

    def bearish_trigger(self, df_15m):

        if len(df_15m) < 3:
            return False

        prev = df_15m.iloc[-3]
        curr = df_15m.iloc[-2]

        engulfing = (
            curr['Close'] < curr['Open']
            and curr['Open'] > prev['Close']
            and curr['Close'] < prev['Open']
        )

        body = abs(
            float(curr['Close'])
            - float(curr['Open'])
        )

        rng = max(
            float(curr['High'])
            - float(curr['Low']),
            0.0001
        )

        body_ratio = body / rng

        strong_body = body_ratio >= 0.60

        return engulfing or strong_body

    # -----------------------------------
    # Score Engine
    # -----------------------------------

    def calculate_structure_score(
        self,
        side,
        sweep_depth,
        mss,
        trigger
    ):

        score = 0

        # Sweep Score (20)

        if sweep_depth >= 1.0:
            score += 20

        elif sweep_depth >= 0.50:
            score += 15

        elif sweep_depth >= 0.25:
            score += 10

        # MSS Score (10)

        if mss:
            score += 10

        # Trigger Score (10)

        if trigger:
            score += 10

        return score

    # -----------------------------------
    # Main Evaluation
    # -----------------------------------

    def evaluate(
        self,
        side,
        df_60m,
        df_15m
    ):

        if side == "BUY":

            sweep = self.detect_bullish_sweep(df_60m)

            if not sweep:
                return None

            mss = self.bullish_mss(df_60m)

            trigger = self.bullish_trigger(df_15m)

            score = self.calculate_structure_score(
                side,
                sweep["depth_pct"],
                mss,
                trigger
            )

            return {
                "side": "BUY",
                "score": score,
                "sweep": True,
                "mss": mss,
                "trigger": trigger,
                "sweep_depth": sweep["depth_pct"]
            }

        if side == "SELL":

            sweep = self.detect_bearish_sweep(df_60m)

            if not sweep:
                return None

            mss = self.bearish_mss(df_60m)

            trigger = self.bearish_trigger(df_15m)

            score = self.calculate_structure_score(
                side,
                sweep["depth_pct"],
                mss,
                trigger
            )

            return {
                "side": "SELL",
                "score": score,
                "sweep": True,
                "mss": mss,
                "trigger": trigger,
                "sweep_depth": sweep["depth_pct"]
            }

        return None
