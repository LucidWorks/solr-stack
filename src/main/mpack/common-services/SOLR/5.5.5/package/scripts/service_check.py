#!/usr/bin/env python

import os

from resource_management.core.logger import Logger
from resource_management.core.resources.system import Execute
from resource_management.libraries.functions.format import format
from resource_management.libraries.script import Script

from solr_utils import exists_collection


class ServiceCheck(Script):
    def service_check(self, env):
        import params
        env.set_params(params)

        if not os.path.isfile(params.solr_config_pid_file):
            Logger.error(format("PID file {solr_config_pid_file} does not exist"))
            exit(1)

        if not params.solr_collection_sample_create:
            Logger.info("Create sample collection unchecked, skipping ...")
            return

        if exists_collection(params.solr_collection_name):
            Logger.warning(format("Collection {solr_collection_name} already exists, skipping ..."))
            return

        if not params.solr_cloud_mode:
            Execute(
                    format(
                            '{solr_config_bin_dir}/solr create_core -c {solr_collection_name}' +
                            ' -d {solr_collection_config_dir} -p {solr_config_port} >> {solr_config_service_log_file} 2>&1'
                    ),
                    environment={'JAVA_HOME': params.java64_home},
                    user=params.solr_config_user
            )
        else:
            Execute(format(
                    '{solr_config_bin_dir}/solr create_collection -c {solr_collection_name}' +
                    ' -d {solr_collection_config_dir} -p {solr_config_port}' +
                    ' -s {solr_collection_shards} -rf {solr_collection_replicas}' +
                    ' >> {solr_config_service_log_file} 2>&1'),
                    environment={'JAVA_HOME': params.java64_home},
                    user=params.solr_config_user
            )


if __name__ == "__main__":
    ServiceCheck().execute()
