from resource_management.core.shell import call
from resource_management.libraries.functions.format import format
from resource_management.core.logger import Logger
from resource_management.core.resources.system import Execute
import re
import os

COLLECTION_PATTERN = "\/solr\/[a-zA-Z0-9\._-]+"
CORE_PATTERN = "{collection_path}\/core_node[0-9]+"
WRITE_LOCK_PATTERN = "{0}/data/index/write.lock "


def solr_port_validation():
    import params

    code, output = call(format('netstat -lnt | awk -v v1={solr_config_port} \'$6 == "LISTEN" && $4 ~ ":"+v1\''),
                        timeout=60)
    Logger.info(format("Solr port validation output: {output}"))

    if "LISTEN" in output:
        Logger.error(format("The port {solr_config_port} is not available"))
        return False

    return True


def solr_status_validation():
    import params

    code, output = call(format('{solr_config_bin_dir}/solr status'),
                        timeout=60)
    Logger.info(format("Solr status output: {output}"))
    pattern = re.compile("Found [0-9]+ Solr nodes:")

    if pattern.search(output):
        Logger.error("Solr is running, it cannot be started again")
        return False

    return True


def exists_collection(collection_name):
    import params

    if not params.solr_cloud_mode:
        if os.path.isdir(format("{solr_config_data_dir}/{collection_name}")):
            return True
        else:
            return False

    code, output = call(format('{zk_client_prefix} -cmd get {solr_cloud_zk_directory}/collections/{collection_name}'),
                        timeout=60
                        )

    if "NoNodeException" in output:
        return False
    else:
        return True


def get_collection_paths(hadoop_output):
    pattern = re.compile(COLLECTION_PATTERN)
    collection_paths = re.findall(pattern, hadoop_output)
    return collection_paths


def get_core_paths(hadoop_output, collection_path):
    pattern = re.compile(format(CORE_PATTERN))
    core_paths = re.findall(pattern, hadoop_output)
    return core_paths


def get_write_lock_files_solr_cloud(hadoop_prefix, collections):
    write_locks_to_delete = ''

    for collection_path in collections:
        code, output = call(format('{hadoop_prefix} -ls {collection_path}'))
        core_paths = get_core_paths(output, collection_path)

        for core_path in core_paths:
            write_locks_to_delete += WRITE_LOCK_PATTERN.format(core_path)

    return write_locks_to_delete


def get_write_lock_files_solr_standalone(collections):
    write_locks_to_delete = ''

    for collection_path in collections:
        write_locks_to_delete += WRITE_LOCK_PATTERN.format(collection_path)

    return write_locks_to_delete


def delete_write_lock_files():
    import params

    if params.security_enabled:
        kinit_if_needed = format('{kinit_path_local} {hdfs_principal_name} -kt {hdfs_user_keytab}; ')
    else:
        kinit_if_needed = ''

    hadoop_prefix = format('{kinit_if_needed}hadoop --config {hadoop_conf_dir} dfs')
    code, output = call(format('{hadoop_prefix} -ls {solr_hdfs_directory}'))
    collections = get_collection_paths(output)

    if params.solr_cloud_mode:
        write_locks_to_delete = get_write_lock_files_solr_cloud(hadoop_prefix, collections)
    else:
        write_locks_to_delete = get_write_lock_files_solr_standalone(collections)

    if len(write_locks_to_delete) > 1:
        Execute(format('{hadoop_prefix} -rm -f {write_locks_to_delete}'),
                user=params.hdfs_user
                )
