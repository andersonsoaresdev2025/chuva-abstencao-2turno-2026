# Documento de Instruções do Projeto
## Chuva × Abstenção Eleitoral – Segundo Turno 2026
**Versão 2.0 | 25 de outubro de 2026 – 06:40 BRT**

### 1. Sumário Executivo
Projeto de monitoramento em tempo real do impacto potencial das chuvas (incluindo tempestades, chuvas torrenciais e risco de alagamentos) sobre a abstenção no segundo turno das eleições de 25/10/2026 (Flávio Bolsonaro × Lula).

**Status atual (06:40 BRT):** Dados essenciais coletados, análises dos Bots 0–4 concluídas em versão utilizável, dashboard Streamlit funcional. Foco agora na publicação e atualização contínua durante o dia.

Todas as informações essenciais estão disponíveis desde antes das **08h00**.

Entregáveis:
- Dashboard público interativo e didático (Streamlit pronto)
- Site de acompanhamento (GitHub Pages a publicar)
- Código aberto no GitHub
- MCP focado em risco climático × abstenção

### 2. Objetivos
1. Quantificar a correlação entre precipitação no dia da eleição e abstenção (literatura + 1º turno 2026 + histórico). **Status: Concluído (Bot 1).**
2. Classificar o risco de chuva durante o horário de votação (08h–17h) em três níveis. **Status: Concluído e atualizado (Bot 2).**
3. Mapear os redutos eleitorais de cada candidato no 1º turno. **Status: Concluído (Bot 3).**
4. Estimar o impacto diferencial da chuva sobre a abstenção e sobre cada candidato. **Status: Versão 1.1 pronta (Bot 4).**

### 3. Arquitetura dos Bots
- **Bot 0** – Aquisição e Organização de Dados (TSE, clima histórico, geo, previsões) → **Dados essenciais disponíveis.**
- **Bot 1** – Correlação Científica e Histórica → **Síntese e coeficientes prontos.**
- **Bot 2** – Monitoramento Meteorológico em Tempo Real → **Classificação a/b/c atualizada.**
- **Bot 3** – Redutos Eleitorais do 1º Turno → **Rankings e arquivos CSV prontos.**
- **Bot 4** – Impacto Diferencial e Síntese → **Síntese executiva e tabelas de impacto prontas.**

### 4. Classificação de Risco de Chuva (padrão do projeto)
- **a) Torrencial / Tempestade / Risco de alagamento** (≥ 20–30 mm ou alertas)
- **b) Moderada** (5–20/30 mm)
- **c) Sem chuva relevante** (< 5 mm)

**Situação atual (manhã de 25/10):** Risco alto (a) concentrado em Grande São Paulo, RJ, Campinas, Curitiba, Campo Grande. Norte/Nordeste firmes.

### 5. Escopo Geográfico
Sempre apresentar resultados por:
- Município (priorizar os maiores colégios eleitorais)
- Unidade da Federação
- Grande Região (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)

### 6. Stack e Hospedagem
- Dashboard: Streamlit (recomendação principal). Código em `/dashboard/` (app.py + requirements.txt). Pronto para `streamlit run app.py` e deploy em Streamlit Community Cloud.
- Site: GitHub Pages (versão estática resumida).
- Repositório: GitHub (código + dados processados + MCP).

### 7. MCP
Foco exclusivo em:
- Risco de chuva, tempestades e alagamentos
- Impacto estimado sobre a mobilidade do eleitor e abstenção
- Consultas por município, estado ou região

### 8. Regras Gerais de Trabalho dos Bots
- Autonomia total de navegação e download.
- Registrar sempre origem e timestamp dos dados.
- Transparência máxima: declarar limitações e incerteza.
- Priorizar os maiores colégios eleitorais quando o tempo for escasso.
- Toda saída deve ser estruturada (CSV/JSON) + resumo executivo em Markdown.

### 9. Prazo Crítico e Status de Dados
Dados base e primeiras análises disponíveis **antes das 08h00**. Atualizações contínuas de clima e impacto durante o dia.

**Arquivos-chave disponíveis em `/data/`:**
- TSE 1º turno (votação e abstenção por município)
- Previsões com classificação de risco
- Redutos eleitorais
- Coeficientes e síntese de correlação
- Impacto diferencial (municípios prioritários, estados, regiões)
- Dashboard Streamlit

### 10. Evolução do Documento
Este documento é vivo. Versão 2.0 reflete o estado pós-coleta e análises iniciais. Novas versões serão geradas conforme atualizações de previsão e resultados reais.

### 11. Próximos Passos Imediatos
1. Publicar o dashboard Streamlit (Community Cloud ou similar).
2. Preparar e publicar site estático no GitHub Pages.
3. Inicializar repositório GitHub com código, dados processados e README.
4. Configurar MCP básico para consultas de risco e impacto.
5. Manter Bot 2 atualizando risco de chuva durante o dia e Bot 4 recalibrando impacto se necessário.

---
**Fim do Documento de Instruções – Versão 2.0**
