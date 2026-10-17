default:
    @just --list --unsorted

# instala as dependências e o pacote
install:
    uv sync --extra dev

# prepara os dados: base indexável e rascunho do gabarito
data:
    uv run python -m pauliceia.extract
    uv run python -m pauliceia.clean
    uv run python -m pauliceia.draft
