"""
Geradores de relatório a partir do diagnóstico consolidado:

  * gerar_docx  -> documento Word editável (.docx)
  * gerar_pptx  -> apresentação no formato do PowerPoint (.pptx)
  * gerar_pdf   -> PDF em paisagem, no estilo de slides

Todos consomem o dicionário produzido por report.consolidado.
"""

from __future__ import annotations

from typing import List, Tuple

AZUL = (0x1F, 0x3A, 0x5F)
VERDE = (0x2E, 0x8B, 0x57)
LARANJA = (0xB0, 0x6A, 0x1F)
VERMELHO = (0xB2, 0x3B, 0x3B)


# ---------------------------------------------------------------- formatação
def brl(v: float) -> str:
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def pct(v: float) -> str:
    return f"{v * 100:.1f}%".replace(".", ",")


QUAD_LABEL = {
    "ofensiva": "Ofensiva / Crescimento",
    "reorientacao": "Reorientação / Crescimento",
    "defensiva": "Defensiva / Manutenção",
    "sobrevivencia": "Sobrevivência",
}


def _linhas_dre(diag: dict) -> List[Tuple[str, str]]:
    d = diag["dre"]["dre"]
    ind = diag["dre"]["indicadores"]
    return [
        ("Receita Líquida", brl(d["receita_liquida"])),
        ("(-) Custos Diretos", brl(-d["custos_diretos"])),
        ("(=) Margem de Contribuição", brl(d["margem_contribuicao"])),
        ("(-) Custos Indiretos", brl(-d["custos_indiretos"])),
        ("(=) EBITDA", brl(d["ebitda"])),
        ("(-) Depreciação / Amortização", brl(-d["depreciacao"])),
        ("(-) Juros", brl(-d["juros"])),
        ("(=) EBIT", brl(d["ebit"])),
        ("(-) IRPJ / CSLL", brl(-(d["irpj"] + d["csll"]))),
        ("(=) Lucro Operacional", brl(d["lucro_operacional"])),
        ("Margem de contribuição", pct(ind["margem_contribuicao_pct"])),
        ("Margem EBITDA", pct(ind["margem_ebitda_pct"])),
        ("Margem líquida", pct(ind["margem_liquida_pct"])),
        ("Ponto de equilíbrio (receita)", brl(ind["ponto_equilibrio_receita"])),
    ]


def _resumo(diag: dict) -> List[Tuple[str, str]]:
    r = diag["resumo"]
    return [
        ("Receita líquida / mês", brl(r["receita_liquida_mensal"])),
        ("Custo total / mês", brl(r["custo_total_mensal"])),
        ("Lucro operacional / mês", brl(r["lucro_operacional_mensal"])),
        ("Margem líquida", pct(r["margem_liquida_pct"])),
        ("Ponto de equilíbrio / mês", brl(r["ponto_equilibrio_receita"])),
        ("Total de alunos", str(r["alunos_total"])),
    ]


# ----------------------------------------------------------------- DOCX
def gerar_docx(diag: dict, caminho: str) -> str:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    meta = diag["meta"]
    doc = Document()

    def titulo(txt, size=15, cor=AZUL, space_before=10):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        run = p.add_run(txt)
        run.bold = True
        run.font.size = Pt(size)
        run.font.color.rgb = RGBColor(*cor)
        return p

    def tabela(linhas, destaque_ultima=False):
        t = doc.add_table(rows=0, cols=2)
        t.style = "Light Grid Accent 1"
        for i, (a, b) in enumerate(linhas):
            row = t.add_row().cells
            row[0].text = a
            row[1].text = b
            for cell in row:
                for par in cell.paragraphs:
                    for run in par.runs:
                        run.font.size = Pt(10)
                        if a.startswith("(=)") or (destaque_ultima and i == len(linhas) - 1):
                            run.bold = True
            row[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        return t

    # Capa
    cabe = doc.add_paragraph()
    cabe.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cabe.add_run("Diagnóstico Econômico-Financeiro")
    r.bold = True
    r.font.size = Pt(24)
    r.font.color.rgb = RGBColor(*AZUL)
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rs = sub.add_run(f"{meta['escola']}  ·  {meta['ano']}")
    rs.font.size = Pt(14)
    doc.add_paragraph(
        f"Regime tributário: {meta['regime'].title()}   |   "
        f"Emitido em {meta['data_geracao']}"
    ).alignment = WD_ALIGN_PARAGRAPH.CENTER

    titulo("Resumo Executivo")
    tabela(_resumo(diag))

    titulo("Receitas")
    seg = diag["receitas"]["segmentos"]
    t = doc.add_table(rows=1, cols=4)
    t.style = "Light Grid Accent 1"
    hdr = t.rows[0].cells
    for i, h in enumerate(["Nível", "Alunos", "Receita bruta", "Participação"]):
        hdr[i].text = h
    for s in seg:
        c = t.add_row().cells
        c[0].text = s["nome"]
        c[1].text = str(s["alunos"])
        c[2].text = brl(s["receita_bruta"])
        c[3].text = f"{s['participacao_pct']}%"

    titulo("Folha de Pagamento")
    folha = diag["folha"]
    labels = {"docente": "Professores e Auxiliares",
              "coordenacao": "Coordenação e Supervisão",
              "administrativo": "Administrativo"}
    linhas = []
    for k in ["docente", "coordenacao", "administrativo"]:
        c = folha["por_categoria"][k]
        linhas.append((labels[k], f"{brl(c['salario_bruto'])}  (+enc. {brl(c['encargos'])})"))
    linhas.append(("Custo total da folha / mês", brl(folha["totais"]["custo_total_mensal"])))
    tabela(linhas, destaque_ultima=True)

    titulo("Tributos")
    tr = diag["tributos"]
    tabela([
        ("Regime", meta["regime"].title()),
        ("Carga efetiva sobre a receita", pct(tr["carga_efetiva_sobre_receita"])),
        ("Tributos sobre a receita / mês", brl(tr["total_sobre_receita"])),
        ("INSS patronal sobre a folha", pct(tr["inss_patronal_pct"])),
    ])

    titulo("DRE — Demonstrativo de Resultado (mês)")
    tabela(_linhas_dre(diag))

    titulo("Custo por Aluno")
    t = doc.add_table(rows=1, cols=4)
    t.style = "Light Grid Accent 1"
    hdr = t.rows[0].cells
    for i, h in enumerate(["Nível", "Alunos", "Custo/aluno (mês)", "Resultado"]):
        hdr[i].text = h
    for n, v in diag["dre"]["por_nivel"].items():
        c = t.add_row().cells
        c[0].text = n
        c[1].text = str(v["alunos"])
        c[2].text = brl(v["custo_por_aluno_mes"])
        c[3].text = brl(v["resultado"])

    titulo("Análise SWOT")
    sw = diag["swot"]
    doc.add_paragraph(f"Posição estratégica: {sw['postura']}").runs[0].bold = True
    tabela([
        ("Forças", f"{sw['scores']['forca']}"),
        ("Fraquezas", f"{sw['scores']['fraqueza']}"),
        ("Oportunidades", f"{sw['scores']['oportunidade']}"),
        ("Ameaças", f"{sw['scores']['ameaca']}"),
        ("Eixo interno (Forças − Fraquezas)", f"{sw['eixo_interno']}"),
        ("Eixo externo (Oportunidades − Ameaças)", f"{sw['eixo_externo']}"),
    ])
    doc.add_paragraph(sw["recomendacao"])

    doc.save(caminho)
    return caminho


# ----------------------------------------------------------------- PPTX
def gerar_pptx(diag: dict, caminho: str) -> str:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    meta = diag["meta"]
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    branco = prs.slide_layouts[6]  # em branco

    def slide_titulo(titulo_txt, sub=""):
        s = prs.slides.add_slide(branco)
        # faixa superior
        faixa = s.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(1.1))
        faixa.fill.solid()
        faixa.fill.fore_color.rgb = RGBColor(*AZUL)
        faixa.line.fill.background()
        tx = faixa.text_frame
        tx.text = titulo_txt
        tx.paragraphs[0].font.size = Pt(28)
        tx.paragraphs[0].font.bold = True
        tx.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        tx.margin_left = Inches(0.4)
        if sub:
            cx = s.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(12), Inches(0.5))
            cx.text_frame.text = sub
            cx.text_frame.paragraphs[0].font.size = Pt(14)
            cx.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x5B, 0x66, 0x75)
        return s

    def tabela_slide(s, linhas, top=Inches(1.5), col_w=(Inches(7.5), Inches(4.5))):
        rows = len(linhas)
        tbl = s.shapes.add_table(rows, 2, Inches(0.6), top,
                                 col_w[0] + col_w[1], Inches(0.4) * rows).table
        tbl.columns[0].width = col_w[0]
        tbl.columns[1].width = col_w[1]
        for i, (a, b) in enumerate(linhas):
            for j, val in enumerate((a, b)):
                cell = tbl.cell(i, j)
                cell.text = val
                p = cell.text_frame.paragraphs[0]
                p.font.size = Pt(13)
                if a.startswith("(=)"):
                    p.font.bold = True
                if j == 1:
                    p.alignment = PP_ALIGN.RIGHT
        return tbl

    # Capa
    capa = prs.slides.add_slide(branco)
    fundo = capa.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    fundo.fill.solid()
    fundo.fill.fore_color.rgb = RGBColor(*AZUL)
    fundo.line.fill.background()
    tb = capa.shapes.add_textbox(Inches(1), Inches(2.6), Inches(11.3), Inches(2))
    tf = tb.text_frame
    tf.text = "Diagnóstico Econômico-Financeiro"
    tf.paragraphs[0].font.size = Pt(40)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    p2 = tf.add_paragraph()
    p2.text = f"{meta['escola']}  ·  {meta['ano']}"
    p2.font.size = Pt(22)
    p2.font.color.rgb = RGBColor(0xCF, 0xDA, 0xE8)

    s = slide_titulo("Resumo Executivo")
    tabela_slide(s, _resumo(diag))

    s = slide_titulo("Folha de Pagamento")
    folha = diag["folha"]
    labels = {"docente": "Professores e Auxiliares",
              "coordenacao": "Coordenação e Supervisão",
              "administrativo": "Administrativo"}
    lf = [(labels[k], brl(folha["por_categoria"][k]["custo_total"]))
          for k in ["docente", "coordenacao", "administrativo"]]
    lf.append(("(=) Custo total da folha / mês", brl(folha["totais"]["custo_total_mensal"])))
    tabela_slide(s, lf)

    s = slide_titulo("DRE — Demonstrativo de Resultado (mês)")
    tabela_slide(s, _linhas_dre(diag)[:10])

    s = slide_titulo("Custo por Aluno")
    cpa = [(n, brl(v["custo_por_aluno_mes"])) for n, v in diag["dre"]["por_nivel"].items()]
    tabela_slide(s, cpa)

    sw = diag["swot"]
    s = slide_titulo("Análise SWOT", sub=f"Posição: {sw['postura']}")
    tabela_slide(s, [
        ("Forças", str(sw["scores"]["forca"])),
        ("Fraquezas", str(sw["scores"]["fraqueza"])),
        ("Oportunidades", str(sw["scores"]["oportunidade"])),
        ("Ameaças", str(sw["scores"]["ameaca"])),
    ])
    cx = s.shapes.add_textbox(Inches(0.6), Inches(5.0), Inches(12), Inches(1.5))
    cx.text_frame.word_wrap = True
    cx.text_frame.text = sw["recomendacao"]
    cx.text_frame.paragraphs[0].font.size = Pt(14)

    prs.save(caminho)
    return caminho


# ----------------------------------------------------------------- PDF
def gerar_pdf(diag: dict, caminho: str) -> str:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    meta = diag["meta"]
    styles = getSampleStyleSheet()
    azul = colors.Color(*[c / 255 for c in AZUL])
    h = ParagraphStyle("h", parent=styles["Heading1"], textColor=azul, fontSize=20)
    sub = ParagraphStyle("s", parent=styles["Normal"], fontSize=12, textColor=colors.grey)

    doc = SimpleDocTemplate(caminho, pagesize=landscape(A4),
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.2 * cm)
    elems = []

    def bloco(titulo_txt, linhas, larguras=(12 * cm, 8 * cm)):
        elems.append(Paragraph(titulo_txt, h))
        elems.append(Spacer(1, 8))
        data = [[a, b] for a, b in linhas]
        t = Table(data, colWidths=list(larguras))
        ts = [
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 0.99)]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.Color(0.88, 0.9, 0.93)),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        for i, (a, _) in enumerate(linhas):
            if a.startswith("(="):
                ts.append(("FONTNAME", (0, i), (-1, i), "Helvetica-Bold"))
                ts.append(("BACKGROUND", (0, i), (-1, i), colors.Color(0.93, 0.96, 0.93)))
        t.setStyle(TableStyle(ts))
        elems.append(t)
        elems.append(PageBreak())

    # Capa
    elems.append(Spacer(1, 5 * cm))
    elems.append(Paragraph("Diagnóstico Econômico-Financeiro",
                           ParagraphStyle("capa", parent=h, fontSize=34, alignment=1)))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph(f"{meta['escola']} · {meta['ano']}",
                           ParagraphStyle("capa2", parent=sub, fontSize=18, alignment=1)))
    elems.append(Paragraph(
        f"Regime: {meta['regime'].title()} · Emitido em {meta['data_geracao']}",
        ParagraphStyle("capa3", parent=sub, alignment=1)))
    elems.append(PageBreak())

    bloco("Resumo Executivo", _resumo(diag))

    seg = [("Nível", "Receita bruta")]
    seg += [(s["nome"], brl(s["receita_bruta"])) for s in diag["receitas"]["segmentos"]]
    bloco("Receitas por nível", seg)

    folha = diag["folha"]
    labels = {"docente": "Professores e Auxiliares",
              "coordenacao": "Coordenação e Supervisão",
              "administrativo": "Administrativo"}
    lf = [(labels[k], brl(folha["por_categoria"][k]["custo_total"]))
          for k in ["docente", "coordenacao", "administrativo"]]
    lf.append(("(=) Custo total da folha / mês", brl(folha["totais"]["custo_total_mensal"])))
    bloco("Folha de Pagamento", lf)

    bloco("DRE — Demonstrativo de Resultado (mês)", _linhas_dre(diag))

    cpa = [("Nível", "Custo/aluno (mês)")]
    cpa += [(n, brl(v["custo_por_aluno_mes"])) for n, v in diag["dre"]["por_nivel"].items()]
    bloco("Custo por Aluno", cpa)

    sw = diag["swot"]
    swot_linhas = [
        ("Posição estratégica", sw["postura"]),
        ("Forças", str(sw["scores"]["forca"])),
        ("Fraquezas", str(sw["scores"]["fraqueza"])),
        ("Oportunidades", str(sw["scores"]["oportunidade"])),
        ("Ameaças", str(sw["scores"]["ameaca"])),
    ]
    elems.append(Paragraph("Análise SWOT", h))
    elems.append(Spacer(1, 8))
    t = Table([[a, b] for a, b in swot_linhas], colWidths=[12 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 0.99)]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 12))
    elems.append(Paragraph(sw["recomendacao"], styles["Normal"]))

    doc.build(elems)
    return caminho
