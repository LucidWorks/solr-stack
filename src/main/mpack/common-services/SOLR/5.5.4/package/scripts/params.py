#!/usr/bin/env python

import functools

from ambari_commons.ambari_metrics_helper import select_metric_collector_hosts_from_hostnames
from resource_management.libraries.functions import conf_select
from resource_management.libraries.functions import default
from resource_management.libraries.functions import get_kinit_path
from resource_management.libraries.functions import stack_select
from resource_management.libraries.functions.format import format
from resource_management.libraries.functions.get_not_managed_resources import \
    get_not_managed_resources
from resource_management.libraries.resources.hdfs_resource import HdfsResource
from resource_management.libraries.script.script import Script

import status_params


def build_zookeeper_hosts():
    zookeeper_hosts_length = len(zookeeper_hosts_list)
    response = ''
    for i, val in enumerate(zookeeper_hosts_list):
        response += val + ':' + zk_client_port
        if (i + 1) < zookeeper_hosts_length:
            response += ','
    return response


config = Script.get_config()

java64_home = config['hostLevelParams']['java_home']
hostname = config['hostname']
zk_client_port = str(default('/configurations/zoo.cfg/clientPort', None))
zookeeper_hosts_list = config['clusterHostInfo']['zookeeper_hosts']
zookeeper_hosts = build_zookeeper_hosts()

map_solr_config = config['configurations']['solr-config-env']
solr_config_user = map_solr_config['solr_config_user']
solr_hdfs_home_directory = format('/user/{solr_config_user}')
solr_config_group = map_solr_config['solr_config_group']
solr_config_port = status_params.solr_config_port
solr_config_memory = map_solr_config['solr_config_memory']
solr_config_log_dir = map_solr_config['solr_config_log_dir']
solr_config_service_log_dir = map_solr_config['solr_config_service_log_dir']
solr_config_service_log_file = format('{solr_config_service_log_dir}/solr-service.log')
solr_config_conf_dir = map_solr_config['solr_config_conf_dir']
solr_config_data_dir = map_solr_config['solr_config_data_dir']
solr_config_in_sh = map_solr_config['solr_in_sh_template']
solr_hostname = hostname

log4j_properties = config['configurations']['solr-log4j']['content']

solr_package_dir = '/opt/lucidworks-hdpsearch'
solr_config_dir = format('{solr_package_dir}/solr')
solr_config_bin_dir = format('{solr_config_dir}/bin')
solr_config_pid_dir = status_params.solr_config_pid_dir
solr_config_pid_file = status_params.solr_config_pid_file
solr_webapp_dir = format('{solr_config_dir}/server/solr-webapp')

# solr cloud
cloud_scripts = format('{solr_config_dir}/server/scripts/cloud-scripts')
map_solr_cloud = config['configurations']['solr-cloud']
solr_cloud_mode = map_solr_cloud['solr_cloud_enable']
solr_cloud_mode_prefix = '#' if not solr_cloud_mode else ''
solr_not_cloud_mode_prefix = '#' if solr_cloud_mode else ''
solr_cloud_zk_directory = map_solr_cloud['solr_cloud_zk_directory']
zk_client_prefix = format('{cloud_scripts}/zkcli.sh -zkhost {zookeeper_hosts}')
clusterprops_json = '/clusterprops.json'
clusterstate_json = '/clusterstate.json'

# solr collection sample
map_example_collection = config['configurations']['example-collection']
solr_collection_sample_create = bool(map_example_collection['solr_collection_sample_create'])
solr_collection_name = map_example_collection['solr_collection_sample_name']
solr_collection_config_dir = map_example_collection['solr_collection_sample_config_directory']
solr_collection_shards = str(map_example_collection['solr_collection_sample_shards'])
solr_collection_replicas = str(map_example_collection['solr_collection_sample_replicas'])

# solr + HDFS
map_solr_hdfs = config['configurations']['solr-hdfs']
solr_hdfs_enable = bool(map_solr_hdfs['solr_hdfs_enable'])
solr_hdfs_prefix = '#' if not solr_hdfs_enable else ''
solr_hdfs_directory = map_solr_hdfs['solr_hdfs_directory']
hadoop_bin_dir = stack_select.get_hadoop_dir('bin')
hadoop_conf_dir = conf_select.get_hadoop_conf_dir()
hdfs_user = config['configurations']['hadoop-env']['hdfs_user']
hdfs_site = config['configurations']['hdfs-site']
hdfs_user_keytab = config['configurations']['hadoop-env']['hdfs_user_keytab']
default_fs = config['configurations']['core-site']['fs.defaultFS']
dfs_type = default('/commandParams/dfs_type', '')
security_enabled = config['configurations']['cluster-env']['security_enabled']
kinit_path_local = get_kinit_path(
        default('/configurations/kerberos-env/executable_search_paths', None))
hdfs_principal_name = config['configurations']['hadoop-env']['hdfs_principal_name']
solr_hdfs_delete_write_lock_files = bool(map_solr_hdfs['solr_hdfs_delete_write_lock_files'])

HdfsResource = functools.partial(
        HdfsResource,
        user=hdfs_user,
        hdfs_resource_ignore_file='/var/lib/ambari-agent/data/.hdfs_resource_ignore',
        security_enabled=security_enabled,
        keytab=hdfs_user_keytab,
        kinit_path_local=kinit_path_local,
        hadoop_bin_dir=hadoop_bin_dir,
        hadoop_conf_dir=hadoop_conf_dir,
        principal_name=hdfs_principal_name,
        hdfs_site=hdfs_site,
        default_fs=default_fs,
        immutable_paths=get_not_managed_resources(),
        dfs_type=dfs_type
)

# solr + SSL
map_solr_ssl = config['configurations']['solr-ssl']
solr_ssl_enable = bool(map_solr_ssl['solr_ssl_enable'])
solr_ssl_prefix = '#' if not solr_ssl_enable else ''
solr_ssl_key_store = map_solr_ssl['solr_ssl_key_store']
solr_ssl_key_store_password = map_solr_ssl['solr_ssl_key_store_password']
solr_ssl_trust_store = map_solr_ssl['solr_ssl_trust_store']
solr_ssl_trust_store_password = map_solr_ssl['solr_ssl_trust_store_password']
solr_ssl_need_client_auth = map_solr_ssl['solr_ssl_need_client_auth']
solr_ssl_want_client_auth = map_solr_ssl['solr_ssl_want_client_auth']
solr_protocol = 'https' if solr_ssl_enable else 'http'

# solr + kerberos auth
solr_kerberos_prefix = '#' if not security_enabled else ''
solr_kerberos_jaas_config = format('{solr_config_conf_dir}/solr_server_jaas.conf')
solr_kerberos_cookie_domain = hostname
solr_kerberos_keytab = map_solr_config.get('solr_keytab_path', '')
solr_kerberos_principal = map_solr_config.get('solr_principal_name', '')
solr_spnego_keytab = map_solr_config.get('solr_spnego_keytab_path', '')
solr_spnego_principal = map_solr_config.get('solr_spnego_principal_name', '')
solr_metrics_kerberos_jaas_config = format('{solr_config_conf_dir}/solr_metrics_jaas.conf')
solr_metrics_kerberos_keytab = map_solr_config.get('solr_metrics_keytab_path', '')
solr_metrics_kerberos_principal = map_solr_config.get('solr_metrics_principal_name', '')
security_json = '/security.json'
map_solr_kerberos = config['configurations']['solr-security']
solr_security_json = map_solr_kerberos.get('solr_security_json', '')

if security_enabled:
    solr_kerberos_principal = solr_kerberos_principal.replace('_HOST', hostname)
    solr_spnego_principal = solr_spnego_principal.replace('_HOST', hostname)
    solr_metrics_kerberos_principal = solr_metrics_kerberos_principal.replace('_HOST', hostname)

# Metrics
solr_metrics_sink_dir = format('{solr_package_dir}/metrics')
solr_metrics_sink_bin = format('{solr_metrics_sink_dir}/bin')

# Metrics collector
ams_collector_hosts = ",".join(default("/clusterHostInfo/metrics_collector_hosts", []))
has_metric_collector = not len(ams_collector_hosts) == 0
if has_metric_collector:
    if 'cluster-env' in config['configurations'] and \
                    'metrics_collector_vip_host' in config['configurations']['cluster-env']:
        metric_collector_host = config['configurations']['cluster-env'][
            'metrics_collector_vip_host']
    else:
        metric_collector_host = select_metric_collector_hosts_from_hostnames(ams_collector_hosts)
    if 'cluster-env' in config['configurations'] and \
                    'metrics_collector_vip_port' in config['configurations']['cluster-env']:
        metric_collector_port = config['configurations']['cluster-env'][
            'metrics_collector_vip_port']
    else:
        metric_collector_web_address = default(
                "/configurations/ams-site/timeline.metrics.service.webapp.address", "0.0.0.0:6188")
        if metric_collector_web_address.find(':') != -1:
            metric_collector_port = metric_collector_web_address.split(':')[1]
        else:
            metric_collector_port = '6188'
    if default("/configurations/ams-site/timeline.metrics.service.http.policy",
               "HTTP_ONLY") == "HTTPS_ONLY":
        metric_collector_protocol = 'https'
    else:
        metric_collector_protocol = 'http'
    metric_truststore_path = default(
            "/configurations/ams-ssl-client/ssl.client.truststore.location", "")
    metric_truststore_type = default("/configurations/ams-ssl-client/ssl.client.truststore.type",
                                     "")
    metric_truststore_password = default(
            "/configurations/ams-ssl-client/ssl.client.truststore.password", "")

solr_metrics = config['configurations']['solr-metrics']
solr_enable_metrics = bool(solr_metrics.get('solr_enable_metrics', False))

solr_metrics_delay = solr_metrics['solr_metrics_delay']
solr_metrics_period = solr_metrics['solr_metrics_period']
solr_core_stats = bool(solr_metrics['solr_core_stats'])
solr_cache_stats = bool(solr_metrics['solr_cache_stats'])
solr_updatehandler_stats = bool(solr_metrics['solr_updatehandler_stats'])
solr_queryhandler_stats = bool(solr_metrics['solr_queryhandler_stats'])
solr_system_stats = bool(solr_metrics['solr_system_stats'])
solr_status_stats = bool(solr_metrics.get('solr_status_stats', False))

solr_metrics_config_conf_dir = solr_metrics['solr_metrics_config_conf_dir']
solr_metrics_config_pid_dir = solr_metrics['solr_metrics_config_pid_dir']
solr_metrics_config_log_dir = solr_metrics['solr_metrics_config_log_dir']

solr_metrics_properties = solr_metrics['solr_metrics_properties']
