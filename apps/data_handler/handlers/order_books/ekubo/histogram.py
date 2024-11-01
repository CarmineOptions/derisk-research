""" A script to display order book histograms for the Ekubo DEX. """
import argparse
from decimal import Decimal
from typing import List

import matplotlib.pyplot as plt

from web_app.order_books.ekubo.main import EkuboOrderBook

TOKEN_A = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
TOKEN_B = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC


def fetch_order_book_and_current_price(token_a: str, token_b: str) -> tuple[dict, Decimal]:
    """
    Fetch the order book and current price for the given token pair.
    :param token_a: Base token contract address
    :param token_b: Quote token contract address
    :return: Tuple containing the order book and current price
    The structure of the order book data dict is as follows:
    {
        "token_a": "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        "token_b": "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        "timestamp": 1634160000,
        "block": 6343456,
        "dex": "Ekubo",
        "asks": [(Decimal("123.76534"), Decimal("456.53423")), ...],
        "bids": [(Decimal("678.45345"), Decimal("910.43567")), ...],
    }
    """
    order_book = EkuboOrderBook(token_a, token_b)
    order_book.fetch_price_and_liquidity()
    return order_book.get_order_book(), order_book.current_price


class Histogram:
    """
    A class to create and display histograms for order book data.

    Attributes:
        fig (plt.Figure): The matplotlib figure object.
        ax (plt.Axes): The matplotlib axes object.
        ask_prices (List[float]): List of ask prices.
        ask_quantities (List[float]): List of ask quantities.
        bid_prices (List[float]): List of bid prices.
        bid_quantities (List[float]): List of bid quantities.
        current_price (float): The current market price.
    """

    def __init__(self):
        """Initialize the Histogram with an empty plot and collect order book data."""
        self.fig, self.ax = plt.subplots()
        self._collect_data()

    def add_label(self, quantity_name: str, price_name: str) -> None:
        """
        Add labels to the histogram.

        Args:
            quantity_name (str): The name of the quantity.
            price_name (str): The name of the price.
        """
        self.ax.set_xlabel(f"Quantity ({quantity_name})")
        self.ax.set_ylabel(f"Price ({price_name})")
        self.ax.legend()

    def _collect_data(self) -> None:
        """Collect order book data and convert to float."""
        data, current_price = fetch_order_book_and_current_price(TOKEN_A, TOKEN_B)

        ask_prices, ask_quantities = zip(*data["asks"])
        bid_prices, bid_quantities = zip(*data["bids"])

        self.ask_prices = [float(price) for price in ask_prices]
        self.ask_quantities = [float(quantity) for quantity in ask_quantities]
        self.bid_prices = [float(price) for price in bid_prices]
        self.bid_quantities = [float(quantity) for quantity in bid_quantities]

        self.current_price = float(current_price)

    def add_current_price_line(self, max_quantity: float = 0) -> None:
        """
        Add a line representing the current price to the histogram.

        Args:
            max_quantity (float): The maximum quantity to set the width of the line. Defaults to 0.
        """
        self.ax.barh(
            [self.current_price],
            max_quantity,
            color="black",
            height=20,
            label="Current Price",
        )
        min_price = min(min(self.bid_prices), min(self.ask_prices), self.current_price)
        max_price = max(max(self.bid_prices), max(self.ask_prices), self.current_price)
        self.ax.set_ylim(min_price - 100, max_price + 100)  # Adding some buffer

    def add_asks(self) -> None:
        """Add ask prices and quantities to the histogram."""
        self.ax.barh(self.ask_prices, self.ask_quantities, color="red", label="Asks", height=15)

    def add_bids(self) -> None:
        """Add bid prices and quantities to the histogram."""
        self.ax.barh(self.bid_prices, self.bid_quantities, color="green", label="Bids", height=15)

    def add_total_box_quantity(self, quantities_name: str, sum_quantities: float) -> None:
        """
        Add a text box displaying the total quantity.

        Args:
            quantities_name (str): The name of the quantities.
            sum_quantities (float): The sum of the quantities.
        """
        total_quantity = round(sum_quantities, 4)
        textstr = f"Total {quantities_name} Quantity: {total_quantity}"
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        self.ax.text(
            0.95,
            1.05,
            textstr,
            transform=self.ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=props,
        )

    def show_asks(self) -> None:
        """Display the asks histogram with the current price line and total quantity."""
        self.add_current_price_line(max(self.ask_quantities))
        self.add_asks()
        self.add_label("ETH", "USDC")
        self.add_total_box_quantity("ETH", sum(self.ask_quantities))
        plt.show()

    def show_bids(self) -> None:
        """Display the bids histogram with the current price line and total quantity."""
        self.add_current_price_line(max(self.bid_quantities))
        self.add_bids()
        self.add_label("USDC", "ETH")
        self.add_total_box_quantity("USDC", sum(self.bid_quantities))
        plt.show()


def main():
    """ Main function to parse command line arguments and display histograms. """
    parser = argparse.ArgumentParser(description="Display order book histograms.")
    parser.add_argument(
        "--type",
        choices=["asks", "bids"],
        required=True,
        help="Type of histogram to display: 'asks' or 'bids'.",
    )

    args = parser.parse_args()

    histogram = Histogram()
    if args.type == "asks":
        histogram.show_asks()
    elif args.type == "bids":
        histogram.show_bids()


if __name__ == "__main__":
    main()
