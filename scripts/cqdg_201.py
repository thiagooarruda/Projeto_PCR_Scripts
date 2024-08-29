from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFileDestination
from PyQt5.QtCore import QCoreApplication
import psycopg2
from fpdf import FPDF

class CompareDatabases(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString(
            'dbname1', 
            'Nome do Banco Modelo (ex: 1292-4-NE)'
        ))
        self.addParameter(QgsProcessingParameterString(
            'dbname2', 
            'Nome do Banco Verificado (ex: edgv_300_recife)'
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
            'Host do Banco de Dados (ex: 105.125.136.33)', 
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

        def get_table_structure(cursor, schema='edgv'):
            cursor.execute(f"""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND column_name <> 'geom'
                ORDER BY table_name, ordinal_position
            """)
            return cursor.fetchall()

        def get_geometry_type(cursor, schema='edgv'):
            cursor.execute(f"""
                SELECT f_table_name, type
                FROM geometry_columns
                WHERE f_table_schema = '{schema}'
            """)
            return cursor.fetchall()

        feedback.pushInfo('Obtendo estruturas dos bancos de dados...')
        cur1 = conn1.cursor()
        cur2 = conn2.cursor()

        estrutura1 = get_table_structure(cur1)
        estrutura2 = get_table_structure(cur2)

        geometry1 = get_geometry_type(cur1)
        geometry2 = get_geometry_type(cur2)

        cur1.close()
        cur2.close()
        conn1.close()
        conn2.close()

        def organize_structure(estrutura):
            estrutura_dict = {}
            for tabela, coluna, tipo in estrutura:
                if tabela not in estrutura_dict:
                    estrutura_dict[tabela] = {}
                estrutura_dict[tabela][coluna] = tipo
            return estrutura_dict

        estrutura1_dict = organize_structure(estrutura1)
        estrutura2_dict = organize_structure(estrutura2)

        geometry1_dict = {table: geom_type for table, geom_type in geometry1}
        geometry2_dict = {table: geom_type for table, geom_type in geometry2}

        todas_tabelas = set(estrutura1_dict.keys()).union(set(estrutura2_dict.keys()))

        def compare_table_attributes(modelo, verificado, todas_tabelas, geom1, geom2):
            inconsistencias = []
            for tabela in todas_tabelas:
                colunas_modelo = modelo.get(tabela, {})
                colunas_verificado = verificado.get(tabela, {})
                for coluna, tipo_verificado in colunas_verificado.items():
                    tipo_modelo = colunas_modelo.get(coluna)
                    if tipo_modelo:
                        inconsistencias.append([
                            tabela, coluna,
                            f"{tipo_modelo}", f"{tipo_verificado}",
                            'Sim' if tipo_modelo == tipo_verificado else 'Não'
                        ])
                    else:
                        inconsistencias.append([
                            tabela, coluna,
                            'Não presente', f"{tipo_verificado}",
                            'Não'
                        ])
                for coluna, tipo_modelo in colunas_modelo.items():
                    if coluna not in colunas_verificado:
                        inconsistencias.append([
                            tabela, coluna,
                            f"{tipo_modelo}", 'Não presente',
                            'Não'
                        ])
                geom_tipo1 = geom1.get(tabela, 'Não presente')
                geom_tipo2 = geom2.get(tabela, 'Não presente')
                inconsistencias.append([tabela, 'Geometria', geom_tipo1, geom_tipo2, 'Sim' if geom_tipo1 == geom_tipo2 else 'Não'])
            return inconsistencias

        inconsistencias = compare_table_attributes(estrutura1_dict, estrutura2_dict, todas_tabelas, geometry1_dict, geometry2_dict)

        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'Relatório de Comparação de Atributos - CQDG 201', 0, 1, 'C')

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

            def add_table(self, data, dbname1, dbname2):
                self.set_font('Arial', 'B', 10)
                col_widths = [70, 50, 50, 50, 30]
                row_height = self.font_size * 1.5

                self.cell(col_widths[0], row_height*2, 'Tabela', border=1, align='C')
                self.cell(col_widths[1], row_height*2, 'Atributo', border=1, align='C')
                self.cell(col_widths[2], row_height*2, dbname1, border=1, align='C')
                self.cell(col_widths[3], row_height*2, dbname2, border=1, align='C')
                self.cell(col_widths[4], row_height*2, 'Coincide?', border=1, align='C')
                self.ln(row_height * 2)

                self.set_font('Arial', '', 10)
                for row in data:
                    for i, item in enumerate(row):
                        self.cell(col_widths[i], row_height, str(item), border=1, align='C')
                    self.ln(row_height)

        feedback.pushInfo('Gerando PDF de relatório...')
        pdf = PDF(orientation='L')
        pdf.add_page()
        pdf.add_table(inconsistencias, dbname1, dbname2)
        pdf.output(output_file)

        feedback.pushInfo(f"Relatório PDF gerado com sucesso: {output_file}")
        return results

    def name(self):
        return 'compare_databases'

    def displayName(self):
        return 'CQDG 201'

    def group(self):
        return 'MEDIDAS DE QUALIDADE DOS DADOS'

    def groupId(self):
        return 'cqdg_comparisons'

    def createInstance(self):
        return CompareDatabases()

    def shortHelpString(self):
        return QCoreApplication.translate(
            "CompareDatabases", 
            "Este script foi desenvolvido para comparar dois bancos de dados PostgreSQL baseados no esquema EDGV, "
            "focando na Consistência Conceitual, conforme a Tabela 7 - Medida conformidade com o modelo de dados. "
            "Ele gera um relatório PDF que destaca as discrepâncias nos atributos e tipos de geometria entre os bancos de dados analisados.\n\n"
            "Este script faz parte de um projeto de pesquisa colaborativo entre a Prefeitura da Cidade do Recife (PCR) "
            "e o Departamento de Cartografia (DECART) da Universidade Federal de Pernambuco (UFPE). O objetivo é auxiliar "
            "na implementação de controles de qualidade em dados geoespaciais, garantindo que os atributos e geometrias estejam "
            "em conformidade com o modelo de dados.\n\n"
    )
