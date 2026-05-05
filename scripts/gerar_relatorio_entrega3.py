"""
Gerador do Relatório de Entrega – Etapa 3
Transformação: Processamento, limpeza, normalização e feature engineering
para análise preditiva.
"""

from pathlib import Path
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ──────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = PROJECT_ROOT / "docs" / "Entrega3_Transformacao_e_FeatureEngineering.pdf"
OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)

DATA_ENTREGA = "14/04/2026"
DISCIPLINA   = "QuimioAnalytics – Análise Preditiva de Metabolômica"
ETAPA        = "Etapa 3 – Transformação, Limpeza, Normalização e Feature Engineering"

# ──────────────────────────────────────────────────────────────────────────────
# ESTILOS
# ──────────────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

titulo_style = ParagraphStyle(
    "Titulo",
    parent=styles["Title"],
    fontSize=18,
    spaceAfter=6,
    textColor=colors.HexColor("#1a3a5c"),
    alignment=TA_CENTER,
)
subtitulo_style = ParagraphStyle(
    "Subtitulo",
    parent=styles["Normal"],
    fontSize=12,
    spaceAfter=4,
    textColor=colors.HexColor("#2e6da4"),
    alignment=TA_CENTER,
)
secao_style = ParagraphStyle(
    "Secao",
    parent=styles["Heading2"],
    fontSize=13,
    spaceBefore=14,
    spaceAfter=4,
    textColor=colors.HexColor("#1a3a5c"),
    borderPad=4,
)
subsecao_style = ParagraphStyle(
    "Subsecao",
    parent=styles["Heading3"],
    fontSize=11,
    spaceBefore=10,
    spaceAfter=3,
    textColor=colors.HexColor("#2e6da4"),
)
corpo_style = ParagraphStyle(
    "Corpo",
    parent=styles["Normal"],
    fontSize=10,
    leading=15,
    spaceAfter=5,
    alignment=TA_JUSTIFY,
)
bullet_style = ParagraphStyle(
    "Bullet",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    leftIndent=18,
    spaceAfter=3,
)
codigo_style = ParagraphStyle(
    "Codigo",
    parent=styles["Normal"],
    fontSize=9,
    fontName="Courier",
    backColor=colors.HexColor("#f4f4f4"),
    leftIndent=14,
    rightIndent=14,
    leading=13,
    spaceAfter=6,
    spaceBefore=4,
)
rodape_style = ParagraphStyle(
    "Rodape",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.grey,
    alignment=TA_CENTER,
)
faculdade_style = ParagraphStyle(
    "Faculdade",
    parent=styles["Normal"],
    fontSize=11,
    spaceAfter=2,
    textColor=colors.HexColor("#1a3a5c"),
    alignment=TA_CENTER,
    fontName="Helvetica-Bold",
)
curso_style = ParagraphStyle(
    "Curso",
    parent=styles["Normal"],
    fontSize=10,
    spaceAfter=8,
    textColor=colors.HexColor("#2e6da4"),
    alignment=TA_CENTER,
    fontName="Helvetica",
)


def hr():
    return HRFlowable(width="100%", thickness=1, color=colors.HexColor("#c0d0e0"), spaceAfter=8)


def secao(texto):
    return Paragraph(texto, secao_style)


def subsecao(texto):
    return Paragraph(texto, subsecao_style)


def p(texto):
    return Paragraph(texto, corpo_style)


def bullet(texto):
    return Paragraph(f"• {texto}", bullet_style)


def code(texto):
    return Paragraph(texto, codigo_style)


# ──────────────────────────────────────────────────────────────────────────────
# CONTEÚDO DO DOCUMENTO
# ──────────────────────────────────────────────────────────────────────────────
def build_content():
    elems = []

    # ── Cabeçalho da Faculdade ──
    elems.append(Paragraph("FACULDADE DE TECNOLOGIA UNISENAI FLORIANÓPOLIS", faculdade_style))
    elems.append(Paragraph("CURSO DE GRADUAÇÃO EM CIÊNCIA DE DADOS E INTELIGÊNCIA ARTIFICIAL", curso_style))
    
    elems.append(Spacer(1, 0.3 * cm))
    elems.append(Paragraph("<b>Equipe:</b>", subsecao_style))
    elems.append(Spacer(1, 0.15 * cm))
    
    # Tabela de integrantes
    integrantes = [
        ["Integrante", "Responsabilidade"],
        ["Guilherme da Silva Anselmo", "Modelagem PostgreSQL e DER"],
        ["Guilherme Zamboni Menegacio", "ETL com Pandas"],
        ["Vinícius Joacir dos Anjos", "Integração com bases públicas"],
        ["Samuel Silva de Rezende", "Documentação e arquitetura"],
    ]
    t_integrantes = Table(integrantes, colWidths=[5 * cm, 11 * cm])
    t_integrantes.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c0d0e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faff")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elems.append(t_integrantes)
    
    elems.append(Spacer(1, 0.4 * cm))
    elems.append(hr())

    # ── Cabeçalho ──
    elems.append(Paragraph(DISCIPLINA, subtitulo_style))
    elems.append(Spacer(1, 0.2 * cm))
    elems.append(Paragraph(ETAPA, titulo_style))
    elems.append(Spacer(1, 0.3 * cm))

    # Tabela de metadados
    meta = [
        ["Data de Entrega", DATA_ENTREGA],
        ["Peso da Etapa",   "10%"],
        ["Entregável",      "Dataset estruturado e normalizado para modelagem"],
    ]
    t = Table(meta, colWidths=[5 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0fa")),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#c0d0e0")),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, colors.HexColor("#f7faff")]),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 0.4 * cm))
    elems.append(hr())

    # ── 1. Visão geral ──
    elems.append(secao("1. Visão Geral"))
    elems.append(p(
        "Este documento descreve todas as etapas de transformação, limpeza, normalização "
        "e feature engineering aplicadas ao dataset do projeto QuimioAnalytics, "
        "produzindo um dataset estruturado e normalizado apto para análise preditiva em metabolômica."
    ))
    elems.append(p(
        "O pipeline de transformação segue uma arquitetura ETL (Extract-Transform-Load) modular, "
        "operando sobre dados oriundos de cinco fontes externas — PubChem, ChEBI, ChemSpider, "
        "ClassyFire e FooDB — além dos dados brutos de entrada do usuário (planilha Excel e CSV)."
    ))

    # ── 2. Fontes de dados ──
    elems.append(secao("2. Fontes de Dados Utilizadas"))
    fontes = [
        ["Fonte",        "Arquivo de Transformação",           "Dados Obtidos"],
        ["PubChem",      "transform/transform_pubchem.py",     "Fórmula, SMILES, InChIKey, propriedades físico-químicas"],
        ["ChEBI",        "transform/transform_chebi.py",       "Ontologia, vias metabólicas, sinônimos"],
        ["ChemSpider",   "transform/transform_chemspider.py",  "Estruturas moleculares, identificadores"],
        ["ClassyFire",   "transform/transform_classyfire.py",  "Classificação química hierárquica"],
        ["FooDB",        "transform/transform_foodb.py",       "Dados de alimentos e metabólitos"],
        ["Entrada (xlsx/csv)", "transform/transform_stg_xlsx.py", "Dados de identificação, abundância e compostos"],
    ]
    tf = Table(fontes, colWidths=[3.2 * cm, 5.8 * cm, 8 * cm])
    tf.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#c0d0e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faff")]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elems.append(tf)

    # ── 3. Processamento e Limpeza ──
    elems.append(secao("3. Processamento e Limpeza dos Dados"))

    elems.append(subsecao("3.1 Dados de Entrada do Usuário"))
    elems.append(p(
        "O arquivo <b>transform_stg_xlsx.py</b> realiza a transformação dos dados brutos "
        "provenientes da planilha Excel e do CSV de resultados (<i>merge_resultado.csv</i>). "
        "As etapas executadas são:"
    ))
    elems.append(bullet("Leitura de arquivos Parquet do diretório <i>staging/</i>."))
    elems.append(bullet("Renomeação padronizada de colunas via mapeamentos <b>COL_MAP_IDENT</b>, "
                        "<b>COL_MAP_ABUND</b> e <b>COL_MAP_COMPOSTOS</b>."))
    elems.append(bullet("Validação e conversão de campos numéricos com a função "
                        "<b>safe_numeric()</b> — retorna <i>None</i> em vez de lançar exceção."))
    elems.append(bullet("Validação e conversão de campos inteiros com <b>safe_int()</b>."))
    elems.append(bullet("Normalização global de valores ausentes: NaN → None via "
                        "<b>normalize_dataframe()</b>, garantindo compatibilidade com PostgreSQL."))
    elems.append(bullet("Exportação dos DataFrames confiáveis para Parquet: "
                        "<i>identificacao_trusted.parquet</i>, <i>abundancia_trusted.parquet</i> "
                        "e <i>compostos_trusted.parquet</i>."))

    elems.append(Spacer(1, 0.3 * cm))
    elems.append(subsecao("3.2 Dados de Fontes Externas (PubChem, ChEBI, ChemSpider…)"))
    elems.append(p(
        "Cada fonte externa possui seu script de transformação dedicado. O utilitário "
        "<b>external_transform_utils.py</b> provê funções compartilhadas. As operações "
        "comuns aplicadas a todas as fontes incluem:"
    ))
    elems.append(bullet("Mapeamento de nomes de colunas da API/fonte para o schema do banco de dados."))
    elems.append(bullet("Verificação da presença de colunas obrigatórias (e.g., "
                        "<i>pubchem_cid</i>, <i>inchikey</i>, <i>canonical_smiles</i>)."))
    elems.append(bullet("Parse seguro de campos JSON (sinônimos, classificações) com "
                        "tratamento de erros."))
    elems.append(bullet("Conversão de tipos (<i>molecular_weight</i>, <i>exact_mass</i>, "
                        "<i>xlogp</i>, <i>tpsa</i> → numérico)."))
    elems.append(bullet("Remoção de duplicatas e aplicação de restrições únicas antes da carga "
                        "(migrations 003, 006)."))

    elems.append(Spacer(1, 0.3 * cm))
    elems.append(subsecao("3.3 Dataset Bruto – merge_resultado.csv"))
    elems.append(p(
        "O arquivo CSV principal contém os candidatos moleculares identificados pelo software "
        "de metabolômica. Colunas-chave limpas e validadas:"
    ))
    colunas = [
        ["Coluna Original",         "Coluna Normalizada",    "Tipo",    "Tratamento"],
        ["Neutral mass (Da)",        "neutral_mass",          "FLOAT",   "pd.to_numeric, coerce"],
        ["m/z",                      "mz",                    "FLOAT",   "pd.to_numeric, coerce"],
        ["Retention time (min)",     "rt",                    "FLOAT",   "pd.to_numeric, coerce"],
        ["Score",                    "score_original",        "FLOAT",   "fillna(0)"],
        ["Fragmentation Score",      "fragment_score",        "FLOAT",   "fillna(0)"],
        ["Mass Error (ppm)",         "mass_error_ppm",        "FLOAT",   "fillna(0), abs()"],
        ["Isotope Similarity",       "isotope_similarity",    "FLOAT",   "fillna(0)"],
        ["1.1 … 6.2 (réplicas)",     "cols_replicatas",       "FLOAT",   "pd.to_numeric, coerce"],
    ]
    tc = Table(colunas, colWidths=[4 * cm, 4 * cm, 2.2 * cm, 6.8 * cm])
    tc.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#2e6da4")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#c0d0e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faff")]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(tc)

    # ── 4. Normalização ──
    elems.append(secao("4. Normalização"))
    elems.append(p(
        "Para garantir compatibilidade com modelos preditivos e consistência estatística, "
        "os seguintes métodos de normalização foram aplicados:"
    ))

    elems.append(subsecao("4.1 Normalização Min-Max do Score do Software"))
    elems.append(code(
        "s_software = (score_original − min) / (max − min)   →   [0, 1]"
    ))
    elems.append(p(
        "O score bruto reportado pelo software de identificação é normalizado "
        "para o intervalo [0, 1] usando os extremos do conjunto de candidatos, "
        "eliminando a dependência de escala entre análises diferentes."
    ))

    elems.append(subsecao("4.2 Normalização por Clip – Fragmentação e Similaridade Isotópica"))
    elems.append(code(
        "s_fragmentation = clip(fragment_score / 100, 0, 1)\n"
        "s_isotope       = clip(isotope_similarity / 100, 0, 1)"
    ))
    elems.append(p(
        "Scores reportados na escala 0–100 são convertidos para 0–1 com saturação "
        "em ambos os extremos, prevenindo distorções por valores fora do intervalo esperado."
    ))

    elems.append(subsecao("4.3 Normalização do Erro de Massa (ppm)"))
    elems.append(code(
        "s_mass = max(0, 1 − |mass_error_ppm| / tolerance)   (tolerância padrão = 5 ppm)"
    ))
    elems.append(p(
        "Penaliza candidatos com desvio de massa elevado. Desvios maiores que a tolerância "
        "resultam em score zero, enquanto desvios próximos de zero resultam em score máximo."
    ))

    elems.append(subsecao("4.4 Normalização da Abundância"))
    elems.append(code(
        "media_abundancia = mean(colunas_replicatas)   [por linha]\n"
        "cv               = std / (media + ε) × 100    [coeficiente de variação %]"
    ))
    elems.append(p(
        "A abundância média e o coeficiente de variação entre réplicas são calculados "
        "por candidato. O CV mede a consistência entre replicatas biológicas/técnicas."
    ))

    # ── 5. Feature Engineering ──
    elems.append(secao("5. Feature Engineering"))
    elems.append(p(
        "O módulo <b>scripts/features/analitcs.py</b> implementa o pipeline de "
        "construção de features para o ranking probabilístico de candidatos moleculares. "
        "O fluxo completo é:"
    ))

    passos = [
        ["Passo", "Operação",                              "Descrição"],
        ["1",  "Carga e renomeação",                       "Leitura do CSV e padronização dos nomes de colunas."],
        ["2",  "Processamento de réplicas",                "Cálculo de média e CV entre as 12 colunas de replicatas (1.1…6.2)."],
        ["3",  "Normalização de scores",                   "Conversão de score_original, fragment_score, isotope_similarity e mass_error_ppm para [0, 1]."],
        ["4",  "Score base ponderado",                     "0,40 × s_mass + 0,30 × s_frag + 0,20 × s_soft + 0,10 × s_isotope"],
        ["5",  "Fator de abundância",                      "log1p(media_abundancia) × 1/(1 + cv) — amplifica candidatos com sinal alto e réplicas estáveis."],
        ["6",  "Score final",                              "score_base × abundance_factor"],
        ["7",  "Probabilidade global (Softmax)",           "Conversão do score_final em probabilidade sobre todos os candidatos."],
        ["8",  "Seleção Top 5",                            "Ordenação decrescente; seleção dos 5 candidatos mais prováveis."],
        ["9",  "Exportação",                               "Salvamento em staging/top5_candidates.parquet."],
    ]
    tp = Table(passos, colWidths=[1.4 * cm, 4.6 * cm, 11 * cm])
    tp.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#c0d0e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faff")]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN",       (0, 0), (0, -1), "CENTER"),
    ]))
    elems.append(tp)

    elems.append(Spacer(1, 0.3 * cm))
    elems.append(subsecao("5.1 Fórmula de Score Final"))
    elems.append(code(
        "score_base  = 0.40·s_mass + 0.30·s_frag + 0.20·s_soft + 0.10·s_isotope\n"
        "score_final = score_base × log1p(abundância_média) × 1/(1 + CV)\n"
        "probabilidade = softmax(score_final)   [sobre todos os candidatos]"
    ))
    elems.append(p(
        "A escolha dos pesos reflete a relevância analítica: o erro de massa (40%) é o "
        "critério mais rigoroso em espectrometria de massas de alta resolução; "
        "a fragmentação (30%) confirma a estrutura; o score do software (20%) captura "
        "informação adicional de alinhamento; e a similaridade isotópica (10%) valida "
        "a fórmula molecular proposta."
    ))

    # ── 6. Dataset Final ──
    elems.append(secao("6. Dataset Final para Modelagem"))
    elems.append(p(
        "O dataset normalizado gerado ao final do pipeline contém, para cada candidato molecular, "
        "as seguintes features prontas para modelagem preditiva:"
    ))

    features = [
        ["Feature",              "Tipo",     "Origem"],
        ["neutral_mass",         "FLOAT",    "Dado bruto normalizado"],
        ["mz",                   "FLOAT",    "Dado bruto normalizado"],
        ["rt",                   "FLOAT",    "Dado bruto normalizado"],
        ["s_mass",               "FLOAT",    "Feature engineered – erro de massa"],
        ["s_fragmentation",      "FLOAT",    "Feature engineered – fragmentação"],
        ["s_isotope",            "FLOAT",    "Feature engineered – isótopos"],
        ["s_software",           "FLOAT",    "Feature engineered – score min-max"],
        ["score_base",           "FLOAT",    "Feature engineered – combinação ponderada"],
        ["media_abundancia",     "FLOAT",    "Feature engineered – média de réplicas"],
        ["cv",                   "FLOAT",    "Feature engineered – coeficiente de variação"],
        ["score_final",          "FLOAT",    "Feature engineered – score × abundância"],
        ["probabilidade",        "FLOAT",    "Feature engineered – softmax global"],
        ["rank",                 "INT",      "Ranking final do candidato"],
        ["molecular_formula",    "STRING",   "Enriquecimento PubChem/ChEBI"],
        ["canonical_smiles",     "STRING",   "Enriquecimento PubChem"],
        ["xlogp / tpsa",         "FLOAT",    "Enriquecimento PubChem (lipofilicidade / área polar)"],
        ["chemical_category",    "STRING",   "Enriquecimento ClassyFire / planilha"],
    ]
    tfeat = Table(features, colWidths=[4.5 * cm, 2 * cm, 10.5 * cm])
    tfeat.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#2e6da4")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#c0d0e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faff")]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(tfeat)

    # ── 7. Qualidade dos Dados ──
    elems.append(secao("7. Avaliação da Qualidade dos Dados Brutos"))
    elems.append(p(
        "Durante o pré-processamento foram identificados e tratados os seguintes "
        "pontos críticos de qualidade:"
    ))
    elems.append(bullet(
        "<b>Valores ausentes:</b> todas as colunas numéricas recebem tratamento "
        "explícito — preenchimento com 0 nos scores (via <i>fillna(0)</i>) e "
        "conversão para <i>None</i> em campos identificadores, conforme semântica do dado."
    ))
    elems.append(bullet(
        "<b>Tipos inconsistentes:</b> colunas numéricas importadas como string "
        "são convertidas com <i>pd.to_numeric(errors='coerce')</i>, substituindo "
        "valores não parseáveis por NaN."
    ))
    elems.append(bullet(
        "<b>Duplicatas:</b> aplicadas via migrations do banco (003 e 006), "
        "garantindo restrições de unicidade em <i>stg.pubchem_compound_raw</i> "
        "e <i>stg.chebi_compound_raw</i>."
    ))
    elems.append(bullet(
        "<b>Abundâncias zero/nulas em réplicas:</b> tratadas com uso de constante "
        "ε = 1e-9 no cálculo de CV, evitando divisão por zero."
    ))
    elems.append(bullet(
        "<b>Escala heterogênea:</b> scores em escalas distintas (0–100, ppm, "
        "escala do software) foram todos normalizados para [0, 1] antes da combinação."
    ))

    # ── 8. Estrutura de Arquivos ──
    elems.append(secao("8. Estrutura de Arquivos Gerados"))
    arqs = [
        ["Arquivo",                           "Descrição"],
        ["staging/identificacao_trusted.parquet",  "Dados de identificação limpos e renomeados"],
        ["staging/abundancia_trusted.parquet",     "Dados de abundância limpos e renomeados"],
        ["staging/compostos_trusted.parquet",      "Dados de compostos limpos e renomeados"],
        ["staging/top5_candidates.parquet",        "Top 5 candidatos com todas as features engineered"],
        ["staging/pubchem_raw.csv",                "Dados brutos extraídos do PubChem"],
        ["staging/chebi_raw.csv",                  "Dados brutos extraídos do ChEBI"],
    ]
    tarqs = Table(arqs, colWidths=[7.5 * cm, 9.5 * cm])
    tarqs.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#c0d0e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faff")]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(tarqs)

    # ── 9. Conclusão ──
    elems.append(secao("9. Conclusão"))
    elems.append(p(
        "O pipeline de transformação e feature engineering implementado no projeto "
        "QuimioAnalytics produz um dataset estruturado, normalizado e enriquecido, "
        "pronto para alimentar modelos de análise preditiva em metabolômica."
    ))
    elems.append(p(
        "Os dados brutos originais passam por limpeza rigorosa (tratamento de ausentes, "
        "tipagem, deduplicação), normalização para escala comum [0, 1] e construção "
        "de features derivadas que capturam, de forma combinada, a qualidade espectral "
        "(massa, fragmentação, isótopos) e a confiabilidade analítica (abundância e "
        "consistência entre réplicas)."
    ))
    elems.append(p(
        "O dataset final (<i>top5_candidates.parquet</i>) contém os 5 candidatos "
        "moleculares mais prováveis para cada feature cromatográfica, com probabilidades "
        "globais calculadas via softmax, fornecendo tanto a estrutura necessária para "
        "modelagem supervisionada quanto para análise exploratória."
    ))

    # ── Rodapé ──
    elems.append(Spacer(1, 0.6 * cm))
    elems.append(hr())
    elems.append(Paragraph(
        f"Documento gerado automaticamente em {date.today().strftime('%d/%m/%Y')} "
        f"| QuimioAnalytics | Etapa 3",
        rodape_style,
    ))

    return elems


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=ETAPA,
        author="QuimioAnalytics",
        subject="Entrega Etapa 3 – Transformação e Feature Engineering",
    )
    doc.build(build_content())
    print(f"PDF gerado com sucesso: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
