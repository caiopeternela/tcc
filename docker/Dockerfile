FROM docker.elastic.co/elasticsearch/elasticsearch:7.3.0

RUN elasticsearch-plugin install --batch analysis-phonetic

RUN elasticsearch-plugin install --batch \
    https://github.com/rodrigopc/elasticsearch-analysis-metaphone_ptBR/raw/master/dist/elasticsearch-analysis-metaphone_ptBR-7.3.0.zip
