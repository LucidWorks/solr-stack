def setup_solr_hdfs_support():
    import params

    # Create a home directory for solr user
    params.HdfsResource(
        params.solr_hdfs_home_directory,
        type="directory",
        action="create_on_execute",
        owner=params.solr_config_user
    )

    params.HdfsResource(params.solr_hdfs_directory,
                        type="directory",
                        action="create_on_execute",
                        owner=params.solr_config_user
                        )
