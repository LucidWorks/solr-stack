def setup_solr_hdfs_support():
    import params

    params.HdfsResource(params.solr_hdfs_directory,
                        type="directory",
                        action="create_on_execute",
                        owner=params.solr_config_user
                        )
