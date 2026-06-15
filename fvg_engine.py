"""
fvg_engine.py
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

    def volume_ratio(
        self,
        df
    ):

        return (
            df["Volume"] /
            df["Volume"]
            .rolling(20)
            .mean()
        )

    def scan_fvgs(
        self,
        df
    ):

        if len(df) < 30:
            return []

        df = df.copy()

        df["ATR"] = self.calculate_atr(df)

        df["VolumeRatio"] = (
            self.volume_ratio(df)
        )

        results = []

        start = max(
            2,
            len(df) - 20
        )

        for i in range(
            start,
            len(df) - 1
        ):

            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1]
            c3 = df.iloc[i]

            atr = c2["ATR"]

            if pd.isna(atr):
                continue

            candle_range = max(
                c2["High"] -
                c2["Low"],
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

            volume_ratio = (
                c2["VolumeRatio"]
            )

            # ------------------
            # Bullish FVG
            # ------------------

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

                    score = self.score_fvg(
                        gap_atr,
                        volume_ratio,
                        body_ratio
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
                            float(
                                c1["High"]
                            ),

                        "fvg_high":
                            float(
                                c3["Low"]
                            )
                    })

            # ------------------
            # Bearish FVG
            # ------------------

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

                    score = self.score_fvg(
                        gap_atr,
                        volume_ratio,
                        body_ratio
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
                            float(
                                c3["High"]
                            ),

                        "fvg_high":
                            float(
                                c1["Low"]
                            )
                    })

        return results

    def score_fvg(
        self,
        gap_atr,
        volume_ratio,
        body_ratio
    ):

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
