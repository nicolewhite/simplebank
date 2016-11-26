from datetime import datetime
from dateutil import parser, tz
import requests
import re
import random


class Unauthorized(Exception):
    pass


def utc_to_local(dt):
    utc = tz.tzutc()
    local = tz.tzlocal()

    dt = dt.replace(tzinfo=utc)
    dt = dt.astimezone(local)

    return dt


def milliseconds_from_date(date=None):
    local = tz.tzlocal()

    if date:
        dt = parser.parse(date)
        dt = dt.replace(tzinfo=local)
    else:
        dt = utc_to_local(datetime.utcnow())

    dt = dt - dt.dst() # Adjust for daylight savings.

    epoch = utc_to_local(datetime(1970, 1, 1))
    delta = dt - epoch

    return int((delta.total_seconds() * 1000))


def date_from_milliseconds(millis):
    dt = datetime.fromtimestamp(millis / 1000)
    return dt.strftime('%Y-%m-%d')


class Simple:

    def __init__(self, username, password):
        self._base_url = 'https://bank.simple.com'

        self._session = requests.Session()
        self._session.headers = {'User-Agent': 'Mozilla/5.0'}
        self._login(username, password)

        self._inexplicable_scale = 10000
        self._colors = {
            'teal':     '#54BFB5',
            'yellow':   '#F2DA61',
            'red':      '#E37368',
            'orange':   '#EDA55A',
            'blue':     '#4EAACC',
            'pink':     '#E091BE',
            'purple':   '#9483AB',
            'lime':     '#91D174',
            'bluegray': '#85B5BB',
            'green':    '#98D3AE'
        }

    def _login(self, username, password):
        login_url = self._base_url + '/signin'
        login_page = self._session.get(login_url)

        csrf = re.search('<meta name="_csrf" content="(.*)">', login_page.text)
        csrf = csrf.group(1)
        self._csrf = csrf

        payload = {
            'username': username,
            'password': password,
            '_csrf': csrf
        }

        attempt = self._session.post(login_url, data=payload)
        oops = 'Your username and passphrase don\'t match, please try again.'

        if oops in attempt.text:
            raise Unauthorized(oops)

    def goals(self):
        goals = self._session.get(self._base_url + '/goals/data')
        goals = goals.json()
        goals = [x for x in goals if not x['archived']]

        for goal in goals:
            for key in ['target_amount', 'contributed_amount']:
                goal[key] /= self._inexplicable_scale

            if 'next_contribution' in goal:
                contrib = goal['next_contribution']
                contrib['amount'] /= self._inexplicable_scale
                contrib['date'] = date_from_milliseconds(contrib['date'])

            for key in ['created', 'modified', 'start', 'finish']:
                goal[key] = date_from_milliseconds(goal[key])

            for key in ['amount', 'entry_ids', 'seq', 'account_ref', 'user_id', 'locked', 'archived']:
                del goal[key]

        return goals

    def create_goal(self, name, amount, finish=None, contribute=0, color=None, description='', start=None):
        color_map = self._colors
        amount *= self._inexplicable_scale
        contribute *= self._inexplicable_scale

        payload = {
            'name': name,
            'amount': amount,
            'finish': milliseconds_from_date(finish),
            'contributed_amount': contribute,
            'color': color_map[color] if color else random.choice(color_map.values()),
            'description': description,
            'start': milliseconds_from_date(start),
            'created': milliseconds_from_date(),
            '_csrf': self._csrf
        }

        self._session.post(self._base_url + '/goals', data=payload)

    def transactions(self):
        transactions = self._session.get(self._base_url + '/transactions/data')
        transactions = transactions.json()['transactions']
        return transactions

    def balance(self):
        balance = self._session.get(self._base_url + '/api/account/balances')
        balance = balance.json()

        for key in balance:
            balance[key] /= self._inexplicable_scale

        return balance