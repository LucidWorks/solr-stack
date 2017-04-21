from resource_management.core.resources.system import Directory, File
from resource_management.core.source import InlineTemplate, Template
from resource_management.libraries.functions.format import format


def setup_solr_metrics_support():
    import params

    Directory(
            [
                params.solr_metrics_config_conf_dir,
                params.solr_metrics_config_pid_dir,
                params.solr_metrics_config_log_dir
            ],
            mode=0755,
            cd_access='a',
            owner=params.solr_config_user,
            group=params.solr_config_group,
            create_parents=True
    )

    File(
            format("{solr_metrics_config_conf_dir}/solr.metrics.properties"),
            content=InlineTemplate(params.solr_metrics_properties),
            owner=params.solr_config_user
    )

    File(
            format("{solr_metrics_config_conf_dir}/log4j2.xml"),
            content=Template("log4j2.xml"),
            owner=params.solr_config_user
    )

    if params.security_enabled:
        File(
            format("{solr_metrics_kerberos_jaas_config}"),
            content=Template("solr_metrics_jaas.conf.j2"),
            owner=params.solr_config_user
        )

