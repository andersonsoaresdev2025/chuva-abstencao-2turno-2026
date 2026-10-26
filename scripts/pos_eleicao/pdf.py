"""Pós-eleição, passo 3: PDF do relatório (markdown + weasyprint)."""
import markdown, weasyprint
from pathlib import Path as _P
import os as _os
ROOT=_P(__file__).resolve().parents[2]
OUT=ROOT/"data"/"resultado_2turno"
_os.chdir(OUT)  # entradas em tse_2t/, saídas nesta pasta
md=open("comparacao_municipios_2turno.md").read()
html=markdown.markdown(md,extensions=["tables"])
css="""@page{size:A4;margin:14mm 12mm} body{font-family:'DejaVu Sans',sans-serif;font-size:9pt;line-height:1.35}
h1{font-size:15pt;color:#12324f}h2{font-size:12pt;color:#12324f;border-bottom:1px solid #ccc;margin-top:16px}h3{font-size:10.5pt}
table{border-collapse:collapse;margin:6px 0;font-size:7.4pt;width:100%}th,td{border:1px solid #bbb;padding:2px 4px;text-align:left}th{background:#eef2f6}
img{max-width:100%;page-break-inside:avoid}blockquote{border-left:3px solid #c0392b;margin:6px 0;padding:2px 8px;background:#fbeeee}code{font-size:8pt}"""
weasyprint.HTML(string=f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{html}</body></html>",base_url=".").write_pdf("comparacao_municipios_2turno.pdf")
