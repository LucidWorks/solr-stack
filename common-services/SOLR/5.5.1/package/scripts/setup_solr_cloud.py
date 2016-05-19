from resource_management.core.resources.system import Execute
from resource_management.libraries.functions.format import format


def setup_solr_cloud():
    import params

    zk_client_prefix = format('export JAVA_HOME={java64_home}; {cloud_scripts}/zkcli.sh -zkhost {zookeeper_hosts}')
    Execute(format('{zk_client_prefix} -cmd makepath {solr_cloud_zk_directory}'),
            not_if=format("{zk_client_prefix} -cmd get {solr_cloud_zk_directory}"),
            ignore_failures=True,
            user=params.solr_config_user
            )
