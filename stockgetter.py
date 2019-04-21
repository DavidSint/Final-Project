# Alpha Vantage download stock data

import requests
import time
import json
from pymongo import MongoClient
from collections import OrderedDict
import smtplib
from email.mime.text import MIMEText
import datetime as dt
import sys
import config as cfg

# gmail password from config.py
# try:
#     gmailpassword = cfg.GMAILPASSWORD
# except KeyError:
#     print('Error, GMAILPASSWORD not stored in config.py!')
#     sys.exit(1)


# API Key from config.py
try:
    KEY = cfg.AVKEY
except KeyError:
    print('Error, AVKEY not stored in config.py!')
    sys.exit(1)


BASE_URL = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=1min&outputsize=full&apikey={key}'
cnt = 0  # counter for API call Limiter
with open('Data/tickers.txt') as f:
    contents = f.readlines()
tickers = [x.strip() for x in contents]  # tickers for S&P 100

# Mongo Client Details
client = MongoClient('localhost', 27017)
StocksDB = client.StocksDB

EMAILLOG = ''


def elog(msg):
    print(msg)
    global EMAILLOG
    EMAILLOG = EMAILLOG + '<br/>' + msg


def program():
    elog(str(dt.datetime.now()))
    get_stocks(cnt)
    # send_mail()


def get_stocks(cnt):
    glblcnt = 1
    for ticker in tickers:
        if (cnt == 5):  # Made to wait a minute for API limit reset
            print("Waiting, 1 minute for API limit reset")
            time.sleep(60)
            cnt = 0

        # Access Alpha Vantage API and remove the meta info
        url = BASE_URL.format(ticker=ticker, key=KEY)
        r = requests.get(url, allow_redirects=True)
        r = r.json()
        r = r['Time Series (1min)']

        # Insert into MongoDB
        mongoInserter(r, ticker)

        elog(str(glblcnt) + ": Got and stored stock data for " + ticker)

        cnt += 1
        glblcnt += 1


def mongoInserter(data, ticker):
    """Inserts stock close and volume into the tickers collection as a new 
    document."""
    data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))
    for i in data:
        if StocksDB[ticker].find({i: {"$exists": True}}).count() > 0:
            elog("{} - already in DB: {}".format(i, ticker))
        else:
            StocksDB[ticker].insert_one(
                {i: {"close": float(data[i]["4. close"]), "volume": int(data[i]["5. volume"])}})
            elog("{} - added to DB: {}".format(i, ticker))


def send_mail():
    # https://stackoverflow.com/questions/24077314/how-to-send-an-email-with-style-in-python3

    global EMAILLOG
    message = MIMEText(EMAILLOG, 'html')
    message['From'] = 'David S <davsint@gmail.com>'
    message['To'] = 'David S <davsint@gmail.com>'
    message['Subject'] = 'Stock script completed at {}'.format(
        str(dt.datetime.now()))
    message = message.as_string()

    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.login('davsint@gmail.com', gmailpassword)
    smtpObj.sendmail('davsint@gmail.com', 'davsint@gmail.com', message)
    smtpObj.quit()


scheduler = True

if scheduler:
    from apscheduler.schedulers.blocking import BlockingScheduler
    sched = BlockingScheduler()

    # Schedules get_stocks to be run every day at 01:00
    sched.add_job(program, 'cron', day_of_week='0-5', hour='1')

    sched.start()
else:
    program()
    print("Finished")
