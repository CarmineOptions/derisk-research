import matplotlib.pyplot as plt
from web_app.ekubo.main import EkuboOrderBook

TOKEN_A = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
TOKEN_B = (
    "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
)

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
    ask_prices, ask_quantities = zip(*data['asks'])
    bid_prices, bid_quantities = zip(*data['bids'])

    ask_prices = [float(price) for price in ask_prices]
    ask_quantities = [float(quantity) for quantity in ask_quantities]
    bid_prices = [float(price) for price in bid_prices]
    bid_quantities = [float(quantity) for quantity in bid_quantities]

    # Create the figure and axis
    fig, ax = plt.subplots()

    # Plot asks and bids
    ax.barh(ask_prices, ask_quantities, color='red', label='Asks')
    ax.barh(bid_prices, bid_quantities, color='green', label='Bids')

    # Highlight the current price
    ax.axhline(current_price, color='black', linestyle='--', linewidth=4, label='Current Price')

    # Labels and title
    ax.set_xlabel('Quantity (ETH)')
    ax.set_ylabel('Price (USDT)')
    ax.set_title('Order Book')
    ax.legend()

    #  Adjust limits to make sure the current price line is visible
    ax.set_xlim(0, max(max(ask_quantities), max(bid_quantities)) * 1.1)
    ax.set_ylim(min(bid_prices) - 10, max(ask_prices) + 10)

    # Show the plot
    plt.show()