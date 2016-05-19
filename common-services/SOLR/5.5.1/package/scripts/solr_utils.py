from resource_management.core.shell import call
from resource_management.libraries.functions.format import format
from resource_management.core.logger import Logger
import re


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
        return False

    zk_client_prefix = format('export JAVA_HOME={java64_home}; {cloud_scripts}/zkcli.sh -zkhost {zookeeper_hosts}')
    code, output = call(format('{zk_client_prefix} -cmd get {solr_cloud_zk_directory}/collections/{collection_name}'),
                        timeout=60
                        )

    if "NoNodeException" in output:
        return False
    else:
        return True
