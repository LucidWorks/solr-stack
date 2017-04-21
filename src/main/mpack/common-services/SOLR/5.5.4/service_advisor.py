import os
import imp
import traceback
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STACKS_DIR = os.path.join(SCRIPT_DIR, '../../../stacks/')
PARENT_FILE = os.path.abspath(os.path.join(STACKS_DIR, 'service_advisor.py'))

try:
    with open(PARENT_FILE, 'rb') as fp:
        service_advisor = imp.load_module('service_advisor', fp, PARENT_FILE, ('.py', 'rb', imp.PY_SOURCE))
except Exception as e:
    traceback.print_exc()
    print "Failed to load parent"

SOLR_CONFIG_ENV = "solr-config-env"
SOLR_CLOUD = "solr-cloud"
SOLR_HDFS = "solr-hdfs"
SOLR_SSL = "solr-ssl"
EXAMPLE_COLLECTION = "example-collection"
PROPERTIES = "properties"


class SOLR554ServiceAdvisor(service_advisor.ServiceAdvisor):
    def is_not_null_or_empty(self, property_value):
        if property_value is None:
            return self.getErrorItem("Value cannot be null or empty")
        return None

    def is_absolute_path(self, property_value):
        status = self.is_not_null_or_empty(property_value)
        if status is not None:
            return status

        if not os.path.isabs(property_value):
            return self.getErrorItem("An absolute path must be used")
        return None

    def to_number(self, property_value):
        try:
            return int(re.sub("\D", "", property_value))
        except ValueError:
            return None

    def is_number(self, property_value):
        status = self.is_not_null_or_empty(property_value)
        if status is not None:
            return status

        value = self.to_number(property_value)
        if value is None:
            return self.getErrorItem("Value should be an integer")
        return None

    def is_boolean(self, property_value):
        status = self.is_not_null_or_empty(property_value)
        if status is not None:
            return status

        value = str(property_value).lower()

        if value == "true" or value == "false":
            return None
        return self.getErrorItem("Value should be true or false")

    def is_memory_format(self, property_value):
        status = self.is_not_null_or_empty(property_value)
        if status is not None:
            return status

        string_pattern = "^[0-9]+(m|g)$"
        pattern = re.compile(string_pattern)

        if pattern.match(property_value):
            return None
        return self.getErrorItem("Invalid JMX value, valid pattern: {0}".format(string_pattern))

    def is_valid_path(self, property_value):
        status = self.is_not_null_or_empty(property_value)
        if status is not None:
            return status

        if not property_value.startswith('/'):
            return self.getErrorItem("Path must start with '/'")

        if property_value.endswith('/'):
            return self.getErrorItem("Path cannot end with '/'")

        return None

    def validator_entry(self, config_name, validator, properties):
        return {
            "config-name": config_name,
            "item": validator(properties[config_name])
        }

    def validate_solr_configuration(self):
        items = [
            self.validator_entry('solr_config_port', self.is_number, self.solr_config_properties),
            self.validator_entry('solr_config_memory', self.is_memory_format, self.solr_config_properties),
            self.validator_entry('solr_config_conf_dir', self.is_absolute_path, self.solr_config_properties),
            self.validator_entry('solr_config_data_dir', self.is_absolute_path, self.solr_config_properties),
            self.validator_entry('solr_config_pid_dir', self.is_absolute_path, self.solr_config_properties),
            self.validator_entry('solr_config_log_dir', self.is_absolute_path, self.solr_config_properties),
            self.validator_entry('solr_config_service_log_dir', self.is_absolute_path, self.solr_config_properties)
        ]
        return self.stackAdvisor.toConfigurationValidationProblems(items, SOLR_CONFIG_ENV)

    def validate_solr_cloud_configuration(self):
        items = [] if "false" in self.solr_cloud_properties["solr_cloud_enable"] else \
            [
                self.validator_entry('solr_cloud_enable', self.is_boolean, self.solr_cloud_properties),
                self.validator_entry('solr_cloud_zk_directory', self.is_valid_path, self.solr_cloud_properties),
            ]
        return self.stackAdvisor.toConfigurationValidationProblems(items, SOLR_CLOUD)

    def validate_solr_hdfs_configuration(self):
        items = [] if "false" in self.solr_hdfs_properties["solr_hdfs_enable"] else \
            [
                self.validator_entry('solr_hdfs_enable', self.is_boolean, self.solr_hdfs_properties),
                self.validator_entry('solr_hdfs_directory', self.is_valid_path, self.solr_hdfs_properties),
            ]
        return self.stackAdvisor.toConfigurationValidationProblems(items, SOLR_HDFS)

    def validate_solr_ssl_configuration(self):
        items = [] if "false" in self.solr_ssl_properties["solr_ssl_enable"] else \
            [
                self.validator_entry('solr_ssl_enable', self.is_boolean, self.solr_ssl_properties),
                self.validator_entry('solr_ssl_key_store', self.is_absolute_path, self.solr_ssl_properties),
                self.validator_entry('solr_ssl_key_store_password', self.is_not_null_or_empty,
                                     self.solr_ssl_properties),
                self.validator_entry('solr_ssl_trust_store', self.is_absolute_path, self.solr_ssl_properties),
                self.validator_entry('solr_ssl_trust_store_password', self.is_not_null_or_empty,
                                     self.solr_ssl_properties),
                self.validator_entry('solr_ssl_need_client_auth', self.is_boolean, self.solr_ssl_properties),
                self.validator_entry('solr_ssl_want_client_auth', self.is_boolean, self.solr_ssl_properties)
            ]
        return self.stackAdvisor.toConfigurationValidationProblems(items, SOLR_SSL)

    def validate_example_collection_configuration(self):
        items = [] if "false" in self.example_collection_properties["solr_collection_sample_create"] else \
            [
                self.validator_entry('solr_collection_sample_create', self.is_boolean,
                                     self.example_collection_properties),
                self.validator_entry('solr_collection_sample_name', self.is_not_null_or_empty,
                                     self.example_collection_properties),
                self.validator_entry('solr_collection_sample_config_directory', self.is_not_null_or_empty,
                                     self.example_collection_properties),
                self.validator_entry('solr_collection_sample_shards', self.is_number,
                                     self.example_collection_properties),
                self.validator_entry('solr_collection_sample_replicas', self.is_number,
                                     self.example_collection_properties)
            ]
        return self.stackAdvisor.toConfigurationValidationProblems(items, EXAMPLE_COLLECTION)

    def getConfigurationsValidationItems(self, stackAdvisor, configurations, recommended_defaults, services, hosts):
        if not SOLR_CONFIG_ENV in configurations:
            return []

        self.stackAdvisor = stackAdvisor
        self.solr_config_properties = configurations[SOLR_CONFIG_ENV][PROPERTIES]
        self.solr_cloud_properties = configurations[SOLR_CLOUD][PROPERTIES]
        self.solr_hdfs_properties = configurations[SOLR_HDFS][PROPERTIES]
        self.solr_ssl_properties = configurations[SOLR_SSL][PROPERTIES]
        self.example_collection_properties = configurations[EXAMPLE_COLLECTION][PROPERTIES]

        return self.validate_solr_configuration() + self.validate_solr_cloud_configuration() + \
               self.validate_solr_hdfs_configuration() + self.validate_solr_ssl_configuration() + \
               self.validate_example_collection_configuration()
