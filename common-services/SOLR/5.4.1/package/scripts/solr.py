from resource_management.core.resources.system import Execute, File
from resource_management.libraries.functions.format import format
from resource_management.libraries.functions.check_process_status import check_process_status
from resource_management.libraries.script.script import Script
from resource_management.core.logger import Logger
from setup_solr import setup_solr
from setup_solr_cloud import setup_solr_cloud
from setup_solr_hdfs_support import setup_solr_hdfs_support
from setup_solr_ssl_support import setup_solr_ssl_support


class Solr(Script):
    def install(self, env):
        import params
        env.set_params(params)
        Logger.info("installing solr")
        self.install_packages(env)

    def configure(self, env):
        import params
        env.set_params(params)
        setup_solr()

        if params.solr_cloud_mode:
            setup_solr_cloud()

        if params.solr_hdfs_enable:
            setup_solr_hdfs_support()

        if params.solr_ssl_enable:
            setup_solr_ssl_support()

    def start(self, env):
        import params
        env.set_params(params)
        self.configure(env)

        start_command = format('{solr_config_bin_dir}/solr start')

        if params.solr_cloud_mode:
            start_command += format(' -cloud -z {zookeeper_hosts}{solr_cloud_zk_directory}')

        if params.solr_hdfs_enable:
            start_command += format(' -Dsolr.directoryFactory=HdfsDirectoryFactory -Dsolr.lock.type=hdfs')
            start_command += format(' -Dsolr.hdfs.home={default_fs}{solr_hdfs_directory}')

        start_command += format(' -p {solr_config_port} -m {solr_config_memory} >> {solr_config_service_log_file} 2>&1')

        Execute(
            start_command,
            user=params.solr_config_user
        )

    def stop(self, env):
        import params
        env.set_params(params)

        Execute(
            format('{solr_config_bin_dir}/solr stop -p {solr_config_port}'),
            user=params.solr_config_user,
            only_if=format("test -f {solr_config_pid_file}")
        )

        File(params.solr_config_pid_file,
             action="delete"
             )

    def status(self, env):
        import status_params
        env.set_params(status_params)

        check_process_status(status_params.solr_config_pid_file)

if __name__ == "__main__":
    Solr().execute()
