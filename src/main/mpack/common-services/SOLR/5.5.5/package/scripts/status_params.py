#!/usr/bin/env python

from resource_management.libraries.functions.format import format
from resource_management.libraries.script.script import Script

config = Script.get_config()

map_solr_config = config['configurations']['solr-config-env']

solr_config_port = map_solr_config['solr_config_port']
solr_config_pid_dir = map_solr_config['solr_config_pid_dir']
solr_config_pid_file = format('{solr_config_pid_dir}/solr-{solr_config_port}.pid')
