## Solr service for Ambari

Stop Ambari server:

    ambari-server stop

Download solr-stack repository:

    git clone https://github.com/lucidworks/solr-stack

Create Solr service pack:

    ./gradlew clean makePackage

Deploy the Solr service on Ambari server:

    ambari-server install-mpack --mpack=build/solr-service-mpack-{serviceVersion}.tar.gz -v

Start Ambari server:

    ambari-server start