from resource_management.core.resources.system import Execute
from resource_management.libraries.functions.format import format


def setup_solr_ssl_support():
    import params

    zk_client_prefix = format('export JAVA_HOME={java64_home}; {cloud_scripts}/zkcli.sh ' +
                              '-zkhost {zookeeper_hosts}{solr_cloud_zk_directory}')
    Execute(format('{zk_client_prefix} -cmd clusterprop -name urlScheme -val https'),
            ignore_failures=True,
            user=params.solr_config_user
            )
