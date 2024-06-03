from handlers.order_books.uniswap_v2.main import UniswapV2OrderBook

if __name__ == '__main__':
    # TODO: delete this file
    token_a = "ETH"
    token_b = (
        "USDC"
    )
    order_book = UniswapV2OrderBook(token_a, token_b)
    order_book.fetch_price_and_liquidity()
    print(order_book.get_order_book(), "\n")
