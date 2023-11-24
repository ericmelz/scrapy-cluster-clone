import http.server
from random import random

from datadog import initialize, statsd
import time

# See https://www.udemy.com/course/datadog-course/learn/lecture/34893206#overview
APP_PORT = 8001

OPTIONS = {'statsd_host': 'localhost',
           'statsd_port': 8125}


class HandleRequests(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        start_time = time.time()
        wait_time = random() * 2
        print(f'{wait_time=}')
        time.sleep(wait_time)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html>"
                               "  <head>"
                               "    <title>First Application</title>"
                               "  </head>"
                               "  <body style='color: #333; margin-top: 30px;'>"
                               "    <center><h2>Welcome to Datadog-Python application.</center</h2>"
                               "  </body>"
                               "</html>",
                               "utf-8"))
        end_time = time.time()
        response_time = end_time - start_time
        statsd.histogram('app.http.request.time.histogram', response_time, sample_rate=1, tags=['env:local', 'app:datadoggie'])


if __name__ == '__main__':
    initialize(**OPTIONS)
    server = http.server.HTTPServer(('localhost', APP_PORT), HandleRequests)
    server.serve_forever()
