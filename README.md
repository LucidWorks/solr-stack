## Solr service for Ambari

Download solr-stack repository:

    git clone https://github.com/lucidworks/solr-stack

Create Solr service pack:

    tar -zcvf solr-ambari-mpack-5.4.1.0.tar.gz solr-stack/

Deploy the Solr service on Ambari:

    ambari-server install-mpack --mpack=solr-ambari-mpack-5.4.1.0.tar.gz -v

Restart Ambari:

    ambari-server restart