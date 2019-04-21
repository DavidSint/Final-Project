from datetime import datetime, timedelta, time
from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR

DATA_PATH = "Data/"


def ticker_scroll(action):
    '''
    Goes through the tickers.txt file and will enact a given function on each ticker
    '''
    for ticker in open(DATA_PATH + 'tickers.txt', 'r'):
        ticker = ticker.strip()
        action(ticker)


def weekdays(start_date, end_date):
    '''
    returns the weekdays between the given start date and end date
    https://stackoverflow.com/questions/11550314/python-date-range-generator-over-business-days
    '''
    return rrule(DAILY, dtstart=start_date, until=end_date, byweekday=(MO, TU, WE, TH, FR))
