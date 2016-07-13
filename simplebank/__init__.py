from datetime import datetime
from dateutil import parser, tz
import requests
import re
import random


class Unauthorized(Exception):
    pass


def milliseconds_from_date(date=None):
    utc = tz.tzutc()
    local = tz.tzlocal()

    if date:
        dt = parser.parse(date)
        dt = dt.replace(tzinfo=local)
    else:
        dt = datetime.utcnow()
        dt = dt.replace(tzinfo=utc)
        dt = dt.astimezone(local)

    dt = dt - dt.dst()

    epoch = datetime(1970, 1, 1)
    epoch = epoch.replace(tzinfo=utc)
    epoch = epoch.astimezone(local)

    delta = dt - epoch
    return int((delta.total_seconds() * 1000))


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
            goal['target_amount'] /= self._inexplicable_scale
            goal['contributed_amount'] /= self._inexplicable_scale

            if 'next_contribution' in goal:
                goal['next_contribution']['amount'] /= self._inexplicable_scale

            del goal['amount']
            del goal['entry_ids']
            del goal['seq']
            del goal['account_ref']
            del goal['user_id']
            del goal['locked']
            del goal['archived']

        return(goals)

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
        return(transactions)
