# Monitoramento de notícias — chuva × eleição (2º turno, 25/10/2026)

Manchetes de portais nacionais e locais sobre chuva/tempo severo e seus efeitos na votação
(locais de votação transferidos, alagamentos, mobilidade, alertas, abstenção).

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `portais.csv` | Portais monitorados (nacionais e regionais das áreas com risco de chuva). Só entram URLs verificadas (HTTP 200) — coluna `verificado_em_utc`. `rss_url` preenchido só quando o feed foi testado e retornou itens. |
| `noticias_<AAAAMMDD_HHMM>UTC.csv` | Notícias relevantes de uma coleta. |
| `noticias_consolidado.csv` | Todas as coletas, deduplicadas (URL + similaridade de título), por relevância. É o arquivo lido pelo dashboard e pelo site. |
| `resumo_noticias.md` | Resumo legível da última coleta (top notícias, distribuição, sinalizados, falhas). |
| `log_coleta.csv` | Por coleta e por fonte: itens lidos, relevantes, erros. |

Colunas de notícia: `titulo, link, portal, dominio, abrangencia (nacional/regional/outro), uf, cidade, regiao,
tema (locais de votação/abstenção/alagamento/mobilidade/alerta/geral), publicado_brt, publicado_utc,
coletado_utc, score (relevância), sinalizacao, menciona_eleicao, origem_coleta, resumo`.

## Como é coletado (`scripts/coletar_noticias.py`)

1. Feeds RSS verificados de `portais.csv`;
2. Google Notícias RSS (pt-BR): buscas temáticas (“chuva eleição”, “alagamento local de votação”,
   “chuva abstenção”…), por cidade sinalizada e `site:` para portais sem RSS.
3. Janela: publicados em 25/10/2026 (BRT) ou a partir de 24/10 18h BRT.
4. Filtro: menção a chuva/tempo severo **e** a eleição; ou chuva forte em área sinalizada no dia 25/10.
5. Sinalização (⚠️): fonte fora da lista verificada; alegações que contradizem fontes oficiais
   (ex.: “eleição adiada”) — esses itens não entram no quadro “Principais notícias agora”.
Nada é inventado: só itens efetivamente baixados dos feeds entram nos arquivos.

## Rodar de novo (de hora em hora)

Só coletar:

```bash
cd ~/projeto_chuva_abstencao_2026 && .venv/bin/python scripts/coletar_noticias.py
```

Coletar **e publicar** (site + dashboard via push no `main`) — comando único usado na rotina horária:

```bash
cd ~/projeto_chuva_abstencao_2026 && scripts/update_and_publish.sh
```

(`update_and_publish.sh` roda a coleta antes do build; use `COLETAR_NOTICIAS=0` para pular.)
Exemplo de cron horário 08h–18h BRT (11–21 UTC): `0 11-21 25 10 * cd ~/projeto_chuva_abstencao_2026 && scripts/update_and_publish.sh >> /tmp/noticias.log 2>&1`

## Limitações

- Links do Google Notícias passam por um redirecionamento `news.google.com` até o portal.
- Paywall em Folha, Estadão, O Globo, Gazeta do Povo e GZH: título público, texto pode não ser.
- Sem RSS funcional verificado: Band, R7, Clique Paraná, Correio do Estado, A Tribuna (Santos), GZH,
  Correio do Povo, Estado de Minas, O Tempo (cobertos via Google Notícias `site:`). Midiamax não respondeu
  na verificação e ficou fora da lista.
- Tema/cidade/UF são classificados por palavras-chave; podem errar (ex.: portal nacional sem cidade).
- Notícia não é dado oficial de comparecimento; abstenção oficial só na totalização do TSE.
