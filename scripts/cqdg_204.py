from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFileDestination
from PyQt5.QtCore import QCoreApplication
import psycopg2
from fpdf import FPDF
import re

class CQDG204CompareDomains(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString(
            'dbname1', 
            'Nome do Banco Modelo (ex: database_1)'
        ))
        self.addParameter(QgsProcessingParameterString(
            'dbname2', 
            'Nome do Banco Verificado (ex: database_2)'
        ))
        self.addParameter(QgsProcessingParameterString(
            'usuario', 
            'Usuário do Banco de Dados'
        ))
        self.addParameter(QgsProcessingParameterString(
            'password', 
            'Senha do Banco de Dados', 
            optional=True
        ))
        self.addParameter(QgsProcessingParameterString(
            'host', 
            'Host do Banco de Dados (ex: 192.168.1.1)', 
            defaultValue='localhost'
        ))
        self.addParameter(QgsProcessingParameterString(
            'port', 
            'Porta do Banco de Dados (ex: 5432)', 
            defaultValue='5432'
        ))
        self.addParameter(QgsProcessingParameterFileDestination(
            'output_file', 
            'Salvar Relatório como', 
            fileFilter='PDF files (*.pdf)'
        ))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        # Capturar as entradas do usuário
        dbname1 = self.parameterAsString(parameters, 'dbname1', context)
        dbname2 = self.parameterAsString(parameters, 'dbname2', context)
        usuario = self.parameterAsString(parameters, 'usuario', context)
        password = self.parameterAsString(parameters, 'password', context)
        host = self.parameterAsString(parameters, 'host', context)
        port = self.parameterAsString(parameters, 'port', context)
        output_file = self.parameterAsString(parameters, 'output_file', context)

        def connect_to_database(dbname):
            return psycopg2.connect(
                dbname=dbname, 
                user=usuario, 
                password=password, 
                host=host, 
                port=port
            )

        feedback.pushInfo('Conectando aos bancos de dados...')
        conn1 = connect_to_database(dbname1)
        conn2 = connect_to_database(dbname2)

        def fetch_table_names(cursor):
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'dominios'")
            return cursor.fetchall()

        def fetch_table_data(cursor, table_name):
            cursor.execute(f"SELECT * FROM dominios.{table_name}")
            return cursor.fetchall()

        def normalize_table_name(name):
            return re.sub(r'^(prefixo_|sufixo_)|(_prefixo|_sufixo)$', '', name).replace('_', '').lower()

        def normalize_value(value):
            return re.sub(r'\s*\(\d+\)', '', value)

        cur1 = conn1.cursor()
        cur2 = conn2.cursor()

        dominios1 = fetch_table_names(cur1)
        dominios2 = fetch_table_names(cur2)

        normalized_dominios1 = {normalize_table_name(item[0]): item[0] for item in dominios1}
        normalized_dominios2 = {normalize_table_name(item[0]): item[0] for item in dominios2}

        table_data = []

        for norm_name, table_name1 in normalized_dominios1.items():
            table_name2 = normalized_dominios2.get(norm_name)
            if table_name2:
                lista1 = fetch_table_data(cur1, table_name1)
                lista2 = fetch_table_data(cur2, table_name2)

                normalized_lista1 = [(item[0], normalize_value(item[1])) for item in lista1]
                normalized_lista2 = [(item[0], normalize_value(item[1])) for item in lista2]

                for row1 in lista1:
                    normalized_row1 = (row1[0], normalize_value(row1[1]))
                    if normalized_row1 in normalized_lista2:
                        table_data.append([table_name1, str(row1), str(row1), 'Sim'])
                    else:
                        table_data.append([table_name1, str(row1), 'Não coincide', 'Não'])
                for row2 in lista2:
                    normalized_row2 = (row2[0], normalize_value(row2[1]))
                    if normalized_row2 not in normalized_lista1:
                        table_data.append([table_name2, 'Não presente', str(row2), 'Não'])
            else:
                possible_match = None
                for other_norm_name, other_table_name2 in normalized_dominios2.items():
                    if norm_name in other_norm_name or other_norm_name in norm_name:
                        possible_match = other_table_name2
                        break
                if possible_match:
                    lista1 = fetch_table_data(cur1, table_name1)
                    lista2 = fetch_table_data(cur2, possible_match)

                    normalized_lista1 = [(item[0], normalize_value(item[1])) for item in lista1]
                    normalized_lista2 = [(item[0], normalize_value(item[1])) for item in lista2]

                    table_data.append([table_name1, 'Nome não coincide mas relacionado', possible_match, 'Possível relação'])

                    for row1 in lista1:
                        normalized_row1 = (row1[0], normalize_value(row1[1]))
                        if normalized_row1 in normalized_lista2:
                            table_data.append([table_name1, str(row1), str(row1), 'Sim'])
                        else:
                            table_data.append([table_name1, str(row1), 'Não coincide', 'Não'])
                    for row2 in lista2:
                        normalized_row2 = (row2[0], normalize_value(row2[1]))
                        if normalized_row2 not in normalized_lista1:
                            table_data.append([possible_match, 'Não presente', str(row2), 'Não'])
                else:
                    table_data.append([table_name1, 'Não presente no banco 2', 'N/A', 'Não'])

        for norm_name, table_name2 in normalized_dominios2.items():
            if norm_name not in normalized_dominios1:
                table_data.append([table_name2, 'N/A', 'Não presente no banco 1', 'Não'])

        cur1.close()
        conn1.close()
        cur2.close()
        conn2.close()

        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'Relatório de Comparação de Domínios - CQDG 204', 0, 1, 'C')

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

            def add_table(self, data, dbname1, dbname2):
                self.set_font('Arial', 'B', 12)
                col_widths = [60, 90, 90, 40]  # Ajustar larguras das colunas
                row_height = self.font_size * 1.5
                headers = ["Classes", dbname1, dbname2, "Coincide?"]

                for i, header in enumerate(headers):
                    self.cell(col_widths[i], row_height, header.encode('latin1', 'replace').decode('latin1'), border=1)
                self.ln(row_height)

                self.set_font('Arial', '', 12)
                for row in data:
                    for i, item in enumerate(row):
                        self.cell(col_widths[i], row_height, str(item).encode('latin1', 'replace').decode('latin1'), border=1)
                    self.ln(row_height)

        pdf = PDF(orientation='L')
        pdf.add_page()
        pdf.add_table(table_data, dbname1, dbname2)
        pdf.output(output_file)

        feedback.pushInfo(f"Relatório PDF gerado com sucesso: {output_file}")
        return results

    def name(self):
        return 'cqdg_204_compare_domains'

    def displayName(self):
        return 'CQDG 204'

    def group(self):
        return 'Comparações CQDG'

    def groupId(self):
        return 'cqdg_comparisons'

    def createInstance(self):
        return CQDG204CompareDomains()

    def shortHelpString(self):
        return QCoreApplication.translate(
            "CQDG204", 
            "Este script foi desenvolvido para comparar os valores dos domínios em dois bancos de dados PostgreSQL, "
            "conforme a Tabela de Medidas de Controle de Qualidade 204 da CQDG. Ele gera um relatório PDF que destaca "
            "as discrepâncias encontradas entre os bancos de dados analisados.\n\n"
            "Este script faz parte de um projeto de pesquisa colaborativo entre a Prefeitura da Cidade do Recife (PCR) "
            "e o Departamento de Cartografia (DECART) da Universidade Federal de Pernambuco (UFPE). O objetivo é auxiliar "
            "na implementação de controles de qualidade em dados geoespaciais, contribuindo para a melhoria contínua dos "
            "processos cartográficos na cidade do Recife.\n\n"
            "Desenvolvido por Thiago Arruda."
    )

