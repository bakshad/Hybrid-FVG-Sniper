"""
data_provider.py

Market data layer.

Primary Source:
    Yahoo Finance

Future:
    5Paisa Adapter
"""

import pandas as pd
import yfinance as yf

from config import (
    DAILY_LOOKBACK,
    HOUR_LOOKBACK,
    M15_LOOKBACK
)


class DataProvider:

    def __init__(self):
        pass

    # =========================
    # Daily
    # =========================

    def get_daily_data(
        self,
        symbol
    ):

        try:

            df = yf.download(
                f"{symbol}.NS",
                period=f"{DAILY_LOOKBACK}d",
                interval="1d",
                auto_adjust=True,
                progress=False
            )

            return self._clean_df(df)

        except Exception as e:

            print(
                f"[ERROR] Daily {symbol}: {e}"
            )

            return pd.DataFrame()

    # =========================
    # 60m
    # =========================

    def get_60m_data(
        self,
        symbol
    ):

        try:

            df = yf.download(
                f"{symbol}.NS",
                period=f"{HOUR_LOOKBACK}d",
                interval="60m",
                auto_adjust=True,
                progress=False
            )

            return self._clean_df(df)

        except Exception as e:

            print(
                f"[ERROR] 60m {symbol}: {e}"
            )

            return pd.DataFrame()

    # =========================
    # 15m
    # =========================

    def get_15m_data(
        self,
        symbol
    ):

        try:

            df = yf.download(
                f"{symbol}.NS",
                period=f"{M15_LOOKBACK}d",
                interval="15m",
                auto_adjust=True,
                progress=False
            )

            return self._clean_df(df)

        except Exception as e:

            print(
                f"[ERROR] 15m {symbol}: {e}"
            )

            return pd.DataFrame()

    # =========================
    # Validation
    # =========================

    def is_valid(
        self,
        df,
        minimum_rows=50
    ):

        if df is None:
            return False

        if len(df) < minimum_rows:
            return False

        return True

    # =========================
    # Cleanup
    # =========================

    def _clean_df(
        self,
        df
    ):

        if df is None:
            return pd.DataFrame()

        if len(df) == 0:
            return pd.DataFrame()

        df = df.copy()

        df.dropna(
            inplace=True
        )

        cols = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        for col in cols:

            if col not in df.columns:

                return pd.DataFrame()

        return df
