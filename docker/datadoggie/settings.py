import os

STATSD_PORT = int(os.getenv('DATADOG_AGENT_SERVICE_PORT_DOGSTATSDPORT', 8125))
STATSD_HOST = 'datadog-agent' if os.getenv('DATADOG_AGENT_SERVICE_PORT_DOGSTATSDPORT') else 'localhost'
