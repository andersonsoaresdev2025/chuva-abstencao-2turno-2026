# Documento de Instruções do Projeto
## Chuva × Abstenção Eleitoral – Segundo Turno 2026
**Versão 2.2 | 25 de outubro de 2026 – 06:38 BRT**

### 1. Sumário Executivo
Projeto de monitoramento em tempo real do impacto potencial das chuvas (incluindo tempestades, chuvas torrenciais e risco de alagamentos) sobre a abstenção no segundo turno das eleições de 25/10/2026 (Flávio Bolsonaro × Lula).

**Status atual:** Dados essenciais coletados, análises dos Bots 0–4 concluídas em versão utilizável, dashboard Streamlit funcional. Foco agora na publicação, atualização contínua e monitoramento de redes sociais (X + locais) para notícias e previsões.

Todas as informações essenciais estão disponíveis desde antes das **08h00**.

Entregáveis:
- Dashboard público interativo e didático (Streamlit pronto)
- Site de acompanhamento (GitHub Pages a publicar)
- Código aberto no GitHub
- MCP focado em risco climático × abstenção
- Monitoramento de redes sociais (X e fontes locais) para notícias, alertas e relatos de chuva/alagamento

### 2. Objetivos
1. Quantificar a correlação entre precipitação no dia da eleição e abstenção (literatura + 1º turno 2026 + histórico). **Status: Concluído (Bot 1).**
2. Classificar o risco de chuva durante o horário de votação (08h–17h) em três níveis. **Status: Concluído e atualizado (Bot 2).**
3. Mapear os redutos eleitorais de cada candidato no 1º turno. **Status: Concluído (Bot 3).**
4. Estimar o impacto diferencial da chuva sobre a abstenção e sobre cada candidato. **Status: Versão 1.1 pronta (Bot 4).**
5. Incorporar sinais em tempo real de redes sociais (X e monitoramento local) para complementar as fontes meteorológicas oficiais.

### 3. Arquitetura dos Bots
- **Bot 0** – Aquisição e Organização de Dados → **Dados essenciais disponíveis.**
- **Bot 1** – Correlação Científica e Histórica → **Síntese e coeficientes prontos.**
- **Bot 2** – Monitoramento Meteorológico em Tempo Real → **Classificação a/b/c atualizada.**
- **Bot 3** – Redutos Eleitorais do 1º Turno → **Rankings e arquivos CSV prontos.**
- **Bot 4** – Impacto Diferencial e Síntese → **Síntese executiva e tabelas de impacto prontas.**
- **Monitoramento de Redes Sociais** – Coleta contínua de posts e relatos relevantes sobre chuva, alertas, alagamentos e impacto na votação (X prioritário + fontes locais públicas via busca e navegação).

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
- Dashboard: Streamlit (recomendação principal). Código em `/dashboard/`. Pronto para deploy.
- Site: GitHub Pages (versão estática resumida).
- Repositório: GitHub (código + dados processados + MCP).
- Monitoramento social: X (busca nativa por palavras-chave e semântica) + navegação/busca em fontes locais públicas (portais de notícias regionais, relatos públicos).

### 7. MCP
Foco exclusivo em:
- Risco de chuva, tempestades e alagamentos
- Impacto estimado sobre a mobilidade do eleitor e abstenção
- Consultas por município, estado ou região
- (Opcional) Sinais recentes de redes sociais sobre condições locais

### 8. Regras Gerais de Trabalho dos Bots
- Autonomia total de navegação e download.
- Registrar sempre origem e timestamp dos dados.
- Transparência máxima: declarar limitações e incerteza.
- Priorizar os maiores colégios eleitorais quando o tempo for escasso.
- Toda saída deve ser estruturada (CSV/JSON) + resumo executivo em Markdown.
- Conteúdo de redes sociais deve ser filtrado por relevância e fonte (preferir contas verificadas, meteorologistas, veículos e relatos locais consistentes). Evitar desinformação.

### 9. Prazo Crítico e Status de Dados
Dados base e primeiras análises disponíveis **antes das 08h00**. Atualizações contínuas de clima, impacto e sinais sociais durante o dia.

**Arquivos-chave disponíveis em `/data/`:**
- TSE 1º turno
- Previsões com classificação de risco
- Redutos eleitorais
- Coeficientes e síntese de correlação
- Impacto diferencial
- Dashboard Streamlit

### 10. Evolução do Documento
Versão 2.2 adiciona monitoramento de redes sociais locais (além do X). Documento vivo.

### 11. Próximos Passos Imediatos
1. Publicar o dashboard Streamlit.
2. Preparar e publicar site estático no GitHub Pages.
3. Inicializar repositório GitHub.
4. Configurar MCP básico.
5. Integrar monitoramento contínuo de redes sociais (X + fontes locais) para alertas de chuva e mobilidade.
6. Manter atualizações de risco e impacto durante o dia.

---
**Fim do Documento de Instruções – Versão 2.2**
