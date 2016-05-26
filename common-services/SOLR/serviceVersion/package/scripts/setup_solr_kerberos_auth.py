from resource_management.core.resources.system import Execute, File
from resource_management.libraries.functions.format import format
from resource_management.core.source import Template
from resource_management.core.shell import call


def setup_solr_kerberos_auth():
    import params

    File(format("{solr_kerberos_jaas_config}"),
         content=Template("solr_server_jaas.conf.j2"),
         owner=params.solr_config_user
         )

    if not params.solr_cloud_mode:
        return

    command = format('{zk_client_prefix} -cmd put {solr_cloud_zk_directory}{security_json} ')
    command += '\'{"authentication":{"class": "org.apache.solr.security.KerberosPlugin"}}\''
    Execute(command,
            ignore_failures=True,
            user=params.solr_config_user
            )


def remove_solr_kerberos_auth():
    import params

    if not params.solr_cloud_mode:
        return

    code, output = call(format('{zk_client_prefix} -cmd get {solr_cloud_zk_directory}{security_json}'),
                        timeout=60
                        )

    if "NoNodeException" in output:
        return

    Execute(format('{zk_client_prefix} -cmd clear {solr_cloud_zk_directory}{security_json}'),
            timeout=60,
            ignore_failures=True,
            user=params.solr_config_user
            )
