from resource_management.core.logger import Logger
from resource_management.core.resources.system import Execute
from resource_management.core.shell import call
from resource_management.libraries.functions.format import format


def setup_solr_cloud():
    import params

    code, output = call(
            format(
                    '{zk_client_prefix} -cmd get {solr_cloud_zk_directory}{clusterstate_json}'
            ),
            env={'JAVA_HOME': params.java64_home},
            timeout=60
    )

    if not ("NoNodeException" in output):
        Logger.info(
                format(
                        "ZK node {solr_cloud_zk_directory}{clusterstate_json} already exists, skipping ..."
                )
        )
        return

    Execute(
            format(
                    '{zk_client_prefix} -cmd makepath {solr_cloud_zk_directory}'
            ),
            environment={'JAVA_HOME': params.java64_home},
            ignore_failures=True,
            user=params.solr_config_user
    )
