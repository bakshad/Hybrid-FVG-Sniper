"""
main.py

FVG Runner Bot
"""

import pandas as pd

from config import (
    STARTING_CAPITAL,
    DYNAMIC_EQUITY,
    MAX_ACTIVE_TRADES,
    MAX_NEW_TRADES_PER_DAY,
    MIN_SCORE
)

from trade_schema import (
    initialize_storage,
    load_active_positions,
    save_active_positions,
    append_trade_history,
    get_current_capital,
    load_fno_symbols
)

from data_provider import DataProvider

from fvg_engine import FVGEngine

from structure_engine import (
    StructureEngine
)

from score_engine import (
    ScoreEngine
)

from trade_manager import (
    TradeManager
)

from telegram_utils import (
    TelegramBot
)

data_provider = DataProvider()

fvg_engine = FVGEngine()

structure_engine = (
    StructureEngine()
)

score_engine = (
    ScoreEngine()
)

trade_manager = (
    TradeManager()
)

def get_capital():

    if DYNAMIC_EQUITY:

        return get_current_capital(
            STARTING_CAPITAL
        )

    return STARTING_CAPITAL
telegram = TelegramBot()

def manage_positions():

    positions = (
        load_active_positions()
    )

    if len(positions) == 0:

        return positions

    updated_positions = []

    for _, row in (
        positions.iterrows()
    ):

        position = row.to_dict()

        symbol = (
            position["Symbol"]
        )

        df_daily = (
            data_provider
            .get_daily_data(
                symbol
            )
        )

        if (
            not data_provider
            .is_valid(
                df_daily
            )
        ):
            continue
        current_price = float(
            df_daily["Close"]
            .iloc[-1]
        )
        trade_manager.update_price_tracking(
            position,
            current_price
        )

        trade_manager.update_chandelier(
            position,
            df_daily
        )
        event = (
            trade_manager
            .process_t1(
                position,
                current_price
            )
        )

        if event == "T1_HIT":

            telegram.send_t1_alert(
                symbol
            )
        event = (
            trade_manager
            .process_t2(
                position,
                current_price
            )
        )

        if event == "T2_HIT":

            telegram.send_t2_alert(
                symbol
            )
        exit_reason = (
            trade_manager
            .check_exit(
                position,
                current_price
            )
        )
        if exit_reason:

            trade = (
                trade_manager
                .close_position(
                    position,
                    current_price,
                    exit_reason
                )
            )

            append_trade_history(
                trade
            )

            telegram.send_exit_alert(
                trade
            )

            continue

        updated_positions.append(
            position
        )

    return pd.DataFrame(
        updated_positions
    )

# ==================================================
# Scan New Trade Opportunities
# ==================================================

def scan_signals(
    capital,
    active_positions
):

    symbols = load_fno_symbols()

    active_symbols = set()

    if len(active_positions) > 0:

        active_symbols = set(
            active_positions["Symbol"].tolist()
        )

    signals = []

    for symbol in symbols:

        print(f"Scanning {symbol}")

        try:

            if symbol in active_symbols:
                continue

            # ----------------------------------
            # Daily Data
            # ----------------------------------

            df_daily = (
                data_provider.get_daily_data(
                    symbol
                )
            )

            if not data_provider.is_valid(
                df_daily
            ):
                continue

            # ----------------------------------
            # ATR
            # ----------------------------------

            df_daily["ATR"] = (
                fvg_engine.calculate_atr(
                    df_daily
                )
            )

            # ----------------------------------
            # FVG
            # ----------------------------------

            fvg = (
                fvg_engine.get_best_fvg(
                    df_daily
                )
            )

            if not fvg:

                print(
                    f"{symbol}: No FVG"
                )

                continue

            # ----------------------------------
            # Direction
            # ----------------------------------

            side = (
                "BUY"
                if fvg["type"] == "BULLISH"
                else "SELL"
            )

            # ----------------------------------
            # Intraday Data
            # ----------------------------------

            df_60m = (
                data_provider.get_60m_data(
                    symbol
                )
            )

            df_15m = (
                data_provider.get_15m_data(
                    symbol
                )
            )

            if not data_provider.is_valid(
                df_60m
            ):
                continue

            if not data_provider.is_valid(
                df_15m
            ):
                continue

            # ----------------------------------
            # Structure Validation
            # ----------------------------------

            structure = (
                structure_engine.evaluate(
                    side,
                    df_60m,
                    df_15m
                )
            )

            if not structure:

                print(
                    f"{symbol}: Structure Failed"
                )

                continue

            # ----------------------------------
            # Build Signal
            # ----------------------------------

            signal = (
                score_engine.build_signal(
                    symbol,
                    side,
                    fvg,
                    structure
                )
            )

            print(
                f"{symbol}: "
                f"Score={signal['Score']} "
                f"Grade={signal['Grade']}"
            )
            
            if signal["Score"] < MIN_SCORE:

                print(
                    f"{symbol}: "
                    f"Rejected Score "
                    f"{signal['Score']}"
                )

                continue

            # ----------------------------------
            # Entry
            # ----------------------------------

            entry = float(
                df_daily["Close"].iloc[-1]
            )

            atr = float(
                df_daily["ATR"].iloc[-1]
            )

            # ----------------------------------
            # Create Position
            # ----------------------------------

            position = (
                trade_manager.create_position(

                    symbol=symbol,

                    side=side,

                    entry=entry,

                    sweep_level=
                    structure[
                        "sweep_level"
                    ],

                    atr=atr,

                    score=
                    signal["Score"],

                    grade=
                    signal["Grade"],

                    capital=capital
                )
            )

            if position:

                signals.append(
                    position
                )

        except Exception as e:

            print(
                f"[SCAN ERROR] "
                f"{symbol}: {e}"
            )

    # ----------------------------------
    # Rank Signals
    # ----------------------------------

    signals = sorted(
        signals,
        key=lambda x: x["Score"],
        reverse=True
    )

    return signals[
        :MAX_NEW_TRADES_PER_DAY
    ]


# ==================================================
# Main
# ==================================================

def main():

    initialize_storage()

    capital = get_capital()

    print(
        f"\nCurrent Capital: "
        f"{capital}"
    )

    # ----------------------------------
    # Manage Existing Trades
    # ----------------------------------

    active_positions = (
        manage_positions()
    )

    available_slots = (

        MAX_ACTIVE_TRADES

        -

        len(active_positions)
    )

    print(
        f"Open Trades: "
        f"{len(active_positions)}"
    )

    print(
        f"Available Slots: "
        f"{available_slots}"
    )

    # ----------------------------------
    # Scan New Trades
    # ----------------------------------

    if available_slots > 0:

        new_positions = (
            scan_signals(
                capital,
                active_positions
            )
        )

        new_positions = (
            new_positions[
                :available_slots
            ]
        )

        for position in new_positions:

            telegram.send_entry_alert(
                position
            )

        combined = pd.concat(
            [
                active_positions,

                pd.DataFrame(
                    new_positions
                )
            ],
            ignore_index=True
        )

    else:

        combined = (
            active_positions
        )

    # ----------------------------------
    # Save
    # ----------------------------------

    save_active_positions(
        combined
    )

    print(
        f"Saved "
        f"{len(combined)} "
        f"active positions"
    )


# ==================================================
# Run
# ==================================================

if __name__ == "__main__":

    main()
