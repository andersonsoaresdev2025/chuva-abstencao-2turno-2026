# Resumo Executivo – Risco de Chuva × Abstenção  
**Bot 2 – Monitoramento Meteorológico em Tempo Real**  
**Data:** 25 de outubro de 2026  
**Horário da última atualização:** 06:35 BRT  
**Janela analisada:** 08h–17h (horário de votação)  
**Status:** Atualização pré-abertura das urnas

---

## 1. Situação atual (06:35 BRT)

**Chuva já em curso em São Paulo** (HeavyRain confirmado).  
Alertas do **INMET** ativos para tempestade em:

- São Paulo (capital + várias regiões)
- Rio de Janeiro (Região Metropolitana e Baixada)
- Campo Grande (MS)
- Curitiba e norte do Paraná
- Campinas e outras cidades paulistas

O risco de alagamento e dificuldade de mobilidade é **real e imediato** nos maiores colégios do Centro-Sul.

---

## 2. Onde está o maior risco de chuva forte

| Nível | Áreas principais | Observação |
|-------|------------------|------------|
| **a** | Grande São Paulo, Campinas, Região Metropolitana do RJ, Campo Grande (MS), Curitiba e norte do PR | Alertas INMET ativos. Chuva forte / tempestades. Risco de alagamento. |
| **b** | Porto Alegre, partes de SC, sul de MG, interior de SP | Chuva moderada isolada. |
| **c** | Todo o Norte e Nordeste + DF, GO, MT | Tempo firme. Sem impacto relevante por chuva. |

---

## 3. Maiores colégios eleitorais mais afetados (prioridade dashboard)

| Município                  | Eleitorado aprox. | Nível | Precip. estimada (08-17h) | Situação |
|----------------------------|-------------------|-------|---------------------------|----------|
| **São Paulo (SP)**        | 9,1 milhões      | **a** | 30–40 mm+                | Chuva forte desde a madrugada. ALERTA INMET. |
| **Rio de Janeiro (RJ)**   | 4,9 milhões      | **a** | ~25–30 mm                | ALERTA INMET. Risco de temporais. |
| **Guarulhos (SP)**        | 949 mil          | **a** | ~35–40 mm                | Volume elevado. Alto risco de alagamento. |
| **Campinas (SP)**         | 874 mil          | **a** | ~20–25 mm                | ALERTA INMET. |
| **São Bernardo do Campo** | 627 mil          | **a** | ~25–30 mm                | Grande ABC sob instabilidade. |
| **São Gonçalo (RJ)**      | 653 mil          | **a** | ~25 mm                   | Baixada Fluminense. |
| **Campo Grande (MS)**     | 641 mil          | **a** | ~20–25 mm                | ALERTA INMET. Temporal à tarde. |
| **Curitiba (PR)**         | 1,4 milhão       | **a** | ~15–20 mm                | ALERTA INMET. |
| **Porto Alegre (RS)**     | 1,1 milhão       | **b** | ~8–10 mm                 | Chuva moderada. |
| **Belo Horizonte (MG)**   | 2,0 milhões      | **b** | ~4–6 mm                  | Chuva isolada. |

**Eleitorado sob risco nível a (estimativa prioritária):** > 18 milhões de eleitores.

---

## 4. Resumo por Grande Região

| Região        | Nível | Avaliação |
|---------------|-------|-----------|
| **Sudeste**   | **a** | SP e RJ sob alerta INMET. Maior impacto esperado na abstenção. |
| **Sul**       | **a/b** | PR sob alerta de tempestade. RS e SC com chuva moderada. |
| **Centro-Oeste** | **a/b** | MS (Campo Grande) sob alerta. Demais estados firmes. |
| **Nordeste**  | **c** | Tempo firme. |
| **Norte**     | **c** | Pancadas isoladas sem relevância. |

---

## 5. Fontes e transparência

- **Fontes principais:** Open-Meteo (modelos de alta resolução) + Alertas oficiais do INMET (confirmados às 06h)
- **Fontes complementares:** Climatempo, G1, Defesa Civil SP
- **Classificação:** Padrão do projeto (a = ≥20–30 mm ou alerta de tempestade/alagamento; b = 5–20/30 mm; c = <5 mm)
- **Limitação:** Volumes locais podem variar. Alertas oficiais foram priorizados sobre estimativas de modelo quando divergentes.

---

## 6. Arquivos atualizados (prontos para dashboard)

Local: `/home/workdir/artifacts/data/clima/previsoes_2026-10-25/`

- `risco_chuva_municipios.csv` (29 municípios prioritários)
- `risco_chuva_estados.csv`
- `risco_chuva_regioes.csv`
- `resumo_executivo.md` (este arquivo)

**Próxima atualização:** entre 07h30 e 08h00, e depois a cada 1–2 horas ou quando houver mudança significativa.

---

**Bot 2 – Monitoramento Meteorológico em Tempo Real**  
Projeto Chuva × Abstenção Eleitoral – Segundo Turno 2026  
**Atualização pré-08h00 concluída.**
