default:
    @just --list --unsorted

# instala as dependências e o pacote
install:
    uv sync --extra dev

# sobe o Elasticsearch com os plugins fonéticos
up:
    docker build -t tcc-elasticsearch docker/
    -@docker stop tcc-elasticsearch 2>/dev/null
    docker run -d --rm --name tcc-elasticsearch -p 9200:9200 \
        -e discovery.type=single-node -e ES_JAVA_OPTS=-Xms1g\ -Xmx1g \
        tcc-elasticsearch
    @echo "esperando o Elasticsearch responder..."
    @until curl -sf localhost:9200 >/dev/null; do sleep 2; done
    @echo "no ar em http://localhost:9200"

# derruba o Elasticsearch
down:
    docker stop tcc-elasticsearch

# prepara os dados: base indexável e rascunho do gabarito
data:
    uv run python -m pauliceia.extract
    uv run python -m pauliceia.clean
    uv run python -m pauliceia.draft
