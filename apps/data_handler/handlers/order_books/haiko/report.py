""" This module is used to generate a report with order books data for all token pairs. """
import json
import logging
from datetime import datetime
from pathlib import Path

from data_handler.handlers.order_books.constants import TOKEN_MAPPING
from data_handler.handlers.order_books.haiko.main import HaikoOrderBook


def filter_logs(logs_path: Path) -> None:
    """
    Remove empty log files.
    :param logs_path: Path to the directory with log files.
    """
    for file in logs_path.iterdir():
        if file.stat().st_size == 0:
            file.unlink()


def serialize_asks_bids(order_book: dict) -> None:
    """
    Convert asks and bids to serializable format.
    :param order_book: Order book data.
    """
    order_book["asks"] = [[float(ask[0]), float(ask[1])] for ask in order_book["asks"]]
    order_book["bids"] = [[float(bid[0]), float(bid[1])] for bid in order_book["bids"]]


def get_report() -> dict:
    """
    Get report for all token pairs.
    :return: Report with order books data.
    The report structure is as follows:
    {
        "empty_pairs": [STRK-ETH, ...],
        "ETH-USDC": {
            "is_empty": False,
            "order_book": {
                "asks": [[price1, amount1], [price2, amount2], ...],
                "bids": [[price1, amount1], [price2, amount2], ...]
            }
        },
        ...
    }
    """
    report = {"empty_pairs": []}
    all_tokens = set(TOKEN_MAPPING.keys())

    for base_token in TOKEN_MAPPING:
        current_tokens = all_tokens - {base_token}
        for quote_token in current_tokens:
            try:
                order_book = HaikoOrderBook(base_token, quote_token)
            except ValueError:
                logging.log(logging.ERROR, f"Pair of tokens: {base_token}-{quote_token}")
                logging.log(logging.ERROR, "One of the tokens isn't supported by Haiko")
                continue
            except RuntimeError as e:
                logging.log(logging.ERROR, f"Pair of tokens: {base_token}-{quote_token}")
                logging.log(logging.ERROR, e)
                continue

            try:
                base_token_name = TOKEN_MAPPING[base_token].name
                quote_token_name = TOKEN_MAPPING[quote_token].name
                order_book.fetch_price_and_liquidity()
                token_pair = f"{base_token_name}-{quote_token_name}"
                report[token_pair] = {"is_empty": False, "order_book": {}}
                entry = order_book.get_order_book()
                serialize_asks_bids(entry)
                report[token_pair]["order_book"] = entry
                if not order_book.bids and not order_book.asks:
                    report[token_pair]["is_empty"] = True
                    report["empty_pairs"].append(token_pair)
            except KeyError:
                order_book.logger.error(f"Pair of tokens: {base_token}-{quote_token}")
                order_book.logger.error("One of the tokens doesn't present in tokens mapping")
            except RuntimeError as e:
                order_book.logger.error(f"Pair of tokens: {base_token}-{quote_token}")
                order_book.logger.error(e)
            except Exception as e:
                order_book.logger.error(f"Pair of tokens: {base_token}-{quote_token}")
                order_book.logger.error(f"Unexpected error: {e}")

    return report


def write_report(report: dict, path: str | Path) -> None:
    """
    Write report to a json file.
    :param report: Report data.
    :param path: Path to the file.
    """
    try:
        with open(path, mode="w", encoding="UTF-8") as file:
            json.dump(report, file, indent=4)
    except IOError as e:
        print(f"Error writing report: {e}")


if __name__ == "__main__":
    report_data = get_report()
    reports_dir = Path("./reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / datetime.now().strftime("report_%Y%m%d_%H%M%S.json")
    filter_logs(reports_dir)
    write_report(report_data, report_path)
