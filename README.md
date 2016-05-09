## Solr service for Ambari

Download solr-stack repository:

    git clone https://github.com/lucidworks/solr-stack -b LWSHADOOP-487-Move-solr-stack-to-AMP

Create Solr service pack:

    tar -zcvf solr-ambari-mpack-5.4.1.0.tar.gz solr-stack/

Install Solr service to Ambari:

    ambari-server install-mpack --mpack=solr-ambari-mpack-5.4.1.0.tar.gz -v

Restart Ambari:

    ambari-server restart