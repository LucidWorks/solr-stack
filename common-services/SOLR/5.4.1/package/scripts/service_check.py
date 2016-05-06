#!/usr/bin/env python

from resource_management.libraries.script import Script
from resource_management.core.logger import Logger

class ServiceCheck(Script):

    def service_check(self, env):
        import params

        Logger.info("Execute: service_check")

if __name__ == "__main__":
    ServiceCheck().execute()