import os
import requests 
import time
import pandas as pd
from binance.client import Client
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# Binance API credentials from environment variables
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Telegram Bot Settings from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Exit Strategy Settings
TAKE_PROFIT_PERCENT = 0.10  # 10%
STOP_LOSS_PERCENT = 0.05    # 5%

# Connect to Binance
client = Client(API_KEY, API_SECRET)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=payload)

def get_historical_klines(symbol, interval=Client.KLINE_INTERVAL_1HOUR, lookback="3 days ago UTC"):
    klines = client.get_historical_klines(symbol, interval, lookback)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

def add_indicators(df):
    df['SMA_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['RSI_14'] = RSIIndicator(close=df['close'], window=14).rsi()

    macd = MACD(close=df['close'])
    df['MACD'] = macd.macd()
    df['MACD_SIGNAL'] = macd.macd_signal()

    bb = BollingerBands(close=df['close'])
    df['BB_UPPER'] = bb.bollinger_hband()
    df['BB_LOWER'] = bb.bollinger_lband()
    return df

def analyze_symbol(symbol):
    df = get_historical_klines(symbol)
    df = add_indicators(df)

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    entry_price = None
    position_type = None

    buy_conditions = (
        latest['RSI_14'] < 30 and
        previous['close'] < previous['SMA_20'] and
        latest['close'] > latest['SMA_20'] and
        latest['MACD'] > latest['MACD_SIGNAL'] and
        latest['close'] < latest['BB_LOWER']
    )

    sell_conditions = (
        latest['RSI_14'] > 70 and
        previous['close'] > previous['SMA_20'] and
        latest['close'] < latest['SMA_20'] and
        latest['MACD'] < latest['MACD_SIGNAL'] and
        latest['close'] > latest['BB_UPPER']
    )

    if buy_conditions:
        signal = f"\U0001F4C8 Strong Buy Signal for {symbol}: Multiple indicators align for upside potential."
        entry_price = latest['close']
        position_type = "BUY"
    elif sell_conditions:
        signal = f"\U0001F4C9 Strong Sell Signal for {symbol}: Multiple indicators align for downside risk."
        entry_price = latest['close']
        position_type = "SELL"
    else:
        signal = f"\u23F3 No strong signal for {symbol}. Indicators do not align."

    print(f"\n{signal}")
    send_telegram_message(signal)

    if entry_price and position_type:
        take_profit = entry_price * (1 + TAKE_PROFIT_PERCENT) if position_type == "BUY" else entry_price * (1 - TAKE_PROFIT_PERCENT)
        stop_loss = entry_price * (1 - STOP_LOSS_PERCENT) if position_type == "BUY" else entry_price * (1 + STOP_LOSS_PERCENT)

        send_telegram_message(f"{symbol} {position_type} Entry: {entry_price:.2f}\nTP: {take_profit:.2f}, SL: {stop_loss:.2f}")

def main():
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    for symbol in symbols:
        analyze_symbol(symbol)

if __name__ == "__main__":
    main()
