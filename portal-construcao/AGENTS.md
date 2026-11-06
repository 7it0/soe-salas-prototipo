# Instruções do agente — construção do Portal SOE

Versão 1.0 — 06/11/2026. Concepção e coordenação: José Aguiar de Lima Júnior, Especialista em Geoprocessamento — Gabinete/SOE/ANA.

## Escopo e precedência

Estas instruções regem tarefas do Portal SOE que referenciem esta pasta. Não alteram regras superiores do ambiente nem autorizam mudanças no restante do repositório. O Codex descobre AGENTS.md conforme seu diretório de trabalho; se iniciar na raiz, leia explicitamente `portal-construcao/AGENTS.md`. Nunca suponha que o arquivo de uma subpasta foi carregado em qualquer sessão.

Leia `INICIAR_CODEX.md` e as etapas pertinentes de `ROTEIRO_EXECUCAO.md`. O checkpoint de 29/10/2026 é histórico: conferir o estado real antes de escrever. Não ler toda a conversa ou todas as notas hidrológicas para cada tarefa.

## Objetivo e modo de atendimento

Construir e manter o Portal SOE no SharePoint autorizado, aproveitando página, lista e fluxo existentes. O responsável orienta, autentica e aprova; o agente executa as operações disponíveis, salva, reabre e verifica.

Não substituir execução por outro planejamento longo. Não exigir que o usuário opere cada botão ou envie capturas sequenciais quando houver ferramenta de edição. Sem ferramenta, declarar o bloqueio preciso e executar apenas o trabalho independente dele, com dados sintéticos.

Este documento é uma especificação, não um executável, credencial ou consentimento administrativo. Uma permissão de escrita não comprova autorização para publicar. Ter acesso ao GitHub não implica acesso ao Microsoft 365.

## Contrato de execução

1. Identificar cliente local/nuvem, ferramentas, conta, site, ambiente e recursos permitidos. Começar com leitura. Não enumerar documentos de outros sistemas ou áreas.
2. Fazer o usuário autenticar em interface oficial. Não pedir senhas, códigos, cookies ou tokens pelo chat; não extrair sessões do navegador.
3. Obter aprovação do lote: alvo, mudanças, visibilidade, reversão e limites. Dentro do lote aprovado, executar ações reversíveis sem perguntar a cada clique, respeitando confirmações obrigatórias da plataforma.
4. Usar cópia ou ambiente de desenvolvimento com acesso conferido. A página chamada Proposta aparecia publicada; nome ou rascunho não garantem isolamento.
5. Registrar estado anterior e plano de retorno em destino privado aprovado. Não despejar listas, HTML corporativo, IDs, capturas ou exports institucionais neste repositório público.
6. Manter alterações pequenas, idempotentes e restritas ao escopo. Não recriar fluxo ou lista por não localizá-los na primeira tentativa.
7. Após cada escrita, reabrir e conferir. Distinguir ação solicitada, arquivo salvo, recurso persistente, teste aprovado e publicação concluída.
8. Atualizar checkpoint privado antes de mudar de etapa e antes de pausa. Não prometer trabalho futuro fora de uma execução efetivamente iniciada e suportada.

## Operações que exigem aprovação específica

Publicar ou republicar páginas; criar notícia que possa aparecer em outras páginas; tornar página inicial; alterar navegação produtiva, permissões ou compartilhamento; excluir conteúdo; instalar software/extensões; criar registro de aplicativo, credenciais ou consentimentos; ativar rotina recorrente; mudar fonte/periodicidade do fluxo; contratar licença; mover dados para outro serviço.

A conta ou permissão do usuário não substitui políticas Microsoft, OpenAI ou da ANA. Não usar acesso total, desabilitação de controles ou exportação de sessão para contornar bloqueios. SEI fica fora do escopo.

## Arquitetura e qualidade editorial

- Preserve as seções existentes e a identidade institucional aprovada. Não invente logotipos, competências, nomes de servidores, alertas, decisões ou dados hidrológicos.
- Separe notícias próprias, clipping externo e alertas oficiais. Registro em lista não é publicação no componente Notícias.
- Respeite fontes, datas, versão, autoria e classificação. Links do protótipo pessoal mantêm aviso de não publicação institucional.
- Use modelos compartilhados para páginas de unidades e reuniões; valide as siglas vigentes. Não crie sites ou grupos novos sem necessidade e aprovação.
- Não altere as páginas técnicas do acervo, workflows existentes ou configuração global do GitHub como efeito colateral desta tarefa.

## Automação e economia

Preservar inicialmente o acionador RSS de novas publicações. Validar regras com fixtures ou teste separado. Não depender de aguardar notícia para provar o filtro.

Normalizar título/resumo; aplicar regras versionadas; deduplicar por chave estável com proteção concorrente; registrar pendências; exibir apenas itens aprovados até outra decisão formal.

Nenhuma chamada a modelo por notícia no caminho normal. Usar IA somente em construção, manutenção ou exceção autorizada. Não criar agentes de monitoramento contínuo para funções que um fluxo ou script resolve.

O agente desenvolvedor não é o serviço de produção. Após ativação aprovada, o Power Automate ou runtime institucional mantém a rotina com conexões válidas. Não instalar runner pessoal com segredos corporativos neste repositório público.

## Falhas e interrupções

Erros de autenticação/permissão/política: parar a escrita, registrar a mensagem sem segredos e indicar ação necessária. Não insistir em chamadas negadas.

Erro transitório: no máximo três tentativas, respeitando Retry-After quando presente e sem duplicar registros. Conflito: reler e reconciliar; não sobrescrever cegamente. Se nenhuma ferramenta adequada existir, não apresentar screenshots ou dados simulados como resultados reais.

## Evidência e critério de pronto

Cada etapa deve apresentar objetivo, mudanças, testes executados, resultado observado, localização privada da evidência, reversão e próxima ação. Só marcar concluída quando todos os critérios da etapa forem demonstrados. Um prompt, documento ou teste sintético não comprova integração institucional.

Manter os estados: não iniciado, em execução, bloqueado, aguardando aprovação, validado. Uma etapa aprovada não autoriza automaticamente a seguinte com novos riscos.

## Entrega ao responsável

Responder em português com: entregue; conferido; pendente/bloqueado; única decisão necessária. Não divulgar credenciais nem repetir o roteiro inteiro. Consultar o checkpoint ao retomar.

## Fonte do mecanismo de instruções

OpenAI: https://developers.openai.com/codex/guides/agents-md
O nome AGENTS.md oferece orientação ao agente; não implanta serviço nem garante obediência perfeita. Testes, permissões e revisão continuam necessários.
