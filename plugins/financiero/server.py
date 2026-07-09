import yfinance as yf

def run(params):
    ticker = params.get("ticker", "AAPL")
    stock = yf.Ticker(ticker)
    precio = stock.history(period="1d")["Close"].iloc[-1]
    return f"El precio actual de {ticker} es {precio:.2f}"