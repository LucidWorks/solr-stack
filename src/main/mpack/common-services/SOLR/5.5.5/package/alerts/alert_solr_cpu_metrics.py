import urllib
import httplib
import json
import time

from ambari_commons.ambari_metrics_helper import select_metric_collector_hosts_from_hostnames
from ambari_commons.ambari_metrics_helper import load_properties_from_file

RESULT_STATE_OK = 'OK'
RESULT_STATE_CRITICAL = 'CRITICAL'
RESULT_STATE_WARNING = 'WARNING'
RESULT_STATE_UNKNOWN = 'UNKNOWN'
RESULT_STATE_SKIPPED = 'SKIPPED'

KERBEROS_KEYTAB = '{{hdfs-site/dfs.web.authentication.kerberos.keytab}}'
KERBEROS_PRINCIPAL = '{{hdfs-site/dfs.web.authentication.kerberos.principal}}'
SECURITY_ENABLED_KEY = '{{cluster-env/security_enabled}}'
SMOKEUSER_KEY = '{{cluster-env/smokeuser}}'

METRICS_COLLECTOR_WEBAPP_ADDRESS_KEY = '{{ams-site/timeline.metrics.service.webapp.address}}'
METRICS_COLLECTOR_VIP_HOST_KEY = '{{cluster-env/metrics_collector_vip_host}}'
METRICS_COLLECTOR_VIP_PORT_KEY = '{{cluster-env/metrics_collector_vip_port}}'

SOLR_METRICS_CONF_DIR = '{{solr-metrics/solr_metrics_config_conf_dir}}'
SOLR_METRICS_PERIOD = '{{solr-metrics/solr_metrics_period}}'

AMS_METRICS_GET_URL = "/ws/v1/timeline/metrics?%s"

CONNECTION_TIMEOUT_DEFAULT = 5.0
CONNECTION_TIMEOUT_KEY = "connection.timeout"

METRIC_NAMES_DEFAULT = "solr.admin.info.system.processCpuLoad"
METRIC_NAMES_KEY = "metric.names"

APP_ID_DEFAULT = "solr-host-app"
APP_ID_KEY = "app.id"

WARNING_THRESHOLD_DEFAULT = 50
WARNING_THRESHOLD_KEY = "metric.solr.cpu.warning.threshold"

CRITICAL_THRESHOLD_DEFAULT = 75
CRITICAL_THRESHOLD_KEY = "metric.solr.cpu.critical.threshold"


def get_tokens():
    """
    Returns a tuple of tokens in the format {{site/property}} that will be used
    to build the dictionary passed into execute
    """
    return (SMOKEUSER_KEY, KERBEROS_KEYTAB, KERBEROS_PRINCIPAL, SECURITY_ENABLED_KEY, METRICS_COLLECTOR_VIP_HOST_KEY,
            METRICS_COLLECTOR_VIP_PORT_KEY, METRICS_COLLECTOR_WEBAPP_ADDRESS_KEY, SOLR_METRICS_CONF_DIR,
            SOLR_METRICS_PERIOD)


def execute(configurations={}, parameters={}, host_name=None):
    collector_host, collector_port = get_collector_config(configurations)

    if collector_host is None or collector_port is None:
        return RESULT_STATE_UNKNOWN, ['Undefined collector host: {0} or collector port {1}'.format(collector_host,
                                                                                                   collector_port)]

    metric_name = METRIC_NAMES_DEFAULT
    if METRIC_NAMES_KEY in parameters:
        metric_name = parameters[METRIC_NAMES_KEY]

    app_id = APP_ID_DEFAULT
    if APP_ID_KEY in parameters:
        app_id = parameters[APP_ID_KEY]

    connection_timeout = CONNECTION_TIMEOUT_DEFAULT
    if CONNECTION_TIMEOUT_KEY in parameters:
        connection_timeout = parameters[CONNECTION_TIMEOUT_KEY]

    warning_threshold = WARNING_THRESHOLD_DEFAULT
    if WARNING_THRESHOLD_KEY in parameters:
        warning_threshold = parameters[WARNING_THRESHOLD_KEY]

    critical_threshold = CRITICAL_THRESHOLD_DEFAULT
    if CRITICAL_THRESHOLD_KEY in parameters:
        critical_threshold = parameters[CRITICAL_THRESHOLD_KEY]

    current_time = int(time.time()) * 1000
    metric_period = int(configurations[SOLR_METRICS_PERIOD])
    start_time = current_time - (metric_period * 2)

    get_metrics_parameters = {
        "metricNames": metric_name,
        "appId": app_id,
        "hostname": host_name,
        "startTime": start_time,
        "endTime": current_time,
        "grouped": "true",
    }

    encoded_get_metrics_parameters = urllib.urlencode(get_metrics_parameters)

    try:
        conn = httplib.HTTPConnection(collector_host, int(collector_port), timeout=connection_timeout)
        conn.request("GET", AMS_METRICS_GET_URL % encoded_get_metrics_parameters)
        response = conn.getresponse()
        data = response.read()
        conn.close()
    except Exception:
        return RESULT_STATE_UNKNOWN, ["Unable to retrieve metrics from the Ambari Metrics service."]

    data_json = json.loads(data)
    cpu_load_value = -1

    for metrics_data in data_json["metrics"]:
        if "solr.admin.info.system.processCpuLoad" in metrics_data["metricname"]:
            metrics = metrics_data["metrics"].values()
            if len(metrics) > 0:
                cpu_load_value = metrics[0] * 100
                break

    if int(cpu_load_value) == -1:
        return RESULT_STATE_UNKNOWN, ["There is not enough data"]

    response = 'CPU load {0:.2f} %'.format(cpu_load_value)

    if int(cpu_load_value) >= warning_threshold and int(cpu_load_value) < critical_threshold:
        return RESULT_STATE_WARNING, [response]

    if cpu_load_value >= critical_threshold:
        return RESULT_STATE_CRITICAL, [response]

    return RESULT_STATE_OK, [response]


def get_collector_config(configurations):
    solr_metrics_props = "{0}/{1}".format(configurations[SOLR_METRICS_CONF_DIR], "solr.metrics.properties")
    props = load_properties_from_file(solr_metrics_props)
    collector_hosts = props.get("collector.hosts")

    if METRICS_COLLECTOR_VIP_HOST_KEY in configurations and METRICS_COLLECTOR_VIP_PORT_KEY in configurations:
        collector_host = configurations[METRICS_COLLECTOR_VIP_HOST_KEY]
        collector_port = int(configurations[METRICS_COLLECTOR_VIP_PORT_KEY])
    else:
        collector_webapp_address = configurations[METRICS_COLLECTOR_WEBAPP_ADDRESS_KEY].split(":")
        if valid_collector_webapp_address(collector_webapp_address):
            collector_host = select_metric_collector_hosts_from_hostnames(collector_hosts)
            collector_port = int(collector_webapp_address[1])
        else:
            return None, None
    return collector_host, collector_port


def valid_collector_webapp_address(webapp_address):
    if len(webapp_address) == 2 and webapp_address[0] != '127.0.0.1' and webapp_address[1].isdigit():
        return True
    return False
