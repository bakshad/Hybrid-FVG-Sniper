"""
fvg_engine.py

Institutional Fair Value Gap Engine

Score Range:
    0 - 60
"""

import pandas as pd
import numpy as np

from config import (
    ATR_PERIOD,
    MIN_FVG_ATR,
    MIN_VOLUME_RATIO,
    MIN_DISPLACEMENT
)


class FVGEngine:

    # =========================
    # ATR
    # =========================

    def calculate_atr(
        self,
        df,
        period=ATR_PERIOD
    ):

        high_low = df["High"] - df["Low"]

        high_close = abs(
            df["High"] -
            df["Close"].shift()
        )

        low_close = abs(
            df["Low"] -
            df["Close"].shift()
        )

        tr = pd.concat(
            [
                high_low,
                high_close,
                low_close
            ],
            axis=1
        ).max(axis=1)

        return tr.rolling(period).mean()

    # =========================
    # Volume Ratio
    # =========================

    def calculate_volume_ratio(
        self,
        df
    ):

        volume_ma = (
            df["Volume"]
            .rolling(20)
            .mean()
        )

        return (
            df["Volume"] /
            volume_ma
        )

    # =========================
    # FVG Scoring
    # =========================

    def score_fvg(
        self,
        gap_atr,
        volume_ratio,
        body_ratio
    ):
        """
        Maximum:
            60
        """

        score = 0

        score += min(
            gap_atr * 20,
            20
        )

        score += min(
            volume_ratio * 10,
            20
        )

        score += min(
            body_ratio * 20,
            20
        )

        return round(score, 2)

    # =========================
    # Active FVG Check
    # =========================

    def is_active_fvg(
        self,
        current_price,
        atr,
        fvg_low,
        fvg_high
    ):

        # Inside FVG

        if (
            fvg_low <= current_price <= fvg_high
        ):
            return True

        # Near FVG

        distance = min(
            abs(current_price - fvg_low),
            abs(current_price - fvg_high)
        )

        return distance <= (atr * 2)

    # =========================
    # Scan FVGs
    # =========================

    def scan_fvgs(
        self,
        df
    ):

        if len(df) < 30:
            return []

        df = df.copy()

        df["ATR"] = (
            self.calculate_atr(df)
        )

        df["VolumeRatio"] = (
            self.calculate_volume_ratio(df)
        )

        current_price = (
            float(
                df["Close"].iloc[-1]
            )
        )

        results = []

        start = max(
            2,
            len(df) - 20
        )

        for i in range(
            start,
            len(df)
        ):

            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1]
            c3 = df.iloc[i]

            atr = float(c2["ATR"])

            if np.isnan(atr):
                continue

            candle_range = max(
                (
                    c2["High"] -
                    c2["Low"]
                ),
                0.01
            )

            body_size = abs(
                c2["Close"] -
                c2["Open"]
            )

            body_ratio = (
                body_size /
                candle_range
            )

            volume_ratio = float(
                c2["VolumeRatio"]
            )

            # ---------------------
            # Bullish FVG
            # ---------------------

            if c1["High"] < c3["Low"]:

                gap_size = (
                    c3["Low"] -
                    c1["High"]
                )

                gap_atr = (
                    gap_size /
                    atr
                )

                if (
                    gap_atr >= MIN_FVG_ATR
                    and
                    volume_ratio >= MIN_VOLUME_RATIO
                    and
                    body_ratio >= MIN_DISPLACEMENT
                ):

                    fvg_low = float(
                        c1["High"]
                    )

                    fvg_high = float(
                        c3["Low"]
                    )

                    if not self.is_active_fvg(
                        current_price,
                        atr,
                        fvg_low,
                        fvg_high
                    ):
                        continue

                    score = (
                        self.score_fvg(
                            gap_atr,
                            volume_ratio,
                            body_ratio
                        )
                    )

                    results.append({

                        "type":
                            "BULLISH",

                        "score":
                            score,

                        "gap_atr":
                            round(
                                gap_atr,
                                2
                            ),

                        "volume_ratio":
                            round(
                                volume_ratio,
                                2
                            ),

                        "body_ratio":
                            round(
                                body_ratio,
                                2
                            ),

                        "fvg_low":
                            round(
                                fvg_low,
                                2
                            ),

                        "fvg_high":
                            round(
                                fvg_high,
                                2
                            )
                    })

            # ---------------------
            # Bearish FVG
            # ---------------------

            if c1["Low"] > c3["High"]:

                gap_size = (
                    c1["Low"] -
                    c3["High"]
                )

                gap_atr = (
                    gap_size /
                    atr
                )

                if (
                    gap_atr >= MIN_FVG_ATR
                    and
                    volume_ratio >= MIN_VOLUME_RATIO
                    and
                    body_ratio >= MIN_DISPLACEMENT
                ):

                    fvg_low = float(
                        c3["High"]
                    )

                    fvg_high = float(
                        c1["Low"]
                    )

                    if not self.is_active_fvg(
                        current_price,
                        atr,
                        fvg_low,
                        fvg_high
                    ):
                        continue

                    score = (
                        self.score_fvg(
                            gap_atr,
                            volume_ratio,
                            body_ratio
                        )
                    )

                    results.append({

                        "type":
                            "BEARISH",

                        "score":
                            score,

                        "gap_atr":
                            round(
                                gap_atr,
                                2
                            ),

                        "volume_ratio":
                            round(
                                volume_ratio,
                                2
                            ),

                        "body_ratio":
                            round(
                                body_ratio,
                                2
                            ),

                        "fvg_low":
                            round(
                                fvg_low,
                                2
                            ),

                        "fvg_high":
                            round(
                                fvg_high,
                                2
                            )
                    })

        return results

    # =========================
    # Best FVG
    # =========================

    def get_best_fvg(
        self,
        df
    ):

        fvgs = self.scan_fvgs(df)

        if not fvgs:
            return None

        return max(
            fvgs,
            key=lambda x: x["score"]
        )
