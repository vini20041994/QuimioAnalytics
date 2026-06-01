# Runners de Execucao

Este diretório concentra entrypoints de operacao do pipeline.

## Entrypoints principais

- `plug_and_play.sh`: sobe/derruba stack completa com Docker Compose (fallback para Flatpak host).
- `run_pipeline_frontend.py`: orquestrador principal (ETL interno, ranking e ETL externo opcional).
- `run_full_stack_etl.py`: wrapper de compatibilidade para executar o fluxo full stack com defaults.
- `primeira_execucao.sh`: setup inicial da maquina + execucao do orquestrador principal.

## ETL interno

- `run_etl.py`: fluxo Extract -> Transform -> Load das planilhas internas.

## ETLs externos (por fonte)

- `run_etl_candidates_external.py`: orquestrador de fontes externas por candidatos ranqueados.
- `run_etl_pubchem.py`: runner dedicado da fonte PubChem.
- `run_etl_chebi.py`: runner dedicado da fonte ChEBI.
- `run_etl_chemspider.py`: runner dedicado da fonte ChemSpider.
- `run_etl_classyfire.py`: runner dedicado da fonte ClassyFire.

## Setup de ambiente

- `install_system_prereqs.sh`: instalacao de pre-requisitos de sistema para ambiente local.

## Convencoes

- Prefira chamar `run_pipeline_frontend.py` para operacao normal.
- Use runners por fonte somente para reprocessamento pontual, debug ou validacao isolada.
- Evite criar wrappers legados de compatibilidade sem necessidade operacional.