# Padrão de botões das Notas Técnicas — SOE/ANA

Referência visual indicada pelo usuário: `gaops-20261013/nt-final.html` (115ª reunião do GAOPS, 13/10/2026).

## Ordem, rótulos e comportamento

| Ordem | Rótulo exato | Aparência | Destino |
|---|---|---|---|
| 1 | Baixar NT completa · PDF | Botão principal, fundo verde-claro `#c9f3e8`, texto `#064f4b` | PDF integral efetivamente disponível, com atributo de download |
| 2 | Ler NT integral | Fundo branco, texto `#07556b`, borda clara | HTML integral da NT; quando a própria página já é integral, âncora para o início do texto |
| 3 | Baixar indicadores · CSV | Mesmo estilo secundário do botão HTML | CSV real, com fonte, período, unidade e natureza do dado |

Os botões ficam juntos, no cabeçalho, abaixo da identificação da reunião e dos créditos, sempre na mesma ordem. Não renomear casualmente entre reuniões.

Geometria: borda de 1 px, raio de 7 px, preenchimento de 11 px por 18 px, espaçamento de 12 px, texto sem sublinhado e altura visual uniforme. A ordem deve permanecer no celular; em telas estreitas, os botões podem ocupar a largura disponível. O foco por teclado deve ser visível.

A ação de impressão pode permanecer em uma linha discreta abaixo, sem competir com os três botões principais. Botões de navegação não aparecem na versão impressa.

## Regras editoriais

- Não criar botões sem arquivo/destino funcional. O CSV só aparece quando houver dados efetivamente disponíveis, e não deve confundir observações, previsões, premissas de simulação ou decisões.
- Não publicar o DOCX editável: permanece de uso privado. O download público da NT é PDF.
- Preservar nome, cargo, vínculo e referência ao suporte de IA na abertura e no rodapé.
- Manter a NT, as verticais e as figuras como conteúdo principal. Fontes e apresentações/anexos integrais permanecem ao final, sem grandes botões de anexo na abertura.
- Padronizar os controles não significa reduzir o texto, as figuras ou a análise técnica.
- Distinguir a edição web em PDF do DOCX original quando forem produtos editoriais distintos.

## Verificação antes da publicação

Testar os dois downloads; conferir se o botão de leitura leva ao conteúdo integral; verificar layout em computador e celular; confirmar preservação do conteúdo técnico, das figuras e dos créditos.

Aplicação inicial deste ajuste: `pantanal/13a-2026-10-21/`. A página histórica do GAOPS usada como referência não foi modificada.
