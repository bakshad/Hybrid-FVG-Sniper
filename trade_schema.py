import os
import pandas as pd

from config import (
    ACTIVE_POSITIONS_FILE,
    TRADE_HISTORY_FILE,
    SIGNAL_DATASET_FILE
)


ACTIVE_COLUMNS = [

    "Symbol",

    "Side",

    "Entry",

    "SL",

    "SweepLevel",

    "InitialRisk",

    "Qty",

    "RemainingQty",

    "T1Qty",

    "T2Qty",

    "RunnerQty",

    "RealizedPnL",

    "EntryCapital",

    "Score",

    "Grade",

    "T1",

    "T2",

    "T1Hit",

    "T2Hit",

    "RunnerActive",

    "HighestPrice",

    "LowestPrice",

    "ChandelierStop",

    "EntryTime",

    "LastUpdateTime",

    "Status"
]

HISTORY_COLUMNS = [

    "EntryTime",

    "ExitTime",

    "Symbol",

    "Side",

    "Score",

    "Grade",

    "Entry",

    "Exit",

    "Qty",

    "PnL",

    "PnLPct",

    "RMultiple",

    "DaysHeld",

    "ExitReason"
]


SIGNAL_COLUMNS = [

    "Date",

    "Symbol",

    "Side",

    "Score",

    "Grade",

    "GapATR",

    "VolumeRatio",

    "BodyRatio",

    "SweepStrength",

    "TrendStrength",

    "Entry",

    "SL",

    "Outcome"
]


def create_csv_if_missing(
    path,
    columns
):

    if not os.path.exists(path):

        pd.DataFrame(
            columns=columns
        ).to_csv(
            path,
            index=False
        )


def initialize_storage():

    create_csv_if_missing(
        ACTIVE_POSITIONS_FILE,
        ACTIVE_COLUMNS
    )

    create_csv_if_missing(
        TRADE_HISTORY_FILE,
        HISTORY_COLUMNS
    )

    create_csv_if_missing(
        SIGNAL_DATASET_FILE,
        SIGNAL_COLUMNS
    )


def load_active_positions():

    initialize_storage()

    return pd.read_csv(
        ACTIVE_POSITIONS_FILE
    )


def save_active_positions(df):

    df.to_csv(
        ACTIVE_POSITIONS_FILE,
        index=False
    )


def append_trade_history(record):

    initialize_storage()

    df = pd.read_csv(
        TRADE_HISTORY_FILE
    )

    df = pd.concat(
        [
            df,
            pd.DataFrame([record])
        ],
        ignore_index=True
    )

    df.to_csv(
        TRADE_HISTORY_FILE,
        index=False
    )


def append_signal_dataset(record):

    initialize_storage()

    df = pd.read_csv(
        SIGNAL_DATASET_FILE
    )

    df = pd.concat(
        [
            df,
            pd.DataFrame([record])
        ],
        ignore_index=True
    )

    df.to_csv(
        SIGNAL_DATASET_FILE,
        index=False
    )
