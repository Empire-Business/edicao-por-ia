# Organização física

A raiz apresenta seis itens: guia, gravações, entregas, ajuda, formatos e este sistema.
O motor e seus dados foram movidos fisicamente para esta pasta. Os registros de formatos mantêm o caminho relativo `context/clients/`, os mesmos arquivos e esquemas. O ledger de orçamento e checkpoints mantém o caminho relativo `.factory/`.

Gravações e entregas são pastas reais na raiz. Os formatos são pastas de identificação; o usuário pede cadastro e edição pelo Claude. A fonte de verdade das preferências continua nos bancos existentes.

`motion/projetos/tutorial-omnx-sell` guarda o tutorial. `motion/LEIA-ME.md` distingue motores, componentes, exemplos e projetos. Protótipos ficam em `prototipos/`; entregas antigas e navegação anterior, em `arquivo/`.

Compatibilidade: acessos antigos locais são links ocultos, sem cópias de dados. Os caminhos canônicos novos e as ferramentas de cadastro/controle funcionam sem esses links; testes de migração os desativam. `tools/project_layout.py` traduz referências absolutas antigas ao ler, preservando o conteúdo e hashes das evidências. A identidade anterior também é considerada ao procurar lotes, sem duplicar pedidos nem reiniciar gastos.

Arquivos de entrada dos agentes permanecem na raiz por descoberta automática. As configurações nativas e o ambiente Python existente permanecem ali. As proteções contra escrita por symlink não foram removidas; as ferramentas escrevem no motor real. No Mac, apenas os pontos de entrada e links de compatibilidade são ocultos. Há também uma lista `.hidden` para gerenciadores de arquivos que a respeitam. Não há alteração de permissões de execução, autenticação ou acesso a segredos.

Recibos: `.factory/structure-migration.json`, `.factory/layout.json` e `.factory/navigation/physical-integrity.json`. A recuperação move apenas caminhos registrados e recusa sobrescrever alterações posteriores. Windows/Linux não foram testados em máquinas reais.

O backup Git não inclui demonstrações renderizadas ou modelos da pasta privada de formatos. Verifique uma cópia de código com `tools/verify_package.py --installed --repository`; o pacote completo mantém a verificação normal. As mídias sintéticas dos testes são geradas temporariamente.
