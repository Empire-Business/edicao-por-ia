# Revisão v1.3.0 — animações JavaScript

## Escopo
Entrada: claude-video-factory-v1.2.0.zip. Não foram recebidas gravações ou mídias de cliente nesta revisão. Fontes originais permanecem no pacote; apenas caches Python antigos foram excluídos. Presets de vídeo v1/v2 preservados byte a byte relativamente ao ZIP de entrada.

O uso de animações em JavaScript deixou de ser uma menção opcional genérica: há política, fluxo, regras de modelos, quatro componentes reutilizáveis, render leve local, composição e testes. Novos efeitos complexos podem usar Opus desde a criação; reutilização usa props locais/Sonnet. O render não faz chamadas de modelo.

## Implementado
- Componente JS/SVG puro e determinístico por frame: frase, passos, identificação e print.
- Render via Playwright/Chromium, sem rede, com frames PNG transparentes e hash.
- Compositor FFmpeg com tempo em frames da montagem final; preserva áudio e duração; rejeita versões desatualizadas, arquivo sobrescrito e mistura de filhos.
- Plano e exemplos parametrizados; workflow alinhado ao roteiro, cortes de fala, silêncio e assets já previstos.
- Subagentes e skill manual de motion; não se afirma que esses arquivos troquem modelos automaticamente fora do Claude Code.
- Adapter React/Remotion e instruções de instalação explícita. Não foi instalado/testado nesta construção.

## Verificações executadas nesta revisão
- 20 testes JavaScript: 20 passaram.
- 53 testes Python: 53 passaram (37 regressões anteriores + 16 novos testes do plano de motion).
- 19 verificações de integração com JS real, navegador e FFmpeg: 19 passaram. Vídeo sintético; transparência, determinismo no mesmo ambiente, períodos de entrada/saída, hash de imagem, mesma duração/fps/geometria, áudio preservado, fonte intacta e fonte sem áudio.
- Regressão integrada roteiro/silêncio: executada novamente, 16 checks passaram.
- Smoke original: executado novamente, 6 checks passaram.
- Inspeção visual de frames do efeito e do resultado composto, com exemplos em geometria horizontal e vertical. Isso NÃO equivale a aprovação de marca/semântica em uma gravação real.
- Verificador estrutural/sintático/integridade executado; resultado acompanha o pacote.

## Problema encontrado e corrigido
No primeiro teste composto, a negociação automática de fps deixou a duração da faixa de vídeo um frame menor, apesar de a contagem de frames estar correta. O export agora força a taxa constante da montagem; duração e fps são verificados no teste final. O teste de pixels admite pequena diferença de re-encoding, mas rejeita overlays fora da janela.

## Pendências e limites
Não houve chamada real ao Claude/Opus; não se mediu superioridade artística de modelo ou percentual de economia de tokens. Não houve gravação real de cliente, ASR real, avaliação de timing semântico pelo agente, teste no Mac/Windows ou aprovação humana do movimento completo em reprodução. Efeitos complexos/3D precisam de implementação e QA próprios.

A tentativa de consultar o registry npm falhou por DNS (EAI_AGAIN). O adapter Remotion é fornecido como caminho opcional de código, não como instalação ou integração homologada. A rota JS/browser/FFmpeg foi executada de fato. Não há node_modules, credenciais, fontes comerciais ou mídias privadas incluídas.

## Uso
Extraia em uma pasta nova. Preserve os seus jobs, contexto e padrões aprovados. Leia START-HERE.md e motion/README.md. Só autorize instalações quando a checagem indicar uma dependência necessária. Invoque a skill com a intenção visual em linguagem comum; o agente deve conduzir até um render revisado, não entregar apenas código.
