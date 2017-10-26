from resource_management.core.logger import Logger
from resource_management.core.resources.system import Execute, File
from resource_management.core.shell import call
from resource_management.core.source import Template
from resource_management.libraries.functions.format import format


def setup_solr_kerberos_auth():
    import params

    File(format("{solr_kerberos_jaas_config}"),
         content=Template("solr_server_jaas.conf.j2"),
         owner=params.solr_config_user
         )

    if _has_security_json():
        Logger.info("Solr Security Json was found, it will not be overridden")
        return

    command = format('{zk_client_prefix} -cmd put {solr_cloud_zk_directory}{security_json} ')
    command += format('\'{solr_security_json}\'')
    Execute(command,
            environment={'JAVA_HOME': params.java64_home},
            ignore_failures=True,
            user=params.solr_config_user
            )


def remove_solr_kerberos_auth():
    import params

    if not _has_security_json():
        Logger.debug(format("Solr Security Json not found {solr_cloud_zk_directory}{security_json}"))
        return

    Execute(format('{zk_client_prefix} -cmd clear {solr_cloud_zk_directory}{security_json}'),
            environment={'JAVA_HOME': params.java64_home},
            timeout=60,
            ignore_failures=True,
            user=params.solr_config_user
            )


def _has_security_json():
    import params

    if not params.solr_cloud_mode:
        return False

    code, output = call(
        format('{zk_client_prefix} -cmd get {solr_cloud_zk_directory}{security_json}'),
        env={'JAVA_HOME': params.java64_home},
        timeout=60
    )

    if "{}" == output:
        return False
    return "NoNodeException" not in output
