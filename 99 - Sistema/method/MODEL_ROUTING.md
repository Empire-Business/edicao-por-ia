# Roteamento de modelos — v1.6

Consulte `method/EXECUTION_AND_COSTS.md` antes de gastar. O nome de um agente não comprova qual modelo foi usado.

## Primeiro: precisa de modelo?
Probe, hash, extração, transcrição local, silêncio, cortes, retiming, render e composição usam ferramentas locais. A conversa do coordenador ainda consome uso. Reaplicar componente JS aprovado com novos dados não pede novo projeto ao modelo.

## Três papéis, duas configurações
- **Triagem:** filtrar trechos de transcrição, classificar candidatos óbvios, trabalhar com metadados curtos. Não arbitrar mudança de sentido ou julgar imagem que não recebeu.
- **Edição padrão:** comparar fala/roteiro, escolher takes claros, planejar EDL e revisar cortes; adaptar código aprovado.
- **Direção complexa:** novo componente de animação, ambiguidade semântica importante, linguagem visual nova. Perfil econômico/equilibrado pede autorização para subir. No elaborado, essa capacidade está prevista, mas orçamento e consentimento continuam obrigatórios.

`config/model-catalog.json` tem candidatos consultados em documentação oficial. **Não são prova de disponibilidade ou de preço na conta.** Claude usa aliases da família Haiku/Sonnet/Opus; Codex tem modelos próprios configurados em TOML. Use o seletor do host para conferir modelo/esforço e registre a confirmação com `model-bind`; atualize subagentes com `setup`.

## Nativo versus controlado
Agentes nativos recebem um pacote restrito ao formato/vídeo atual. Sete papéis existem nos dois hosts. Eles retornam decisões ou código para o coordenador; não escrevem memória, não instalam, não compram e não delegam em cascata.

No modo controlado, `run` despacha apenas texto/código via CLI. Não alegue ter executado visão, rastreamento, geração de imagem ou edição apenas porque um worker devolveu uma proposta.

Prefira resolver sem delegar quando a resposta já consta do contexto ou de um comando local. Delegação tem custo adicional. Não chamar os sete papéis por obrigação.

## Falha e indisponibilidade
Pare se o modelo não existir, a conta limitar uso ou um parâmetro não for suportado. Nunca migrar de assinatura para API nem trocar de provedor sem autorização. Reavaliar o vínculo após 30 dias no executor. Ajustar modelos é uma configuração, não refazer o método.
