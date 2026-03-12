import yfinance as yf

def fetch_major_indices() -> str:
    """Fetches the current daily performance of major US market indices (S&P 500, Nasdaq, Dow Jones)"""
    indices = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones"}
    result = "Major US Indices Performance Today:\n"
    
    for ticker, name in indices.items():
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")
            if not hist.empty:
                close_price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
                pct_change = ((close_price - open_price) / open_price) * 100
                result += f"- {name} ({ticker}): {close_price:.2f} ({pct_change:+.2f}%)\n"
            else:
                result += f"- {name} ({ticker}): No data available for today.\n"
        except Exception as e:
            result += f"- {name} ({ticker}): Error fetching data ({e})\n"
            
    return result

def fetch_top_tech_stocks() -> str:
    """Fetches the current daily performance of major tech stocks (AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA, META)"""
    stocks = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META"]
    result = "Top Tech Stocks Performance Today:\n"
    
    for ticker in stocks:
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")
            if not hist.empty:
                close_price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
                pct_change = ((close_price - open_price) / open_price) * 100
                result += f"- {ticker}: {close_price:.2f} ({pct_change:+.2f}%)\n"
            else:
                result += f"- {ticker}: No data available for today.\n"
        except Exception as e:
            result += f"- {ticker}: Error fetching data ({e})\n"
            
    return result
