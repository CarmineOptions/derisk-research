import matplotlib.pyplot as plt
from web_app.ekubo.main import EkuboOrderBook

TOKEN_A = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
TOKEN_B = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC


def fetch_order_book_and_current_price(token_a: str, token_b: str) -> tuple:
    """
    Fetch the order book and current price for the given token pair.
    :param token_a: Base token contract address
    :param token_b: Quote token contract address
    :return: Tuple containing the order book and current price
    """
    order_book = EkuboOrderBook(token_a, token_b)
    order_book.fetch_price_and_liquidity()
    return order_book.get_order_book(), order_book.current_price


if __name__ == "__main__":
    data, current_price = fetch_order_book_and_current_price(TOKEN_A, TOKEN_B)
    # Extract data for plotting and convert to float
    ask_prices, ask_quantities = zip(*data["asks"])
    bid_prices, bid_quantities = zip(*data["bids"])

    ask_prices = [float(price) for price in ask_prices]
    ask_quantities = [float(quantity) for quantity in ask_quantities]
    bid_prices = [float(price) for price in bid_prices]
    bid_quantities = [float(quantity) for quantity in bid_quantities]

    # Convert current_price to float
    current_price = float(current_price)

    fig, ax = plt.subplots()
    # Add current price line
    ax.barh(
        [current_price],
        max((max(bid_quantities), max(ask_quantities))),
        color="black",
        height=20,
        label="Current Price",
    )

    # Plot asks and bids
    ax.barh(ask_prices, ask_quantities, color="red", label="Asks", height=5)
    ax.barh(bid_prices, bid_quantities, color="green", label="Bids", height=5)

    # Set y-axis limits to include current_price
    min_price = min(min(bid_prices), min(ask_prices), current_price)
    max_price = max(max(bid_prices), max(ask_prices), current_price)
    ax.set_ylim(min_price - 100, max_price + 100)  # Adding some buffer

    # Labels and title
    ax.set_xlabel("Quantity (ETH)")
    ax.set_ylabel("Price (USDC)")
    ax.set_title("Order Book")
    ax.legend()

    # Show the plot
    plt.show()
