from time import sleep
from random import randint
from datadog import initialize, statsd


def init():
    options = {
        'statsd_host': 'datadog-agent',
        'statsd_port': 8125
    }
    initialize(**options)


def hitit():
    for i in range(100):
        r = randint(0, 100)
        print(f'{i}: {r}')
        statsd.histogram('app.custom.randint.hist', r, sample_rate=1, tags=['env:dev', 'app:datadoggie'])
        sleep(1)
