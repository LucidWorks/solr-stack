#!/usr/bin/env python

from resource_management.libraries.script.script import Script
from resource_management.libraries.functions import default
from resource_management.libraries.functions.format import format
from resource_management.core.logger import Logger
from resource_management.libraries.resources.hdfs_resource import HdfsResource
from resource_management.libraries.functions.get_not_managed_resources import get_not_managed_resources
from resource_management.libraries.functions import conf_select
from resource_management.libraries.functions import stack_select

import status_params
import functools

def build_zookeeper_hosts():
    zookeeper_hosts_length = len(zookeeper_hosts_list)
    response = ""
    for i, val in enumerate(zookeeper_hosts_list):
        response += val + ":" + zk_client_port
        if (i + 1) < zookeeper_hosts_length:
            response += ","
    return response

config = Script.get_config()

java64_home = config['hostLevelParams']['java_home']
zk_client_port = str(default('/configurations/zoo.cfg/clientPort', None))
zookeeper_hosts_list = config['clusterHostInfo']['zookeeper_hosts']
zookeeper_hosts = build_zookeeper_hosts()

map_solr_config = config['configurations']['solr-config-env']
solr_config_user = map_solr_config['solr.config.user']
solr_config_group = map_solr_config['solr.config.group']
solr_config_port = status_params.solr_config_port
solr_config_memory = map_solr_config['solr.config.memory']
solr_config_log_dir = map_solr_config['solr.config.log.dir']
solr_config_service_log_dir = map_solr_config['solr.config.service.log.dir']
solr_config_service_log_file = format("{solr_config_service_log_dir}/solr-service.log")
solr_config_conf_dir = map_solr_config['solr.config.conf.dir']
solr_config_data_dir = map_solr_config['solr.config.data.dir']

solr_config_dir = '/usr/lib/ambari-logsearch-solr'
solr_config_bin_dir = solr_config_dir + '/bin'
solr_config_pid_dir = status_params.solr_config_pid_dir
solr_config_pid_file = status_params.solr_config_pid_file

# solr cloud
cloud_scripts = format('{solr_config_dir}/server/scripts/cloud-scripts')
map_solr_cloud = config['configurations']['solr-cloud']
solr_cloud_mode = map_solr_cloud['solr.cloud.enable']
solr_cloud_zk_directory = map_solr_cloud['solr.cloud.zk.directory']

# collection sample
map_example_collection = config['configurations']['example-collection']
solr_collection_sample_create = bool(map_example_collection['solr.collection.sample.create'])
solr_collection_name = map_example_collection['solr.collection.sample.name']
solr_collection_config_dir = map_example_collection['solr.collection.sample.config.directory']
solr_collection_shards = str(map_example_collection['solr.collection.sample.shards'])
solr_collection_replicas = str(map_example_collection['solr.collection.sample.replicas'])

# HDFS
map_solr_hdfs = config['configurations']['solr-hdfs']
solr_hdfs_enable = bool(map_solr_hdfs['solr.hdfs.enable'])
solr_hdfs_directory = map_solr_hdfs['solr.hdfs.directory']
hadoop_bin_dir = stack_select.get_hadoop_dir("bin")
hadoop_conf_dir = conf_select.get_hadoop_conf_dir()
hdfs_user = config['configurations']['hadoop-env']['hdfs_user']
hdfs_site = config['configurations']['hdfs-site']
hdfs_user_keytab = config['configurations']['hadoop-env']['hdfs_user_keytab']
default_fs = config['configurations']['core-site']['fs.defaultFS']
dfs_type = default("/commandParams/dfs_type", "")

HdfsResource = functools.partial(
    HdfsResource,
    user=hdfs_user,
    hdfs_resource_ignore_file="/var/lib/ambari-agent/data/.hdfs_resource_ignore",
    security_enabled=False,
    keytab=hdfs_user_keytab,
    hadoop_bin_dir=hadoop_bin_dir,
    hadoop_conf_dir=hadoop_conf_dir,
    hdfs_site=hdfs_site,
    default_fs=default_fs,
    immutable_paths=get_not_managed_resources(),
    dfs_type=dfs_type
)

# solr ssl
map_solr_ssl = config['configurations']['solr-ssl']
solr_ssl_enable = bool(map_solr_ssl['solr.ssl.enable'])
solr_ssl_prefix = "#" if not solr_ssl_enable else ""
solr_ssl_key_store = map_solr_ssl['solr.ssl.key.store']
solr_ssl_key_store_password = map_solr_ssl['solr.ssl.key.store.password']
solr_ssl_trust_store = map_solr_ssl['solr.ssl.trust.store']
solr_ssl_trust_store_password = map_solr_ssl['solr.ssl.trust.store.password']
solr_ssl_need_client_auth = map_solr_ssl['solr.ssl.need.client.auth']
solr_ssl_want_client_auth = map_solr_ssl['solr.ssl.want.client.auth']
