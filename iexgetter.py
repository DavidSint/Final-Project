from datetime import datetime, timedelta
from iexfinance.stocks import get_historical_intraday
from pymongo import MongoClient
import json
import pandas as pd

from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR


def weekdays(start_date, end_date):
    return rrule(DAILY, dtstart=start_date, until=end_date, byweekday=(MO, TU, WE, TH, FR))


# Mongo Client Details
client = MongoClient('localhost', 27017)
StocksDB = client.TestStocksDB


def mongoInserter(data, ticker):
    """Inserts stock close and volume into the tickers collection as a new 
    document."""
    for i in data:
        if StocksDB[ticker].find({"timestamp": i['timestamp']}).count() > 0:
            print("{} - already in DB: {}".format(i['timestamp'], ticker))
        else:
            StocksDB[ticker].insert_one(i)
            print("{} - added to DB: {}".format(i['timestamp'], ticker))


start_date = datetime(2019, 3, 27).date()
end_date = datetime(2019, 3, 28).date()

error = []
for day in weekdays(start_date, end_date):
    for ticker in open('Data/tickers.txt', 'r'):
        ticker = ticker.strip()
        try:
            print(ticker, day)
            try:
                df = get_historical_intraday(
                    ticker, day, output_format='pandas')
            except:
                # For this API, the ticker names sometimes have a convention where x class shares
                # are classed as ticker.x rather than tickerx e.g. BRKB == BRK.B
                # this try, except block attempts both conventions.
                df = get_historical_intraday(
                    ticker[:-1] + "." + ticker[-1:], day, output_format='pandas')
            print("got data")
            try:
                df = df[['close', 'volume']].reset_index()
                df.rename(columns={'index': 'timestamp'}, inplace=True)
                df['timestamp'] = df['timestamp'] + pd.Timedelta(minutes=1)
                df['timestamp'] = df['timestamp'].dt.strftime(
                    '%Y-%m-%d %H:%M:%S')

                records = json.loads(df.T.to_json()).values()
                mongoInserter(records, ticker)
            except KeyError as e:
                # If the day doesn't exist in the APIs database, then record this as an error and continue.
                error.append([ticker, day, e])
                print([ticker, day, e])
                pass
        except:
            # If there is a genuine error, raise it immediately.
            raise
print("Errors skipped:", error)
