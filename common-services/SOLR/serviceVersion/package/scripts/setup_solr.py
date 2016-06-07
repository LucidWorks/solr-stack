from resource_management.core.resources.system import Directory, File, Execute
from resource_management.libraries.functions.format import format
from resource_management.core.source import Template, InlineTemplate


def setup_solr():
    import params

    Directory([params.solr_config_dir, params.solr_config_log_dir, params.solr_config_service_log_dir,
               params.solr_config_pid_dir, params.solr_config_conf_dir, params.solr_config_data_dir],
              mode=0755,
              cd_access='a',
              owner=params.solr_config_user,
              group=params.solr_config_group,
              create_parents=True
              )

    Execute(('chmod', '-R', '777', params.solr_webapp_dir),
            sudo=True
            )

    File(format("{solr_config_bin_dir}/solr.in.sh"),
         content=InlineTemplate(params.solr_config_in_sh),
         owner=params.solr_config_user
         )

    File(format("{solr_config_conf_dir}/log4j.properties"),
         content=InlineTemplate(params.log4j_properties),
         owner=params.solr_config_user
         )

    File(format("{solr_config_data_dir}/solr.xml"),
         content=Template("solr.xml.j2"),
         owner=params.solr_config_user
         )

    # Create a home directory for solr user
    params.HdfsResource(params.solr_hdfs_home_directory,
                        type="directory",
                        action="create_on_execute",
                        owner=params.solr_config_user
                        )
