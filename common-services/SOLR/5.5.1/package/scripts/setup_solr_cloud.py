from resource_management.core.resources.system import Execute
from resource_management.libraries.functions.format import format
from resource_management.core.shell import call
from resource_management.core.logger import Logger


def setup_solr_cloud():
    import params

    code, output = call(format('{zk_client_prefix} -cmd get {solr_cloud_zk_directory}{clusterstate_json}'),
                        timeout=60
                        )

    if not ("NoNodeException" in output):
        Logger.info(format("ZK node {solr_cloud_zk_directory}{clusterstate_json} already exists, skipping ..."))
        return

    Execute(format('{zk_client_prefix} -cmd makepath {solr_cloud_zk_directory}'),
            ignore_failures=True,
            user=params.solr_config_user
            )
