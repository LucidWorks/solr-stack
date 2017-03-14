from resource_management.core.logger import Logger
from resource_management.core.resources.system import Execute, File
from resource_management.libraries.functions.check_process_status import check_process_status
from resource_management.libraries.functions.format import format
from resource_management.libraries.script.script import Script

from setup_solr import setup_solr
from setup_solr_cloud import setup_solr_cloud
from setup_solr_hdfs_support import setup_solr_hdfs_support
from setup_solr_kerberos_auth import setup_solr_kerberos_auth, remove_solr_kerberos_auth
from setup_solr_metrics import setup_solr_metrics_support
from setup_solr_ssl_support import setup_solr_ssl_support, remove_solr_ssl_support
from solr_utils import is_solr_running, solr_port_validation, delete_write_lock_files


class Solr(Script):
    def install(self, env):
        import params
        env.set_params(params)
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
        else:
            remove_solr_ssl_support()

        if params.security_enabled:
            setup_solr_kerberos_auth()
        else:
            remove_solr_kerberos_auth()

        if params.solr_hdfs_enable and params.solr_hdfs_delete_write_lock_files:
            delete_write_lock_files()

        if params.has_metric_collector and params.solr_enable_metrics:
            setup_solr_metrics_support()

    def start(self, env):
        import params
        env.set_params(params)
        self.configure(env)

        if not solr_port_validation():
            exit(1)

        if is_solr_running():
            Logger.info("Solr is running, it can not be started it again")
            exit(1)

        Logger.info("Starting Solr ... ")
        start_command = format('{solr_config_bin_dir}/solr start >> {solr_config_service_log_file} 2>&1')

        Execute(
            start_command,
            environment={'JAVA_HOME': params.java64_home},
            user=params.solr_config_user
        )

        if params.has_metric_collector and params.solr_enable_metrics:
            Logger.info('Starting Solr Metrics Sink.')

            if params.security_enabled:
                Execute(
                    format('{kinit_path_local} -kt {solr_metrics_kerberos_keytab} {solr_metrics_kerberos_principal}'),
                    user=params.solr_config_user
                )

            Execute(
                format('{solr_metrics_sink_bin}/solr.metrics.sh start'),
                environment={
                    'JAVA_HOME': params.java64_home,
                    'SOLR_METRICS_PID_DIR': params.solr_metrics_config_pid_dir,
                    'SOLR_METRICS_LOGS': params.solr_metrics_config_log_dir,
                    'SOLR_METRIC_CONF': params.solr_metrics_config_conf_dir
                },
                user=params.solr_config_user
            )

    def stop(self, env):
        import params
        env.set_params(params)

        if params.has_metric_collector and params.solr_enable_metrics:
            Logger.info('Stopping Solr Metrics Sink.')

            if params.security_enabled:
                Execute(
                    format('{kinit_path_local} -kt {solr_metrics_kerberos_keytab} {solr_metrics_kerberos_principal}'),
                    user=params.solr_config_user
                )

            Execute(
                format('{solr_metrics_sink_bin}/solr.metrics.sh stop'),
                environment={
                    'JAVA_HOME': params.java64_home,
                    'SOLR_METRICS_PID_DIR': params.solr_metrics_config_pid_dir,
                    'SOLR_METRICS_LOGS': params.solr_metrics_config_log_dir,
                    'SOLR_METRIC_CONF': params.solr_metrics_config_conf_dir
                },
                ignore_failures=True,
                user=params.solr_config_user
            )

        if not is_solr_running():
            Logger.info("Solr is not running, it can not be stopped it again")
            return

        Execute(
            format(
                '{solr_config_bin_dir}/solr stop -all >> {solr_config_service_log_file} 2>&1'),
            environment={'JAVA_HOME': params.java64_home},
            user=params.solr_config_user
        )

        File(
            params.solr_config_pid_file,
            action="delete"
        )

    def status(self, env):
        import status_params
        env.set_params(status_params)

        check_process_status(status_params.solr_config_pid_file)


if __name__ == "__main__":
    Solr().execute()
