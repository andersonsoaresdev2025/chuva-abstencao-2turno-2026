# Documento de Instruções do Projeto
## Chuva × Abstenção Eleitoral – Segundo Turno 2026
**Versão 1.1 | 25 de outubro de 2026**

### 1. Sumário Executivo
Projeto de monitoramento em tempo real do impacto potencial das chuvas (incluindo tempestades, chuvas torrenciais e risco de alagamentos) sobre a abstenção no segundo turno das eleições de 25/10/2026 (Flávio Bolsonaro × Lula).

Todas as informações essenciais devem estar disponíveis a partir das **08h00** (horário de Brasília).

Entregáveis:
- Dashboard público interativo e didático
- Site de acompanhamento
- Código aberto no GitHub
- MCP focado em risco climático × abstenção

### 2. Objetivos
1. Quantificar a correlação entre precipitação no dia da eleição e abstenção (literatura + 1º turno 2026 + histórico).
2. Classificar o risco de chuva durante o horário de votação (08h–17h) em três níveis.
3. Mapear os redutos eleitorais de cada candidato no 1º turno.
4. Estimar o impacto diferencial da chuva sobre a abstenção e sobre cada candidato.

### 3. Arquitetura dos Bots
- **Bot 0** – Aquisição e Organização de Dados (TSE, clima histórico, geo, previsões)
- **Bot 1** – Correlação Científica e Histórica
- **Bot 2** – Monitoramento Meteorológico em Tempo Real
- **Bot 3** – Redutos Eleitorais do 1º Turno
- **Bot 4** – Impacto Diferencial e Síntese

### 4. Classificação de Risco de Chuva (padrão do projeto)
- **a) Torrencial / Tempestade / Risco de alagamento** (≥ 20–30 mm ou alertas)
- **b) Moderada** (5–20/30 mm)
- **c) Sem chuva relevante** (< 5 mm)

### 5. Escopo Geográfico
Sempre apresentar resultados por:
- Município (priorizar os maiores colégios eleitorais)
- Unidade da Federação
- Grande Região (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)

### 6. Stack e Hospedagem
- Dashboard: priorizar solução de fácil navegação, layout limpo, didático e mobile-friendly (Streamlit é a recomendação principal por velocidade de desenvolvimento e publicação).
- Site: GitHub Pages (gratuito, rápido e alinhado com a publicação do código).
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

### 9. Prazo Crítico
Tudo que for essencial para o acompanhamento do dia deve estar disponível **a partir das 08h00**.

### 10. Evolução do Documento
Este documento é vivo. Novas versões serão geradas conforme o projeto avançar (inclusão de novos dados, mudanças de metodologia, resultados dos bots etc.). Sempre manter o histórico de versões.

### 11. Próximos Passos Imediatos
1. Executar Bot 0 e Bot 2 em paralelo (maior urgência).
2. Em seguida Bot 3 e Bot 1.
3. Bot 4 consolida tudo.
4. Publicar dashboard e site.

---
**Fim do Documento de Instruções – Versão 1.1**