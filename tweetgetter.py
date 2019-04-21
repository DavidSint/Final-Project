# Tweets getter script using TwitterScraper from https://github.com/taspinar/twitterscraper/

from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
import datetime as dt
from twitterscraper import query_tweets
from collections import OrderedDict
import sys
import config as cfg


# # Get gmail password from environment variable
# try:
#     gmailpassword = cfg.GMAILPASSWORD
# except KeyError:
#     print('Error, GMAILPASSWORD not stored in config.py!')
#     sys.exit(1)


# Get tickers from Data/tickers.txt
try:
    with open('Data/tickers.txt') as f:
        contents = f.readlines()
    tickers = [x.strip() for x in contents]  # tickers for S&P 100
except:
    print('Error, tickers.txt not found.')
    sys.exit(1)

# Mongo Client Details
client = MongoClient('localhost', 27017)
TweetsDB = client.TweetsDB

EMAILLOG = ""


def program():
    get_tweets()
    # send_mail()


def logticker(msg):
    print(msg)
    global EMAILLOG
    EMAILLOG = '{}<h3>{}</h3>'.format(EMAILLOG, msg)


def logtweet(url, tweetid, ticker):
    print('{} - added to DB: {}'.format(tweetid, ticker))
    global EMAILLOG
    EMAILLOG = '{}<a href="https://twitter.com{}"> {} - added to DB: {}</a><br>'.format(
        EMAILLOG, url, tweetid, ticker)


def get_tweets():
    for ticker in tickers:
        logticker(ticker)

        # Get date of last tweet
        if TweetsDB[ticker].count_documents({}) == 0:
            startdate = dt.date(2018, 10, 29)
        else:
            collection = TweetsDB[ticker].find().sort('timestamp', -1).limit(1)
            for doc in collection:
                startdate = dt.datetime.strptime(
                    doc['timestamp'], '%Y-%m-%d %H:%M:%S').date() + dt.timedelta(days=1)

        # Get yesterdays date
        finishdate = dt.datetime.now().date() - dt.timedelta(days=1)

        if startdate == finishdate:
            logticker("You are up to date!")
        else:
            # Get tweets between those days
            list_of_tweets = query_tweets('${}'.format(
                ticker), limit=300000, begindate=startdate, enddate=finishdate)

            # Make tweet objects for ticker
            for tweet in list_of_tweets:
                data = {}
                data['timestamp'] = str(tweet.timestamp)
                data['user'] = tweet.user
                data['fullname'] = tweet.fullname
                data['text'] = tweet.text
                data['replies'] = str(tweet.replies)
                data['retweets'] = str(tweet.retweets)
                data['likes'] = str(tweet.likes)

                # Write object to db
                TweetsDB[ticker].insert_one(data)
                logtweet(tweet.url, tweet.id, ticker)


def send_mail():
    # https://stackoverflow.com/questions/24077314/how-to-send-an-email-with-style-in-python3

    global EMAILLOG
    message = MIMEText(EMAILLOG, 'html')
    message['From'] = 'David S <davsint@gmail.com>'
    message['To'] = 'David S <davsint@gmail.com>'
    message['Subject'] = 'Tweet script completed at {}'.format(
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

    # Schedules get_stocks to be run every day at 00:01
    sched.add_job(program, 'cron', day_of_week='0-6', hour='0', minute='1')

    sched.start()
else:
    program()
    print("Finished")
