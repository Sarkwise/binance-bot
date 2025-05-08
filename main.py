def get_current_price(symbol="BTCUSDT"):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

import requests

from binance.client import Client
import pandas as pd
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator

# 1. Set your Binance API credentials
API_KEY = 'VJEu8nhUzelNe4NZAjRYxEzD7GFuwWuaVIGpgKhwpn1k2EjesSl7vEp3rGEWNs5l'
API_SECRET = 'ktoj75wNhuFDKAOmL71hDIdwGatoIJUjubhKeZCKNPqElDw6fsvlGNR2f6ARkeXi'

# Telegram Bot Settings
TELEGRAM_TOKEN = '7697892603:AAEpDNsR7DWmw2D8upj_N_N_hPADIjowYhs'
CHAT_ID = '986048210'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    requests.post(url, data=payload)

# Exit Strategy
TAKE_PROFIT_PERCENT = 0.02  # 2%
STOP_LOSS_PERCENT = 0.01    # 1%


# 2. Connect to Binance
client = Client(API_KEY, API_SECRET)

# 3. Function to get historical candlestick data
def get_historical_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_1HOUR, lookback="3 days ago UTC"):
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

# 4. Add indicators
def add_indicators(df):
    df['SMA_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['RSI_14'] = RSIIndicator(close=df['close'], window=14).rsi()
    return df

# 5. Main bot logic
btc_data = get_historical_klines()
btc_data = add_indicators(btc_data)

# 6. Basic buy/sell signal logic with Telegram alerts
latest = btc_data.iloc[-1]
previous = btc_data.iloc[-2]

if (latest['RSI_14'] < 30) and (previous['close'] < previous['SMA_20']) and (latest['close'] > latest['SMA_20']):
    signal = "📈 Buy Signal: Price may rise!"
elif (latest['RSI_14'] > 70) and (previous['close'] > previous['SMA_20']) and (latest['close'] < latest['SMA_20']):
    signal = "📉 Sell Signal: Price may fall!"
else:
    signal = "⏳ No clear signal. Hold position."

print(f"\n{signal}")
send_telegram_message(signal)

import time

# Store entry price if signal is triggered
entry_price = None
position_type = None  # "BUY" or "SELL"

if (latest['RSI_14'] < 30) and (previous['close'] < previous['SMA_20']) and (latest['close'] > latest['SMA_20']):
    signal = "📈 Buy Signal: Price may rise!"
    entry_price = latest['close']
    position_type = "BUY"
elif (latest['RSI_14'] > 70) and (previous['close'] > previous['SMA_20']) and (latest['close'] < latest['SMA_20']):
    signal = "📉 Sell Signal: Price may fall!"
    entry_price = latest['close']
    position_type = "SELL"
else:
    signal = "⏳ No clear signal. Hold position."

print(f"\n{signal}")
send_telegram_message(signal)


