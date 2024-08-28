Relatório: CQDG 201 - Comparação de Bancos de Dados PostgreSQL
Nome do Script: cqdg_201_compare_databases.py

Descrição:
Este script foi desenvolvido para comparar dois bancos de dados PostgreSQL baseados no esquema EDGV, focando na Consistência Conceitual, conforme a Tabela de Medidas de Controle de Qualidade 201 da CQDG. Ele gera um relatório PDF que destaca as discrepâncias nos atributos e tipos de geometria entre os bancos de dados analisados.

Objetivo:
O objetivo do script é garantir que os atributos e geometrias dos bancos de dados estejam em conformidade com o modelo de dados estabelecido, identificando possíveis inconsistências conceituais que possam comprometer a qualidade dos dados.

Componentes:

  Comparação de Atributos: Verifica se os atributos dos bancos de dados correspondem ao modelo de referência.
  Verificação de Tipos de Geometria: Compara os tipos de geometria presentes nos bancos de dados.
  Geração de Relatório PDF: O script gera um relatório PDF com todas as discrepâncias encontradas, organizado por tabelas e atributos.
  
Colaboração:
Este script faz parte de um projeto de pesquisa colaborativo entre a Prefeitura da Cidade do Recife (PCR) e o Departamento de Cartografia (DECART) da Universidade Federal de Pernambuco (UFPE). O foco é melhorar a qualidade dos dados geoespaciais utilizados nos processos cartográficos da cidade do Recife.
