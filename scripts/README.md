
# Diretório scripts

Este diretório contém scripts Python usados para diversas tarefas de controle de qualidade e análise de dados no projeto PCR.

## Scripts Disponíveis

### 1. `cqdg_201_compare_databases.py`
- **Descrição**: Compara dois bancos de dados PostgreSQL de acordo com as diretrizes do CQDG 201 para consistência conceitual. O script verifica se as classes e atributos de um banco de dados estão em conformidade com o modelo de dados de referência.
- **Uso**: 
  ```bash
  python scripts/cqdg_201_compare_databases.py --dbname1 "NomeDoBancoModelo" --dbname2 "NomeDoBancoVerificado"

Como Contribuir
Se você deseja adicionar novos scripts, por favor, siga estas diretrizes:

Nomeie o script de forma clara e descritiva.
Inclua comentários explicativos no código.
Atualize este arquivo README.md com informações sobre o novo script.
