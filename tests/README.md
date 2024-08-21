# Diretório tests

Este diretório contém testes automatizados para os scripts contidos no repositório. Os testes garantem que as funcionalidades dos scripts estejam funcionando corretamente e ajudam a detectar problemas antes de serem implementados em produção.

## Testes Disponíveis

### 1. `test_cqdg_201.py`
- **Descrição**: Testa o script `cqdg_201_compare_databases.py`, verificando se ele retorna os resultados esperados para diferentes cenários de comparação entre bancos de dados.
- **Execução**:
  ```bash
  python -m unittest tests/test_cqdg_201.py

