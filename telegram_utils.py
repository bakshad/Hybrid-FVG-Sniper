"""
telegram_utils.py

Telegram notification layer.
"""

import requests

from config import (
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID
)


class TelegramBot:

    def __init__(self):

        self.token = TELEGRAM_TOKEN

        self.chat_id = TELEGRAM_CHAT_ID

    # =========================
    # Core Sender
    # =========================

    def send_message(
        self,
        message
    ):

        if not self.token:

            print(
                "[INFO] Telegram disabled"
            )

            return

        try:

            url = (
                f"https://api.telegram.org/bot"
                f"{self.token}/sendMessage"
            )

            payload = {

                "chat_id":
                    self.chat_id,

                "text":
                    message,

                "parse_mode":
                    "HTML"
            }

            requests.post(
                url,
                json=payload,
                timeout=20
            )

        except Exception as e:

            print(
                f"Telegram Error: {e}"
            )

    # =========================
    # Entry Alert
    # =========================

    def send_entry_alert(
        self,
        position
    ):

        msg = f"""
🔥 <b>{position['Grade']}</b>

Symbol: {position['Symbol']}

Side: {position['Side']}

Score: {position['Score']}

Entry: {position['Entry']}

SL: {position['SL']}

T1: {position['T1']}

T2: {position['T2']}

Qty: {position['Qty']}
"""

        self.send_message(msg)

    # =========================
    # T1 Alert
    # =========================

    def send_t1_alert(
        self,
        symbol
    ):

        msg = f"""
🎯 T1 HIT

{symbol}

SL moved to Breakeven
"""

        self.send_message(msg)

    # =========================
    # T2 Alert
    # =========================

    def send_t2_alert(
        self,
        symbol
    ):

        msg = f"""
🎯 T2 HIT

{symbol}

SL moved to T1
"""

        self.send_message(msg)

    # =========================
    # Exit Alert
    # =========================

    def send_exit_alert(
        self,
        trade
    ):

        msg = f"""
🏁 EXIT

Symbol: {trade['Symbol']}

Side: {trade['Side']}

PnL: ₹{trade['PnL']}

Reason:
{trade['ExitReason']}
"""

        self.send_message(msg)

    # =========================
    # Daily Summary
    # =========================

    def send_summary(
        self,
        text
    ):

        msg = f"""
📊 DAILY SUMMARY

{text}
"""

        self.send_message(msg)
