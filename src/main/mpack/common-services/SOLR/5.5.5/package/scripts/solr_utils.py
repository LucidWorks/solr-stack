import os
import re

from resource_management.core.logger import Logger
from resource_management.core.resources.system import Execute
from resource_management.core.shell import call
from resource_management.libraries.functions.format import format

COLLECTION_PATTERN = "{solr_hdfs_directory}/[a-zA-Z0-9\._-]+"
CORE_PATTERN = "{collection_path}\/core_node[0-9]+"
WRITE_LOCK_PATTERN = "{0}/data/index/write.lock "
DYNAMIC_WRITE_LOCK_PATTERN = "{0}/write.lock "
DYNAMIC_INDEX_PATTERN = "index=([^\s]*)"
HOSTNAME_VERIFIER_PATTERN = "{core_node_name}\":{{((?!\"shard|\"core_node).)*\"node_name\":\"{solr_hostname}"


def solr_port_validation():
    code, output = call(
        format('netstat -lnt | awk -v v1={solr_config_port} \'$6 == "LISTEN" && $4 ~ ":"v1\''),
        timeout=60)
    Logger.info(format("Solr port validation output: {output}"))

    if "LISTEN" in output:
        Logger.error(format("The port {solr_config_port} is not available"))
        return False

    return True


def is_solr_running():
    import params

    code, output = call(
        format('{solr_config_bin_dir}/solr status'),
        env={'JAVA_HOME': params.java64_home},
        timeout=60
    )
    Logger.info(format("Solr status output: {output}"))
    pattern_port = re.compile(format('running on port {solr_config_port}'))

    if pattern_port.search(output):
        Logger.error(format("A Solr instance is running on port {solr_config_port}"))
        return True

    return False


def exists_collection(collection_name):
    import params

    if not params.solr_cloud_mode:
        if os.path.isdir(format("{solr_config_data_dir}/{collection_name}")):
            return True
        return False

    code, output = call(format(
        '{zk_client_prefix} -cmd get {solr_cloud_zk_directory}/collections/{collection_name}'),
        env={'JAVA_HOME': params.java64_home},
        timeout=60
    )

    if "NoNodeException" in output:
        return False
    return True


def get_collection_paths(hadoop_output):
    import params
    pattern = re.compile(format(COLLECTION_PATTERN))

    collection_paths = re.findall(pattern, hadoop_output)
    return collection_paths


def get_core_paths(hadoop_output, collection_path):
    pattern = re.compile(format(CORE_PATTERN))
    core_paths = re.findall(pattern, hadoop_output)
    return core_paths


def get_write_lock_files_solr_cloud(hadoop_prefix, collections):
    import params

    write_locks_to_delete = ''

    for collection_path in collections:
        code, output = call(format('{hadoop_prefix} -ls {collection_path}'))
        core_paths = get_core_paths(output, collection_path)

        collection_name = collection_path.replace(format('{solr_hdfs_directory}/'), '')
        zk_code, zk_output = call(format(
            '{zk_client_prefix} -cmd get {solr_cloud_zk_directory}/collections/{collection_name}/state.json'),
            env={'JAVA_HOME': params.java64_home},
            timeout=60
        )
        if zk_code != 0:
            Logger.error(format('Cannot determine cores owned by [{solr_hostname}] in collection [{collection_name}] due to ZK error.'))
            continue

        for core_path in core_paths:
            core_node_name = core_path.replace(format('{collection_path}/'), '')
            pattern = re.compile(format(HOSTNAME_VERIFIER_PATTERN), re.MULTILINE|re.DOTALL)
            core_on_hostname = re.search(pattern, zk_output)
            if core_on_hostname is not None:
                # always add static index directory name to remove lock
                write_locks_to_delete += WRITE_LOCK_PATTERN.format(core_path)
                # check if index.properties file exists, then use dynamic index directory name
                code_indexprop_exists, output_indexprop_exists = call(format('{hadoop_prefix} -test -e {core_path}/data/index.properties'))
                if code_indexprop_exists == 0:
                    code_index_name, output_index_name = call(format('{hadoop_prefix} -cat {core_path}/data/index.properties | grep \'index=\''))
                    if code_index_name == 0 and len(output_index_name) > 0:
                        pattern2 = re.compile(format(DYNAMIC_INDEX_PATTERN), re.MULTILINE|re.DOTALL)
                        index_matcher = re.search(pattern2, output_index_name)
                        if index_matcher is not None and len(index_matcher.groups()) > 0:
                            index_dirname = index_matcher.group(1)
                            index_directory_path = format('{core_path}/data/{index_dirname}')
                            write_locks_to_delete += DYNAMIC_WRITE_LOCK_PATTERN.format(index_directory_path)

    return write_locks_to_delete


def get_write_lock_files_solr_standalone(collections):
    write_locks_to_delete = ''

    for collection_path in collections:
        write_locks_to_delete += WRITE_LOCK_PATTERN.format(collection_path)

    return write_locks_to_delete


def delete_write_lock_files():
    import params

    if params.security_enabled:
        kinit_if_needed = format(
            '{kinit_path_local} {hdfs_principal_name} -kt {hdfs_user_keytab}; ')
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
        Logger.info(format('For hostname: \'{solr_hostname}\' lock files \'{write_locks_to_delete}\' will be deleted.'))
        Execute(
            format('{hadoop_prefix} -rm -f {write_locks_to_delete}'),
            user=params.hdfs_user
        )
