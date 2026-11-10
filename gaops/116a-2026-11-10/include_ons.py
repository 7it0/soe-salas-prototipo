#!/usr/bin/env python3
"""Incremental ONS integration. Preserves earlier verticals and uses the same DOM for HTML/PDF."""
from pathlib import Path
import csv, hashlib, html, re, types
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
ONS_SHA='7bef207e667eb08c522fe046e2ac9fbdaa618e7b3d1b00c803a82c310b1d9e29'
FIGS_ONS=[(3,'Santa Cecília — vazões naturais e médias mensais','Maio a novembro parcial; novembro em 204% da MLT até 09/11. Não é vazão defluente.'),(4,'Santa Cecília — detalhe de 2026','Série de 2014 como referência visual, não cenário probabilístico.'),(5,'Armazenamento equivalente — série histórica','57,06% rotulado; rodapé informa 06/09/2026, divergindo do alcance gráfico. Data a confirmar.'),(6,'Armazenamento dos reservatórios e equivalente','Curvas distintas; 57,06% no equivalente. Rodapé de 06/09/2026 preservado.'),(7,'Armazenamento equivalente — comparação anual','Curva de 2026 avança no gráfico além da data de 10/08/2026 indicada no rodapé.'),(9,'Operação de Paraibuna','Afluência, defluência e volume útil; sem extração de valores pontuais sem rótulo.'),(10,'Operação de Santa Branca','Inclui volume de espera. Não extrapolar a linha tracejada além do trecho apresentado.'),(11,'Operação de Jaguari','Recomposição do estoque na parte final da série; não informa vazão de transferência para SABESP.'),(12,'Operação de Funil','Resposta com oscilações e volume de espera; não é previsão de pico de cheia.'),(14,'Curva de segurança — operação normal','Aplicação abril–novembro de 2026: novembro 16,7%; novembro-final 11,6%.'),(15,'Simulação do sistema equivalente','Novembro observado na lâmina: 56,5%; novembro-final simulado: 54,0%. Premissas não detalhadas nesta apresentação.')]
ONS_HTML='''<section class="chapter" id="ons"><h2>5. Vertical ONS — hidrologia, armazenamento e operação</h2>
<h3>5.1 Situação hidrológica observada</h3>
<p>A apresentação de 10/11/2026 registra mudança expressiva no comportamento das vazões naturais de Santa Cecília: as médias de maio a agosto permaneceram abaixo da média de longo termo (MLT), em 69%, 79%, 78% e 72%, respectivamente; setembro alcançou 247%, outubro 230% e novembro parcial 204%, com corte explícito em 09/11/2026. Isso sustenta a leitura de recuperação recente, mas não autoriza concluir que a vazão absoluta diminuiu na mesma proporção entre meses: a referência climatológica mensal também varia. [O, p. 3]</p>
<p>Os hidrogramas das páginas 3 e 4 mostram pulsos importantes em setembro, outubro e início de novembro, contrastando com o período de menores vazões no inverno. A série de 2014 aparece como comparação histórica; não é a MLT, nem um cenário com probabilidade atribuída. Vazão natural não é a vazão efetivamente liberada a jusante, bombeada ou transferida entre sistemas. [O, pp. 3–4]</p>
<h3>5.2 Indicadores, armazenamento e referências temporais</h3>
<p>As páginas 5 e 6 rotulam o armazenamento equivalente em <strong>57,06%</strong>. Entretanto, ambas informam no rodapé “Dados até 06/09/2026”, enquanto as curvas alcançam visualmente novembro. A página 7 apresenta outra divergência: rodapé “Dados até 10/08/2026” e curva de 2026 estendida além de agosto. Mantêm-se valores e datas originais; os 57,06% não são publicados como observação confirmada de 09 ou 10/11. A data-base deve ser esclarecida com o ONS. [O, pp. 5–7]</p>
<p>No quadro de simulação, a sequência identificada como armazenamento observado é 58,5% em abril; 58,9% em maio; 55,0% em junho; 52,1% em julho; 46,2% em agosto; 39,8% em setembro; 49,0% em outubro; e 56,5% em novembro. A lâmina não especifica o dia de referência de cada ponto. Os 56,5% de novembro e os 57,06% das séries anteriores permanecem como registros distintos, sem harmonização silenciosa. [O, p. 15]</p>
<p>A evolução de 39,8% em setembro para 56,5% em novembro sinaliza recomposição na sequência apresentada, não uma medição de recuperação uniforme em todos os reservatórios. O armazenamento equivalente é um indicador agregado; não substitui a avaliação individual de Paraibuna, Santa Branca, Jaguari e Funil. [O, pp. 6 e 9–12 e 15]</p>
<h3>5.3 Efeitos sobre reservatórios e operação</h3>
<p><strong>Paraibuna:</strong> o painel mostra recuperação do volume útil na parte final da série, após o declínio do período seco, com pulsos de afluência e defluências menores que as praticadas no trecho anterior. A leitura é qualitativa, pois não há rótulos numéricos dos últimos pontos. Não se deduz uma nova regra de operação a partir da curva. [O, p. 9]</p>
<p><strong>Santa Branca:</strong> há recuperação do volume útil após o mínimo recente, com pulsos de afluência e mudança do patamar de defluência. O painel inclui volume de espera, mas a linha tracejada não cobre integralmente o horizonte final; não deve ser prolongada como se fosse a condição vigente em novembro. [O, p. 10]</p>
<p><strong>Jaguari:</strong> a parte final do painel apresenta recomposição do volume útil com defluências em patamar visualmente baixo e afluências variáveis. O gráfico não fornece a vazão de transferência Jaguari–Atibainha, a demanda atual da SABESP ou o balanço específico dessa transferência. Ausência do dado não significa transferência nula. [O, p. 11]</p>
<p><strong>Funil:</strong> o painel mostra recuperação e oscilações do estoque associadas a pulsos de afluência e resposta operativa. O histórico de volume de espera é reproduzido sem extrapolação. Em conjunto com os demais reservatórios, justifica acompanhar sincronização dos aportes e propagação a jusante, mas não permite quantificar um pico futuro em Santa Cecília ou Ilha dos Pombos. Esta última consequência é inferência analítica, não previsão numérica do ONS. [O, p. 12; C, p. 11]</p>
<h3>5.4 Curva de segurança, simulação e riscos</h3>
<p>A curva para operação normal tem aplicação indicada de abril a novembro de 2026 e é identificada na legenda como “Curva Captação Suplementar”. Seus valores são 57,7%, 56,4%, 50,8%, 44,9%, 38,2%, 30,8%, 23,8%, 16,7% e 11,6%, respectivamente para abril, maio, junho, julho, agosto, setembro, outubro, novembro e novembro-final. Esses valores são referências da curva apresentada, não observações ou previsões de armazenamento. [O, p. 14]</p>
<p>Na página 15, o armazenamento observado rotulado em novembro é 56,5% e a simulação para novembro-final é <strong>54,0%</strong>. A projeção, portanto, não é de elevação contínua do estoque, embora permaneça acima da curva. Cálculos desta NT, explicitamente derivados dos rótulos: diferença de 39,8 pontos percentuais entre 56,5% e 16,7%; diferença de 42,4 pontos percentuais entre 54,0% e 11,6%; e recuo simulado de 2,5 pontos percentuais entre os dois pontos de novembro. Não são volumes adicionais disponíveis para captação nem intervalos de confiança. [O, pp. 14–15]</p>
<p>A apresentação não detalha as premissas de afluências, defluências, transferências e perdas utilizadas para os 54,0%, nem fornece um conjunto de cenários de armazenamento para 2027. Não se extrapola essa trajetória para dezembro, janeiro ou o restante de 2027. Permanecem relevantes a incerteza meteorológica, a distribuição espacial dos aportes, as diferenças entre reservatórios e a confirmação das datas-base. [O, pp. 14–15; M, pp. 8–12; C, pp. 8–17]</p>
<h3>5.5 Implicações para ANA/GAOPS e usos múltiplos</h3>
<p>O material acrescenta elementos operativos à análise, mas não registra nova decisão de defluência, autorização de captação suplementar ou alteração das condições de transferência. A posição acima da curva não comprova, isoladamente, o atendimento integral das condições aplicáveis. O confronto solicitado com a Resolução Conjunta nº 1.382/2015 depende dos atos e condições pertinentes e de dados operativos com data-base confirmada; a apresentação recebida não contém essa auditoria normativa. Esta NT não cria nem flexibiliza limites.</p>
<p>Para as interfaces com CEIVAP/AGEVAP e SABESP, é necessário distinguir recuperação hidrológica, estoque agregado e condições de atendimento dos usos. Os três PDFs não documentam solicitação atual de aumento de transferência, manifestação desses participantes ou novos volumes autorizados. Esses campos permanecem sem atribuição institucional até que haja documento ou relato identificável. [M; C; O]</p>
<h3>5.6 Recomendações analíticas e decisões</h3>
<p>Recomenda-se confirmar com o ONS as datas-base das páginas 5–7, esclarecer a relação temporal entre 57,06% e 56,5% e explicitar as premissas da simulação de 54,0%. Acompanhar a chuva realizada, os pulsos de vazão natural de Santa Cecília, os volumes e as vazões operadas de cada reservatório e as condições a jusante. Para avaliação de 2027, solicitar horizonte e premissas próprios, em vez de prolongar a simulação de novembro. São recomendações analíticas; não foram informadas novas deliberações ou encerramento da reunião.</p></section>'''
CROSS_HTML='''<section class="chapter" id="cruzamentos"><h2>6. Cruzamentos técnicos e consequências operacionais</h2><p>A incorporação do ONS permite cruzar diagnóstico meteorológico, índices hidrológicos, armazenamento e operação. A convergência entre produtos não elimina diferenças de variável, área, período, data-base e dependência dos dados. Recomendações abaixo são analíticas, não decisões do colegiado.</p><div class="tablewrap"><table><thead><tr><th>Cruzamento</th><th>Convergência ou diferença</th><th>Consequência para ANA/GAOPS</th></tr></thead><tbody>
<tr><td>INPE/INMET × ONS</td><td>Anomalias positivas de chuva em setembro/outubro e vazão natural em Santa Cecília em 247% e 230% da MLT; novembro parcial em 204% até 09/11. [M, p. 5; O, p. 3]</td><td>Convergência de recuperação recente; não comparar diretamente milímetros com vazão, nem vazão natural com defluência.</td></tr>
<tr><td>CEMADEN × ONS — Santa Cecília</td><td>TSI-3 de outubro 2,03 e TSI-6 1,08, ambos em excesso; vazões naturais recentes acima da MLT. [C, pp. 5–6; O, p. 3]</td><td>Convergência qualitativa, com memórias temporais diferentes. Excesso do índice não é confirmação de inundação.</td></tr>
<tr><td>TSI-3 × TSI-6 × estoques</td><td>Paraibuna, Santa Branca e Ilha dos Pombos em excesso no TSI-3 e normais no TSI-6; ONS mostra estoques diferenciados. [C, pp. 5–6; O, pp. 6 e 9–12]</td><td>Não confundir recuperação recente com recomposição homogênea ou reservatórios cheios.</td></tr>
<tr><td>Chuva prevista × operação observada</td><td>GEFS rotula cerca de 112 mm em 14 dias; MONAN/BAM têm outras janelas; ONS registra a resposta histórica dos reservatórios. [M, pp. 8–9; C, pp. 8–9; O, pp. 9–12]</td><td>Acompanhar realização nas áreas contribuintes, defasagem e sincronização dos aportes. Não converter o acumulado previsto diretamente em VU ou defluência.</td></tr>
<tr><td>MHD/GloFAS × simulação equivalente</td><td>MHD prevê vazão natural de 07/11 a 07/12; GloFAS usa categorias. ONS simula armazenamento equivalente de 54,0% em novembro-final. [C, pp. 11–13; O, p. 15]</td><td>Não há contradição automática entre vazão natural favorável e redução simulada do estoque: o balanço também depende da operação. Sem as premissas do ONS, não se atribui a causa da diferença.</td></tr>
<tr><td>Armazenamento × curva de segurança</td><td>Na mesma lâmina: novembro 56,5% versus curva 16,7%; novembro-final simulado 54,0% versus 11,6%. [O, pp. 14–15]</td><td>Posição acima da curva no cenário apresentado, sem inferir liberação automática para novas captações, transferências ou defluências.</td></tr>
<tr><td>Controle de qualidade das séries</td><td>57,06% nas páginas 5–6, rodapé de 06/09; página 7 com rodapé de 10/08; 56,5% em novembro na página 15.</td><td>Manter registros separados e datas pendentes; não rotular todos como estoque de 09/11 nem inserir em série anual validada sem confirmação.</td></tr>
<tr><td>Horizonte sazonal × 2027</td><td>INPE/INMET e CEMADEN incluem NDJ 2026/2027; a simulação ONS fornecida termina em novembro de 2026. [M, pp. 11–12; C, pp. 16–17; O, p. 15]</td><td>A informação sazonal não prolonga automaticamente o estoque projetado. Cenário operativo de 2027 permanece não apresentado.</td></tr>
<tr><td>Recuperação × CEIVAP/SABESP</td><td>Há melhora hidrológica, mas sem balanço de transferências, demanda atual ou manifestação desses atores nos arquivos.</td><td>Não atribuir aumento de atendimento, transferência nula ou autorização suplementar. Incorporar manifestações somente quando informadas.</td></tr>
<tr><td>Fontes compartilhadas</td><td>INPE é fonte de chuva do CEMADEN; dados ONS/ANA alimentam o TSI e o MHD. [C, pp. 2–6 e 11]</td><td>Não tratar toda concordância como evidência estatística independente.</td></tr>
</tbody></table></div><h3>6.1 Pauta de integração para a SOE</h3><p>Confirmar as datas e premissas do ONS; confrontar a previsão com chuva e afluências realizadas; avaliar armazenamento e operação por reservatório, sem substituir esse acompanhamento pelo equivalente; registrar condições a jusante e eventuais demandas de CEIVAP/AGEVAP, SABESP e demais participantes. A eventual avaliação de aderência à Resolução Conjunta nº 1.382/2015 e a outros instrumentos deve identificar os dispositivos e os dados empregados, sem presumir vigência auditada ou nova autorização nesta NT.</p></section>'''

def frag(text):return BeautifulSoup(text,'html.parser')
def table(headers,rows):
    return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+html.escape(str(x))+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def replace_p(sec,prefix,text):
    candidates=[p for p in sec.find_all('p',recursive=False) if p.get_text(' ',strip=True).startswith(prefix)]
    assert len(candidates)==1,(sec.get('id'),prefix,len(candidates))
    candidates[0].replace_with(frag(text).p)

def patch_html(path):
    s=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    # Preserve all analytical paragraphs of INPE/INMET and CEMADEN except receipt-status updates.
    before={k:len(s.find(id=k).find_all('p',recursive=False)) for k in ['inpe','cemaden']}
    executive=s.find(id='executivo')
    executive.find('p',class_='scope').replace_with(frag('<p class="scope"><strong>Escopo desta edição:</strong> incorporados os três PDFs da 116ª GAOPS de 10/11/2026: INPE/INMET (13 páginas), CEMADEN (17 páginas) e ONS (16 páginas). A pendência inicial do ONS está superada. Permanecem ressalvas sobre datas e rótulos das fontes; não foram informadas deliberações ou encerramento. O cenário de armazenamento apresentado pelo ONS termina em novembro, não em 2027.</p>').p)
    replace_p(executive,'Na previsão GEFS','<p>Na previsão GEFS de 10/11 às 00 UTC, o acumulado central rotulado para a bacia é de aproximadamente 112 mm em 14 dias. Os modelos semanais apresentam variação espacial e temporal; as perspectivas MHD e GloFAS não constituem programa de defluências. Com o ONS incorporado, a integração distingue vazão natural prevista, operação observada e simulação do sistema equivalente. [M, pp. 8–9; C, pp. 8–13; O, pp. 9–15]</p>')
    new='''<p id="sintese-ons"><strong>O ONS corrobora a recuperação recente em Santa Cecília:</strong> vazão natural em 247% da MLT em setembro, 230% em outubro e 204% em novembro parcial até 09/11. Na lâmina de simulação, novembro aparece com 56,5% de armazenamento equivalente observado e novembro-final com 54,0% simulado, acima das referências da curva de 16,7% e 11,6%. São variáveis e naturezas distintas; a posição acima da curva não constitui autorização operativa. [O, pp. 3 e 14–15]</p><p id="ressalva-ons-datas"><strong>Ressalva de data-base:</strong> os 57,06% das páginas 5–6 vêm acompanhados do rodapé 06/09/2026, embora as curvas alcancem novembro; a página 7 informa 10/08/2026. Esses rótulos não foram corrigidos silenciosamente nem equiparados aos 56,5% da simulação. Confirmar datas e premissas antes de incorporar os registros às séries anuais. [O, pp. 5–7 e 15]</p>'''
    for e in reversed(list(frag(new).find_all('p',recursive=False))):executive.find('div',class_='tablewrap').insert_before(e)
    for tr in executive.select('tbody tr'):
        tds=tr.find_all('td')
        if tds[0].get_text(strip=True)=='Operação e usos':
            tds[1].string='ONS incorporado: 56,5% no ponto novembro; 54,0% em novembro-final simulado; sem balanço de transferências.'
            tds[2].string='Distinguir estoque, simulação e curva; sem inferir autorização ou atendimento adicional.'
        if tds[0].get_text(strip=True)=='Qualidade documental':
            tds[1].string='Ressalvas meteorológicas mantidas; ONS com datas de rodapés divergentes e valores 57,06% / 56,5% não harmonizados.'
    replace_p(s.find(id='inpe'),'O material subsidia','<p>O material subsidia o acompanhamento meteorológico, mas não apresenta decisão regulatória, novo limite de defluência ou autorização de transferência. O confronto com a apresentação do ONS está desenvolvido na seção 6, preservadas as ressalvas de data-base e de premissas. A melhora meteorológica, isoladamente, não fundamenta flexibilização de condicionantes.</p>')
    replace_p(s.find(id='cemaden'),'Confrontar o excesso','<p>Confrontar o excesso indicado pelo TSI com as curvas de armazenamento e operação agora recebidas do ONS; acompanhar a chuva efetiva e a dispersão das previsões; esclarecer o percentual da página 4 e as janelas do GloFAS, assim como as datas divergentes dos painéis operativos. Não há deliberação informada nesta etapa. Dados de previsão e índices acumulados ficam separados das observações diárias na base anual.</p>')
    s.find(id='ons').replace_with(frag(ONS_HTML).section)
    s.find(id='cruzamentos').replace_with(frag(CROSS_HTML).section)
    s.select_one('nav a[href="#ons"]').string='ONS'
    scope=s.find(id='escopo')
    scope.insert(2,frag('<p>[O] identifica o PDF “116ª Reunião GAOPS-10-11-2026-Apresentação ONS.pdf”, recebido e analisado integralmente (16 páginas). A incorporação não transforma as anotações do material em decisões da reunião.</p>').p)
    for row in [('Vazão natural ONS — Santa Cecília','Maio–outubro completos; novembro até 09/11','Percentuais mensais da MLT; não são defluências.'),('Armazenamento ONS — pp. 5–7','Rodapés 06/09 e 10/08/2026; alcance gráfico posterior','57,06% preservado com data-base pendente.'),('Simulação ONS — p. 15','Pontos mensais abril–novembro; novembro-final simulado','56,5% observado na lâmina; 54,0% simulado; dias não especificados.')]:scope.select_one('tbody').append(frag('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>').tr)
    register=s.find(id='registro')
    replace_p(register,'Situação do registro:','<p><strong>Situação do registro:</strong> três PDFs recebidos e analisados, com incorporação incremental do ONS autorizada pelo responsável. Não foram informadas manifestações do debate, deliberações ou encerramento. Recomendações desta NT não substituem a ata e não são apresentadas como decisões do colegiado.</p>')
    replace_p(register,'Encaminhamentos propostos','<p><strong>Encaminhamentos propostos para avaliação da equipe:</strong> esclarecer datas-base e premissas do ONS; preservar as demais ressalvas documentais; complementar transferências e demandas se apresentadas; registrar eventuais decisões com fonte e atribuição. Nenhum prazo ou responsável institucional foi arbitrado.</p>')
    sources=s.find(id='fontes')
    sources.insert(3,frag('<p>[O] ONS: 116ª Reunião GAOPS-10-11-2026-Apresentação ONS.pdf — 16 páginas. Análise hidrológica e hidráulica da bacia do Rio Paraíba do Sul, 10/11/2026. Cópia hospedada conferida por SHA-256 contra o arquivo recebido.</p>').p)
    replace_p(sources,'[R] Relatos','<p>[R] Relatos do responsável: programação às 15h00; recebimento inicial de INPE/INMET e CEMADEN, seguido do ONS; autorização para atualização e cruzamentos incrementais. Não há relato de encerramento ou de decisão adicional nesta edição.</p>')
    replace_p(sources,'As duas apresentações','<p>As três apresentações anexadas são a base documental. Referências a NOAA, ECMWF, INMET, INPE e ANA/ONS dentro das lâminas identificam a origem dos produtos/dados e não confirmam participação adicional nesta reunião.</p>')
    sources.append(frag('<p><strong>Controle adicional ONS:</strong> páginas 5–6, 57,06% com rodapé 06/09/2026; página 7, rodapé 10/08/2026; página 15, novembro 56,5% e simulação novembro-final 54,0%. Não há datas diárias explícitas dos pontos mensais ou premissas completas da simulação. Os valores pontuais sem rótulo nas curvas de reservatórios não foram digitalizados nem apresentados com falsa precisão.</p>').p)
    annex=s.find(id='anexo-i')
    h=next(x for x in annex.find_all('h3') if x.get_text().startswith('I.4'))
    node=h
    while node:
        nxt=node.next_sibling;node.extract();node=nxt
    monthly=[('Maio/2026','69'),('Junho/2026','79'),('Julho/2026','78'),('Agosto/2026','72'),('Setembro/2026','247'),('Outubro/2026','230'),('Novembro/2026 até 09/11','204')]
    annex.append(frag('<h3>I.4 Vazão natural de Santa Cecília — ONS</h3>').h3)
    annex.append(frag(table(['Período','Valor','Unidade','Natureza','Fonte / interpretação'],[(a,b,'% MLT','Média verificada; novembro parcial','O, p. 3. Não é vazão defluente.') for a,b in monthly])).div)
    months=['Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Nov-final']
    ref=[57.7,56.4,50.8,44.9,38.2,30.8,23.8,16.7,11.6]
    obs=[58.5,58.9,55.0,52.1,46.2,39.8,49.0,56.5,None]
    br=lambda v:f'{v:.1f}'.replace('.',',')
    rows=[(m,br(r),br(o) if o is not None else '—','54,0' if o is None else '—','O, pp. 14–15; referência mensal sem dia explicitado') for m,r,o in zip(months,ref,obs)]
    annex.append(frag('<h3>I.5 Sistema equivalente — curva, observado e simulado</h3>').h3)
    annex.append(frag('<p>Todos os valores deste quadro são percentuais de armazenamento equivalente; as colunas não são intercambiáveis. A curva tem aplicação declarada abril–novembro de 2026. Não representa limite individual de cada reservatório.</p>').p)
    annex.append(frag(table(['Ponto em 2026','Curva de segurança (%)','Observado na lâmina (%)','Simulado (%)','Fonte / ressalva'],rows)).div)
    annex.append(frag(table(['Comparação derivada','Valor','Unidade','Natureza','Cálculo / fonte'],[('Novembro: observado menos curva','39,8','p.p.','Cálculo desta NT','56,5 − 16,7; O, pp. 14–15'),('Novembro-final: simulado menos curva','42,4','p.p.','Cálculo desta NT','54,0 − 11,6; O, pp. 14–15'),('Novembro-final simulado menos novembro observado','−2,5','p.p.','Variação condicional calculada','54,0 − 56,5; O, p. 15')])).div)
    annex.append(frag('<h3>I.6 Registros com data-base a confirmar</h3>').h3)
    annex.append(frag(table(['Registro','Valor','Unidade','Data literal / natureza','Fonte / controle'],[('Armazenamento equivalente — histórico','57,06','%','Rodapé 06/09/2026; data conflitante','O, p. 5; gráfico com alcance posterior'),('Armazenamento equivalente — componentes','57,06','%','Rodapé 06/09/2026; data conflitante','O, p. 6; repetição do indicador, não nova observação'),('Comparação anual 2026','Não transcrito','%','Rodapé 10/08/2026; data conflitante','O, p. 7; sem último valor rotulado')])).div)
    annex.append(frag('<h3>I.7 Operação, usos e contribuição ao Conjuntura</h3>').h3)
    annex.append(frag('<p>Os painéis ONS de Paraibuna, Santa Branca, Jaguari e Funil foram reproduzidos, sem transcrever como exatos os últimos valores sem rótulo. Não há balanço numérico de transferências para a SABESP, demanda atual, vazão bombeada ou manifestação do CEIVAP/AGEVAP nos arquivos. Campo ausente não é zero. A apresentação do ONS não fornece cenário operativo para 2027.</p>').p)
    annex.append(frag('<p>Para a memória anual, separar observações, referências da curva, projeções, cálculos derivados e registros com data pendente. Não somar janelas de precipitação sobrepostas; não transformar TSI em VU; não contar os 57,06% repetidos nas páginas 5–6 como duas observações independentes; não usar previsão como resultado verificado. Esta síntese é subsídio técnico, não estatística anual homologada.</p>').p)
    for k,n in before.items():assert len(s.find(id=k).find_all('p',recursive=False))==n,'Earlier vertical lost'
    for bad in ['ONS · pendente','ONS ainda não recebido','ONS aguardado','dois PDFs recebidos']:
        # Old header is replaced by the generation function below.
        assert bad not in s.main.get_text(),bad
    path.write_text(str(s),encoding='utf-8')

def main():
    source=ROOT/'fontes/ons.pdf'
    assert source.exists() and hashlib.sha256(source.read_bytes()).hexdigest()==ONS_SHA,'Exact received ONS PDF missing; stop before changing publication'
    patch_html(ROOT/'index.html')
    code=(ROOT/'build_received.py').read_text(encoding='utf-8')
    replacements={
      'Prévia documental 0.2':'Prévia documental 0.3',
      'PRÉVIA DOCUMENTAL 0.2':'PRÉVIA DOCUMENTAL 0.3',
      "'version':'0.2'":"'version':'0.3'",
      'INPE/INMET e CEMADEN analisados. ONS ainda não recebido; debate e encerramento não informados.':'INPE/INMET, CEMADEN e ONS analisados. Registro do debate e encerramento ainda em aberto.',
      'Texto integral, cruzamentos técnicos, Anexo I e 24 reproduções identificadas.':'Texto integral, cruzamentos técnicos, Anexo I e 35 reproduções identificadas.',
      'INPE/INMET e CEMADEN; ONS pendente. Anexo I e 24 reproduções.':'INPE/INMET, CEMADEN e ONS. Anexo I e 35 reproduções.',
      'Prévia documental; ONS pendente; encerramento não informado':'Prévia documental integrada; três fontes recebidas; encerramento não informado',
      'PRÉVIA DOCUMENTAL 0.3 — INPE/INMET e CEMADEN, cruzamentos, Anexo I, 24 reproduções e 38 registros numéricos. ONS ainda não recebido; deliberações e encerramento não informados. NT integral e apresentações hospedadas.':'PRÉVIA DOCUMENTAL 0.3 — INPE/INMET, CEMADEN e ONS incorporados; cruzamentos atualizados, Anexo I, 35 reproduções e 68 registros numéricos. Ressalvas de datas e premissas explicitadas. Deliberações e encerramento não informados. NT integral e três apresentações hospedadas.'
    }
    for a,b in replacements.items():
        assert a in code,'Generator marker missing: '+a
        code=code.replace(a,b)
    mod=types.ModuleType('gaops116_ons_builder');mod.__file__=str(ROOT/'build_received.py');exec(compile(code,mod.__file__,'exec'),mod.__dict__)
    mod.HASHES['ons']=ONS_SHA;mod.LABELS['ons']='ONS';mod.PAGES['ons']=16;mod.FIGS['ons']=FIGS_ONS
    def obtain(out,local=None):
        import shutil,fitz
        records={}
        for key,h in mod.HASHES.items():
            src=(Path(local) if local else ROOT/'fontes')/(key+'.pdf')
            assert src.exists() and mod.sha(src)==h,'Source differs: '+key
            with fitz.open(src) as d:assert len(d)==mod.PAGES[key]
            dest=out/'fontes'/(key+'.pdf')
            if src.resolve()!=dest.resolve():shutil.copyfile(src,dest)
            records[key]={'sha256':h,'pages':mod.PAGES[key],'matches_received_file':True,'method':'verified_received_copy_in_repository'}
        return records
    mod.obtain=obtain
    previous_data=mod.data
    def data(out):
        rows=previous_data(out)
        def add(system,var,value,unit,period,nature,page,note=''):
            rows.append(['ONS',system,var,str(value).replace('.',','),unit,period,nature,page,mod.SITE+f'fontes/ons.pdf#page={page}',note])
        for month,val in [('Maio',69),('Junho',79),('Julho',78),('Agosto',72),('Setembro',247),('Outubro',230),('Novembro',204)]:add('Santa Cecília','Vazão natural média relativa à MLT',val,'% MLT',month+'/2026'+(' até 09/11' if month=='Novembro' else ''),'observado_parcial' if month=='Novembro' else 'observado_mensal',3,'Não é defluência; climatologia varia entre meses')
        for pg in [5,6]:add('Sistema equivalente Paraíba do Sul','Armazenamento equivalente — rótulo',57.06,'%','Rodapé 06/09/2026; curva com alcance posterior','observado_data_pendente',pg,'Mesmo valor repetido em duas lâminas; não contar como duas observações')
        months=['Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Nov-final']
        for month,v in zip(months,[57.7,56.4,50.8,44.9,38.2,30.8,23.8,16.7,11.6]):add('Sistema equivalente Paraíba do Sul','Curva de segurança para operação normal',v,'% VU equivalente',month+'/2026','referencia_curva',14,'Legenda Curva Captação Suplementar; não é valor observado')
        for month,v in zip(months,[58.5,58.9,55.0,52.1,46.2,39.8,49.0,56.5]):add('Sistema equivalente Paraíba do Sul','Armazenamento observado na lâmina de simulação',v,'% VU equivalente',month+'/2026 — dia não explicitado','observado_rotulo_mensal',15,'Não harmonizado com 57,06% das pp. 5–6')
        add('Sistema equivalente Paraíba do Sul','Armazenamento simulado',54.0,'% VU equivalente','Novembro-final/2026','simulacao_condicional',15,'Premissas não detalhadas; não extrapolar para 2027')
        for var,v,period,note in [('Diferença observado menos curva',39.8,'Novembro/2026','56,5 − 16,7'),('Diferença simulado menos curva',42.4,'Novembro-final/2026','54,0 − 11,6'),('Variação simulada em novembro',-2.5,'Novembro a novembro-final/2026','54,0 − 56,5')]:add('Sistema equivalente Paraíba do Sul',var,v,'pontos percentuais',period,'calculo_derivado',15,'Cálculo desta NT: '+note+'; não é disponibilidade para captação')
        assert len(rows)==68,len(rows)
        with (out/'indicadores.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f,delimiter=';');w.writerow(['instituicao','sistema','variavel','valor','unidade','periodo','natureza','pagina_fonte','fonte_pdf','observacao']);w.writerows(rows)
        return rows
    mod.data=data
    mod.main()
if __name__=='__main__':main()
