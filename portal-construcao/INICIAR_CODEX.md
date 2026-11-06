# Iniciar ou retomar a construção do Portal SOE

Versão 1.0 — 06/11/2026. Este arquivo é uma instrução de tarefa, não programa executável nem autorização institucional.

## Onde começar

Repositório de documentação pública: `7it0/soe-salas-prototipo`.

Leia explicitamente `portal-construcao/AGENTS.md` e `portal-construcao/ROTEIRO_EXECUCAO.md`. Se o cliente permitir, inicie com diretório de trabalho `portal-construcao`. Uma instrução em subpasta não deve ser presumida carregada quando se trabalha na raiz.

O guia de leitura é `portal-construcao/execucao.html`. O checkpoint histórico de 29/10/2026 está no roteiro; verificar o estado atual antes de modificar qualquer recurso.

## Prompt inicial

```text
Você é o executor técnico da construção do Portal SOE.

Leia portal-construcao/AGENTS.md e portal-construcao/ROTEIRO_EXECUCAO.md
no repositório 7it0/soe-salas-prototipo. Este repositório é público:
não copie para ele dados, URLs internas, IDs, capturas ou exports
corporativos. Não altere o acervo das reuniões nem os workflows.

Objetivo deste lote: E00 a E03 — comprovar acesso, conferir os recursos
existentes e preparar a chamada para o índice das reuniões em ambiente
controlado. Não iniciar a implantação completa nem outro plano longo.

Comece somente com leitura. Informe ferramentas realmente disponíveis
para leitura e edição do SharePoint/Power Automate. Não presuma que
sua sessão herdou o login Microsoft de outra aba ou computador.

Se houver ferramenta adequada e permitida, peça meu login apenas na
interface oficial. Confirme conta, site, página, lista e fluxo.
Proponha o alvo de teste e o lote de alterações para minha aprovação.
Depois dessa aprovação, execute as ações reversíveis do lote sem
pedir que eu opere cada botão, respeitando as confirmações da plataforma.

A primeira alteração é a chamada “Salas SOE — Reuniões e Notas Técnicas”,
com destino https://7it0.github.io/soe-salas-prototipo/salas/ e aviso de
protótipo técnico pessoal. Preserve as outras seções, salve, reabra,
confira link e persistência, e documente a reversão.

Não publique, exclua, altere permissões, troque a página inicial,
instale ferramentas ou ative rotinas sem aprovação específica.

Se houver bloqueio, não repita tentativas indefinidamente: descreva
ferramenta, operação, mensagem sem segredos e decisão necessária.
Prossiga apenas em tarefas locais independentes com dados sintéticos,
identificando-as como preparação, não integração concluída.

Ao fim, entregue: o que mudou; o que foi testado; evidência privada;
pendências; forma de retorno; e CHECKPOINT.md atualizado em destino
privado aprovado. Não solicite senha, MFA, cookie ou token pelo chat.
```

## Retomar após uma interrupção

```text
Retome pelo CHECKPOINT.md privado do projeto Portal SOE.
Releia o AGENTS.md aplicável e apenas a etapa pendente do roteiro.
Confira se o estado do recurso mudou. Não refaça etapas já validadas.
Execute o próximo lote aprovado e registre resultado e evidências.
Se o checkpoint não estiver acessível, declare essa ausência antes de
escrever; não invente um estado atual a partir do checkpoint histórico.
```

## Etapas seguintes

E04: arquitetura, navegação e páginas de unidades.
E05: campos da lista existente.
E06: testes de filtro.
E07: integração RSS, idempotência e tratamento de erros.
E08: bloco de notícias externas aprovadas.
E09: expansão para Salas e acervo.
E10: homologação técnica, editorial e acessibilidade.
E11: publicação/ativação expressamente aprovadas.
E12: operação determinística, custos e continuidade.

Cada etapa tem ações, critério de pronto e participação do responsável no roteiro. Nenhum texto do pacote comprova que a conta institucional já tem as permissões necessárias.
