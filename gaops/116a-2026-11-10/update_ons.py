#!/usr/bin/env python3
"""Incremental GAOPS 116 update: received ONS, identical HTML/PDF text, no invented decisions."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, unquote
import argparse, csv, hashlib, html, json, re, shutil, types
import fitz, requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
SITE='https://7it0.github.io/soe-salas-prototipo/gaops/116a-2026-11-10/'
BASE='https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/eventos-criticos/apresentacoes-das-reunioes/'
ONS_SHA='7bef207e667eb08c522fe046e2ac9fbdaa618e7b3d1b00c803a82c310b1d9e29'
ONS_FIGS=[
(3,'Santa Cecília — vazão natural e médias relativas','Maio a agosto abaixo da MLT; setembro 247%, outubro 230% e novembro 204% até 09/11. Vazão natural não é defluência.'),
(4,'Santa Cecília — comparação com 2014','Comparação histórica apresentada pelo ONS; não é cenário de repetição de 2014.'),
(5,'Armazenamento equivalente — histórico','Rótulo 57,06%; rodapé indica 06/09/2026. Data de referência a confirmar, sem corrigir o original.'),
(6,'Armazenamento — reservatórios e equivalente','Curvas até novembro, mas rodapé 06/09/2026. Rótulo equivalente 57,06%; não inferir valores individuais exatos.'),
(7,'Armazenamento equivalente — comparação entre anos','A curva 2026 chega a novembro; o rodapé indica 10/08/2026. Divergência preservada.'),
(9,'Paraibuna — operação','Afluência, defluência e volume útil têm unidades e eixos distintos. Pontos finais sem rótulos não foram convertidos em números exatos.'),
(10,'Santa Branca — operação e volume de espera','Recuperação do volume na parte final da série. Linha de volume de espera não é estoque observado.'),
(11,'Jaguari — operação','Trajetória de recuperação de armazenamento; o gráfico não discrimina a operação da transferência para o Cantareira.'),
(12,'Funil — operação e volume de espera','Variações de afluência, defluência e armazenamento. Não representam, isoladamente, risco de inundação ou nova regra.'),
(14,'Curva de segurança — operação normal','Aplicação abril–novembro/2026; 16,7% em novembro e 11,6% em Nov-final. Referência apresentada, não deliberação desta reunião.'),
(15,'Sistema equivalente — observado e simulação','56,5% rotulado como observado em Nov; 54,0% simulado em Nov-final. Não confundir com 57,06% das páginas 5–6.')]

ONS_HTML='''<section class="chapter" id="ons"><h2>5. Vertical ONS — hidrologia, armazenamento e operação</h2>
<h3>5.1 Situação hidrológica</h3>
<p>A apresentação do ONS, de 10/11/2026, confirma a mudança da condição de vazão natural em Santa Cecília: após médias de 69%, 79%, 78% e 72% da MLT em maio, junho, julho e agosto, respectivamente, setembro alcançou 247%, outubro 230% e novembro parcial 204%, até 09/11. Os dois meses completos e a parcial de novembro são mantidos separados. Vazão natural é a variável indicada na fonte; não representa vazão bombeada, descarga efetivamente praticada nem garantia de atendimento de determinada demanda. [O, pp. 3–4]</p>
<p>A comparação com a série de 2014 contextualiza o comportamento observado, mas não define um cenário futuro de repetição daquele ano. A intensidade e a distribuição dos picos diferem entre as séries; não foram digitalizados pontos sem rótulos numéricos. [O, pp. 3–4]</p>
<h3>5.2 Indicadores, tendências e qualidade temporal</h3>
<p>Os painéis de armazenamento histórico e por reservatório trazem o rótulo de armazenamento equivalente de <strong>57,06%</strong>. Contudo, seus rodapés informam “Dados até 06/09/2026”, enquanto a curva da página 6 avança até novembro. O comparativo interanual da página 7 também chega a novembro, mas informa “Dados até 10/08/2026”. Esses desencontros ficam explicitados: <strong>57,06% é um valor transcrito da apresentação, com data de referência a confirmar</strong>, e não foi silenciosamente reclassificado como observação de 09 ou 10/11. [O, pp. 5–7]</p>
<p>A trajetória recente dos gráficos indica recuperação do sistema equivalente e diferenças entre os quatro reservatórios. O indicador agregado não autoriza atribuir a mesma condição a Paraibuna, Santa Branca, Jaguari e Funil. Os gráficos não fornecem rótulos finais exatos para cada usina; esta NT privilegia a leitura qualitativa e a reprodução integral, sem criar precisão por estimativa visual. [O, pp. 6 e 9–12]</p>
<h3>5.3 Efeitos sobre reservatórios e operação</h3>
<div class="tablewrap"><table><thead><tr><th>Reservatório</th><th>Leitura do gráfico apresentado</th><th>Consequência para o acompanhamento</th></tr></thead><tbody>
<tr><td>Paraibuna</td><td>Recuperação do volume na parte final da série, com afluências variáveis e defluência abaixo dos patamares de parte do período seco.</td><td>Conferir a sustentação dos aportes e o balanço efetivo; a curva não fornece valor final exato. O, p. 9.</td></tr>
<tr><td>Santa Branca</td><td>Elevação recente do volume e alteração das vazões ao longo do período; volume de espera representado separadamente.</td><td>Confrontar sua resposta com Paraibuna e as contribuições incrementais, sem somar volumes percentuais. O, p. 10.</td></tr>
<tr><td>Jaguari</td><td>Armazenamento em recuperação e pulsos de afluência na parte final da série.</td><td>Acompanhar o balanço próprio. A curva não discrimina a transferência para o Cantareira/SABESP. O, p. 11.</td></tr>
<tr><td>Funil</td><td>Recuperação após os menores estoques da série, seguida de oscilações, com variações de afluência e defluência.</td><td>Examinar a propagação a jusante em conjunto com as condições em Santa Cecília. Volume de espera não equivale a volume observado. O, p. 12.</td></tr>
</tbody></table></div>
<p>A leitura combinada dos painéis permite reconhecer a recuperação recente, mas não reconstituir numericamente toda a operação. Não há, nesta apresentação, tabela de transferências, bombeamento em Santa Cecília, atendimento atual da SABESP ou vazões operadas de Ilha dos Pombos. Ausência de informação não é valor zero. [O, pp. 3–15]</p>
<h3>5.4 Curva de segurança, simulação e riscos</h3>
<p>A curva de segurança para operação normal tem aplicação indicada de abril a novembro de 2026. A série denominada “Curva Captação Suplementar” apresenta 57,7%, 56,4%, 50,8%, 44,9%, 38,2%, 30,8%, 23,8%, 16,7% e 11,6%, de abril a “Nov-final”. Esses pontos são referências da curva, não volumes observados nem percentuais de captação. [O, p. 14]</p>
<p>No painel de simulação, os pontos rotulados como armazenamento observado são 58,5% em abril, 58,9% em maio, 55,0% em junho, 52,1% em julho, 46,2% em agosto, 39,8% em setembro, 49,0% em outubro e <strong>56,5% em novembro</strong>. O segmento tracejado indica <strong>54,0% em “Nov-final”</strong>. Portanto, a trajetória projetada nessa lâmina é de pequena redução após a recuperação recente, mantendo-se acima da curva apresentada no mesmo horizonte. Não é uma garantia probabilística: a lâmina não explicita as premissas completas de afluência, defluência, usos e transferências que reproduziriam a simulação. [O, p. 15]</p>
<p>O valor de 56,5% em “Nov” e o rótulo de 57,06% das páginas 5–6 foram mantidos separados. Não se presume que tenham a mesma data ou que um substitua o outro. A comparação com os índices de seca e com os cenários meteorológicos exige respeitar as diferentes datas e variáveis. [O, pp. 5–7 e 15; C, pp. 5–6]</p>
<h3>5.5 Implicações regulatórias e interfaces ANA/GAOPS</h3>
<p>Estar acima da curva apresentada não constitui, por si só, autorização para ampliar captações, transferências ou defluências. A apresentação não contém nova deliberação do GAOPS nem transcrição das condições integrais da Resolução Conjunta nº 1.382/2015. Esta NT não audita sua vigência ou o atendimento dos dispositivos e não infere alteração normativa a partir dos gráficos.</p>
<p>Para as interfaces CEIVAP/AGEVAP e SABESP, a leitura é de acompanhamento dos usos múltiplos, da operação do sistema e das condições a jusante. Não foram atribuídas demandas, concordâncias, pedidos ou decisões a essas instituições sem apresentação específica ou relato do responsável. A incorporação do ONS supera a falta de seu documento, mas não preenche automaticamente essas outras lacunas.</p>
<h3>5.6 Recomendações analíticas</h3>
<p>Confirmar com a fonte as datas dos painéis de armazenamento e a referência do valor de 57,06%; esclarecer as premissas do ponto simulado de 54,0% ao final de novembro; acompanhar a realização das chuvas e sua transformação em vazões e estoques por reservatório; obter valores tabulados contemporâneos quando forem necessários para avaliar condições operativas e usos múltiplos. São propostas para exame técnico, não encaminhamentos aprovados pelo colegiado.</p>
</section>'''

CROSS_HTML='''<section class="chapter" id="cruzamentos"><h2>6. Cruzamentos técnicos e consequências operacionais</h2>
<p><strong>Leitura integrada:</strong> a recuperação de setembro/outubro indicada na meteorologia e nos índices do CEMADEN converge com as vazões naturais superiores à MLT em Santa Cecília e com a recuperação gráfica dos estoques. Essa convergência é qualitativa e não elimina diferenças entre reservatórios, variáveis ou horizontes. [M, p. 5; C, pp. 5–6; O, pp. 3–7]</p>
<div class="tablewrap"><table><thead><tr><th>Cruzamento</th><th>Convergência ou diferença</th><th>Consequência analítica e operacional</th></tr></thead><tbody>
<tr><td>INPE/INMET × ONS</td><td>Anomalias positivas em setembro/outubro acompanham vazão natural de 247% e 230% da MLT em Santa Cecília. M, p. 5; O, p. 3.</td><td>Reconhecer melhora recente sem converter anomalia de chuva em estoque ou vazão operada.</td></tr>
<tr><td>CEMADEN × ONS — Santa Cecília</td><td>TSI-3 de outubro 2,03 e TSI-6 1,08, ambos em excesso, coexistem com vazão de outubro em 230% da MLT; novembro tem parcial de 204%. C, pp. 5–6; O, p. 3.</td><td>Escalas coerentes com recuperação; não são três medidas intercambiáveis, nem comprovam inundação em curso.</td></tr>
<tr><td>TSI-3 × TSI-6 × armazenamento individual</td><td>Paraibuna e Santa Branca têm excesso em três meses e condição normal em seis, enquanto os gráficos do ONS mostram recuperação recente. C, pp. 5–6; O, pp. 9–10.</td><td>A memória do índice e a operação modulam respostas distintas. Não concluir recomposição integral a partir do excesso trimestral.</td></tr>
<tr><td>BAM/MONAN × GEFS</td><td>Modelos, rodadas e janelas diferentes; GEFS rotula aproximadamente 112 mm em 14 dias. M, pp. 8–9; C, pp. 8–10.</td><td>Comparar área e horizonte antes de interpretar divergências. Não somar previsões sobrepostas.</td></tr>
<tr><td>Chuva prevista × MHD/GloFAS × simulação ONS</td><td>MHD/GloFAS apresentam vazão natural ou categorias; o ONS projeta 54,0% de armazenamento equivalente em Nov-final, ante 56,5% observado em Nov no mesmo painel. C, pp. 11–13; O, p. 15.</td><td>Chuva prevista pode coexistir com redução simulada de estoque. Sem premissas completas do balanço, não atribuir a diferença a uma operação específica.</td></tr>
<tr><td>Curva de segurança × estoque observado/simulado</td><td>Na página 15, os pontos observado e simulado de novembro ficam acima das referências de 16,7% e 11,6%, respectivamente.</td><td>Registrar a posição relativa, sem transformá-la em autorização de captação suplementar ou flexibilização de regras.</td></tr>
<tr><td>Consistência temporal do ONS</td><td>57,06% nas páginas 5–6 com rodapé 06/09; página 7 com rodapé 10/08; página 15 rotula Nov em 56,5%.</td><td>Manter registros separados e pedir confirmação. Não interpolar uma data comum nem corrigir o original sem manifestação da fonte.</td></tr>
<tr><td>Recuperação × CEIVAP/AGEVAP/SABESP</td><td>Há dados hidrológicos e painéis operativos, mas não quadro contemporâneo de demandas e transferências nem manifestação específica desses atores.</td><td>Não inferir aumento de atendimento ou transferência. Completar a análise com dados ou relato identificado.</td></tr>
<tr><td>Fontes compartilhadas</td><td>INPE e ONS/ANA aparecem também como insumos do CEMADEN. C, pp. 2–6 e 11.</td><td>Não contar toda concordância como confirmação estatística independente.</td></tr>
</tbody></table></div>
<h3>6.1 Prioridades para a SOE</h3>
<p><strong>Proposta analítica, não decisão:</strong> concentrar o acompanhamento na sustentação dos aportes previstos, no balanço por reservatório e na propagação a jusante. O confronto com a Resolução Conjunta nº 1.382/2015 e demais instrumentos aplicáveis requer dados operativos com referência temporal clara e a conferência dos respectivos atos; esta edição não cria nem modifica condições de operação.</p>
<p>O horizonte climático NDJ alcança janeiro de 2027, enquanto a simulação de armazenamento do ONS apresentada termina em Nov-final de 2026. Não se extrapolou a curva de segurança abril–novembro/2026 nem o armazenamento simulado para 2027. Eventual avaliação desse período exige novo cenário específico. [M, pp. 11–12; C, pp. 16–17; O, pp. 14–15]</p>
</section>'''

REG_HTML='''<section class="chapter" id="registro"><h2>7. Registro da reunião e encaminhamentos</h2>
<p><strong>Programação informada:</strong> 116ª GAOPS, 10/11/2026, às 15h00. O responsável autorizou análise e publicação incremental das apresentações recebidas, inclusive antes do início programado.</p>
<p><strong>Situação documental atualizada:</strong> recebidas e analisadas as apresentações do INPE/INMET (13 páginas), CEMADEN (17 páginas) e ONS (16 páginas). A apresentação do ONS foi incorporada nesta revisão, juntamente com sua vertical, reproduções, indicadores e cruzamentos. A pendência inicial de recebimento do ONS está superada.</p>
<p><strong>Registro do debate:</strong> não foram comunicados, até esta revisão, deliberações, novos encaminhamentos institucionais ou encerramento. Eventuais apresentações adicionais serão identificadas quando recebidas. A documentação disponível não substitui a ata, e recomendações analíticas não são decisões do colegiado.</p>
<p><strong>Pontos propostos para avaliação da equipe:</strong> esclarecer as datas dos painéis de armazenamento do ONS e as premissas da simulação de Nov-final; confirmar a anotação pluviométrica do CEMADEN e os demais desencontros documentais; complementar informações sobre transferências, demandas e condições a jusante quando disponibilizadas; registrar manifestações e decisões com atribuição e fonte. Nenhum prazo, responsável ou aprovação institucional foi presumido.</p>
<p>A identificação “NT final da reunião” será aplicada após confirmação do encerramento e consolidação do material disponível. Eventuais ajustes da equipe serão registrados em nova revisão, preservando este endereço.</p></section>'''

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frag(s):return BeautifulSoup(s,'html.parser')
def replace_section(s,id_,content):s.find(id=id_).replace_with(frag(content).section)
def table(headers,rows):
    return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+html.escape(str(x))+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def append_html(el,text):
    for node in list(frag(text).contents):el.append(node)
def get_ons(out,local=None):
    dest=out/'fontes/ons.pdf'
    for p in [Path(local) if local else ROOT/'fontes/ons.pdf',dest]:
        if p.exists() and sha(p)==ONS_SHA:
            if p.resolve()!=dest.resolve():shutil.copyfile(p,dest)
            return {'method':'verified_existing_copy','sha256':ONS_SHA,'pages':16,'matches_received_file':True}
    sess=requests.Session();sess.headers['User-Agent']='SOE-publication-source-check/1.0';views=[]
    for listing in [BASE+'apresentacoes-das-reunioes',BASE]:
        try:
            r=sess.get(listing,timeout=(8,20));r.raise_for_status()
            for a in BeautifulSoup(r.text,'html.parser').find_all('a',href=True):
                label=unquote(a['href']+' '+a.get_text(' ',strip=True)).lower()
                if 'ons' in label and any(x in label for x in ['116','20261110','10-11-2026','10112026']):views.append(urljoin(listing,a['href']))
            if views:break
        except requests.RequestException as e:print('Source listing unavailable',type(e).__name__,flush=True)
    views.extend(BASE+x for x in ['116a-reuniao-gaops-10-11-2026-apresentacao-ons.pdf/view','116a-reuniao-gaops-10-11-2026-apresentacao-ons-1.pdf/view'])
    for view in list(dict.fromkeys(views))[:6]:
        if not view.endswith('/view'):view=view.rstrip('/')+'/view'
        try:
            r=sess.get(view,timeout=(8,18));r.raise_for_status()
            urls=[urljoin(view,a['href']) for a in BeautifulSoup(r.text,'html.parser').find_all('a',href=True) if '@@download' in a['href']]
            urls.append(view[:-5]+'/@@download/file')
            for url in list(dict.fromkeys(urls))[:2]:
                rr=sess.get(url,timeout=(8,30));rr.raise_for_status()
                if hashlib.sha256(rr.content).hexdigest()!=ONS_SHA:continue
                dest.write_bytes(rr.content)
                with fitz.open(dest) as d:assert len(d)==16
                print('ONS SOURCE VERIFIED',view,url,flush=True)
                return {'view':view,'download':url,'method':'official_copy_sha256_equal_to_attachment','sha256':ONS_SHA,'pages':16,'matches_received_file':True}
        except requests.RequestException as e:print('Source attempt failed',view,type(e).__name__,flush=True)
    raise RuntimeError('Exact received ONS source could not be retrieved; existing publication must remain unchanged.')

def update_html(s):
    for e in s.select('.download-access'):e.decompose()
    for e in s.select('#ons .gallery'):e.decompose()
    s.select_one('nav a[href="#ons"]').string='ONS'
    scope=s.select_one('#executivo .scope');scope.clear();append_html(scope,'<strong>Escopo desta edição:</strong> analisados os três PDFs recebidos do INPE/INMET (13 páginas), CEMADEN (17 páginas) e ONS (16 páginas), referentes a 10/11/2026. O material do ONS está incorporado. A análise preserva as divergências de datas dos painéis de armazenamento; não atribui valores exatos a pontos gráficos sem rótulo e não presume deliberações ou encerramento.')
    for p in s.select('#executivo > p'):
        if 'A conclusão operacional permanece condicionada' in p.get_text():
            text=p.get_text().replace('A conclusão operacional permanece condicionada à incorporação do ONS e às manifestações dos participantes.','O cruzamento com o ONS foi incorporado; a interpretação operacional permanece condicionada às premissas dos cenários e às manifestações efetivamente informadas.');p.clear();p.append(text)
    old=s.find(id='sintese-ons')
    if old:old.decompose()
    syn=frag('<p id="sintese-ons"><strong>Complemento ONS:</strong> Santa Cecília apresenta vazão natural de 247% da MLT em setembro, 230% em outubro e 204% em novembro até 09/11. O painel de simulação rotula 56,5% de armazenamento equivalente observado em Nov e 54,0% simulado em Nov-final. O valor de 57,06% de outros painéis é preservado separadamente, pois há divergências nos rodapés de data. A recuperação recente não implica recomposição uniforme nem autorização de nova captação ou transferência. [O, pp. 3, 5–7 e 14–15]</p>').p
    s.select_one('#executivo .tablewrap').insert_before(syn)
    for tr in s.select('#executivo tbody tr'):
        cells=tr.find_all('td')
        if cells and cells[0].get_text()=='Operação e usos':
            cells[1].string='ONS incorporado: vazão natural, painéis operativos, curva de segurança e simulação; transferências não discriminadas.'
            cells[2].string='Preservar datas e distinguir observado, referência e simulação; não inferir novas autorizações.'
    for secid in ['inpe','cemaden']:
        for p in s.select('#'+secid+' > p'):
            text=p.get_text()
            text=text.replace('O confronto com as condições operativas aplicáveis será complementado quando forem recebidos os dados do ONS.','O confronto com os painéis do ONS está incorporado nos capítulos 5 e 6, mantendo as ressalvas temporais da fonte.')
            text=text.replace('Confrontar o excesso indicado pelo TSI com volumes, afluências e defluências contemporâneos a serem apresentados pelo ONS;','Confrontar o excesso indicado pelo TSI com os painéis de volumes, afluências e defluências do ONS já incorporados, respeitando as ressalvas temporais;')
            if text!=p.get_text():p.clear();p.append(text)
    replace_section(s,'ons',ONS_HTML);replace_section(s,'cruzamentos',CROSS_HTML);replace_section(s,'registro',REG_HTML)
    body=s.select_one('#escopo tbody')
    for row in list(body.find_all('tr')):
        if row.get('data-ons')=='1':row.decompose()
    row=frag('<tr data-ons="1"><td>ONS — observações e simulação</td><td>Santa Cecília até 09/11; armazenamento com rodapés divergentes; simulação até Nov-final/2026</td><td>Não unificar datas nem transformar a simulação em observação.</td></tr>').tr;body.append(row)
    fs=s.find(id='fontes')
    for p in fs.find_all('p',recursive=False):
        text=p.get_text()
        if text.startswith('[R]'):
            p.clear();append_html(p,'<strong>[R] Relatos do responsável:</strong> programação às 15h00; envio das apresentações de INPE/INMET, CEMADEN e, posteriormente, ONS; autorização para publicação incremental e atualização do registro. Nenhum encerramento ou deliberação adicional foi comunicado nesta revisão.')
        elif 'As duas apresentações anexadas' in text:
            p.string=text.replace('As duas apresentações anexadas','As três apresentações anexadas')
    if not fs.find(id='fonte-ons'):
        fs.h2.insert_after(frag('<p id="fonte-ons"><strong>[O] ONS:</strong> 116ª Reunião GAOPS-10-11-2026-Apresentação ONS.pdf — 16 páginas. Capa: 116ª GAOPS, 10/11/2026. Hidrologia, armazenamento, operação de quatro reservatórios e curva de segurança/simulação.</p>').p)
    if not fs.find(id='ressalvas-ons'):
        append_html(fs,'<p id="ressalvas-ons"><strong>Ressalvas do ONS:</strong> páginas 5–6 indicam 57,06% e rodapé 06/09/2026; a página 6 se estende a novembro. A página 7 informa 10/08/2026, embora mostre curva até novembro. A página 15 apresenta 56,5% em Nov e 54,0% simulado em Nov-final, sem detalhamento completo das premissas. Valores e rótulos originais foram preservados.</p>')
    return s

def add_indicators(out):
    p=out/'indicadores.csv'
    with p.open(encoding='utf-8-sig',newline='') as f:allrows=list(csv.reader(f,delimiter=';'))
    header=allrows[0];rows=[r for r in allrows[1:] if r[0]!='ONS'];added=[]
    def add(system,var,value,unit,period,nature,page,note=''):
        row=['ONS',system,var,str(value).replace('.',','),unit,period,nature,str(page),SITE+f'fontes/ons.pdf#page={page}',note];rows.append(row);added.append(row)
    for month,value in [('Maio/2026',69),('Junho/2026',79),('Julho/2026',78),('Agosto/2026',72),('Setembro/2026',247),('Outubro/2026',230),('Novembro/2026 até 09/11',204)]:
        add('Santa Cecília','Vazão natural relativa à MLT',value,'% MLT',month,'observado_parcial' if month.startswith('Novembro') else 'observado_mensal',3,'Não é defluência ou bombeamento')
    add('Sistema equivalente','Armazenamento equivalente — rótulo dos painéis',57.06,'%', 'Rodapé 06/09/2026; curva até novembro; data a confirmar','observado_rotulado_data_a_confirmar',5,'Mesmo rótulo na p. 6; não substituir 56,5% da p. 15')
    for month,value in [('Abr',57.7),('Mai',56.4),('Jun',50.8),('Jul',44.9),('Ago',38.2),('Set',30.8),('Out',23.8),('Nov',16.7),('Nov-final',11.6)]:
        add('Sistema equivalente','Curva Captação Suplementar — referência',value,'% VU',month+'/2026','referencia_operativa_apresentada',14,'Não é estoque observado nem nova autorização')
    for month,value in [('Abr',58.5),('Mai',58.9),('Jun',55),('Jul',52.1),('Ago',46.2),('Set',39.8),('Out',49),('Nov',56.5)]:
        add('Sistema equivalente','Armazenamento observado — painel de simulação',value,'% VU',month+'/2026 (rótulo mensal)','observado_no_painel',15,'Data diária não explicitada; não harmonizado com páginas 5–6')
    add('Sistema equivalente','Armazenamento simulado — Nov-final',54,'% VU','Nov-final/2026','simulacao_condicional',15,'Premissas completas não explicitadas na lâmina')
    assert len(added)==26
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(header);w.writerows(rows)
    return rows,added

def update_annex(s,added):
    sec=s.find(id='anexo-i');h=next(e for e in sec.find_all('h3') if e.get_text().startswith('I.4'))
    for e in list(h.next_siblings):e.extract()
    h.string='I.4 ONS — vazão natural em Santa Cecília'
    r=[(x[5],x[3],x[4],'O, p. 3 · '+('parcial até 09/11' if x[6]=='observado_parcial' else 'média mensal')) for x in added if x[1]=='Santa Cecília']
    append_html(sec,table(['Período','Valor','Unidade','Fonte / natureza'],r))
    append_html(sec,'<h3>I.5 ONS — armazenamento, referência e simulação</h3><p>As séries abaixo são distintas. O rótulo de 57,06% dos painéis das páginas 5–6 mantém a ressalva de data; os pontos mensais e o resultado simulado seguem a página 15.</p>')
    r=[(x[2],x[5],x[3]+' '+x[4],x[6], 'O, p. '+x[7]+'. '+x[9]) for x in added if x[1]!='Santa Cecília']
    append_html(sec,table(['Variável','Referência temporal','Valor','Natureza','Fonte / ressalva'],r))
    append_html(sec,'<h3>I.6 Operação e contribuição ao Conjuntura</h3><p>A apresentação do ONS está incorporada. Valores finais individuais de volume útil e vazões sem rótulos numéricos não foram estimados. Transferências, bombeamento e demandas específicas não estão discriminados no arquivo; campo ausente não é zero.</p><p>Para a memória anual, não somar janelas sobrepostas de chuva, não incorporar previsão ou simulação como observação, não transformar o TSI em percentual de armazenamento e não contar repetições do mesmo dado entre reuniões como observações novas. Registros com data a confirmar precisam de esclarecimento antes da consolidação anual. Esta síntese é subsídio técnico, não estatística anual homologada.</p>')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--ons-file',type=Path);args=ap.parse_args();out=args.out
    assert out.resolve()!=ROOT.resolve()
    for sub in ['fontes','assets','documentos','qa']:(out/sub).mkdir(parents=True,exist_ok=True)
    for sub in ['fontes','assets']:shutil.copytree(ROOT/sub,out/sub,dirs_exist_ok=True)
    for name in ['indicadores.csv','manifesto.json']:shutil.copyfile(ROOT/name,out/name)
    ons=get_ons(out,args.ons_file)
    s=update_html(BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser'))
    rows,added=add_indicators(out);update_annex(s,added)
    old=json.loads((ROOT/'manifesto.json').read_text());figures=[f for f in old['figures'] if f['key']!='ons'];assert len(figures)==24
    gallery=s.new_tag('div',attrs={'class':'gallery'})
    with fitz.open(out/'fontes/ons.pdf') as d:
        for pg,title,caption in ONS_FIGS:
            page=d[pg-1];pix=page.get_pixmap(matrix=fitz.Matrix(1800/page.rect.width,1800/page.rect.width),alpha=False)
            rel=f'assets/ons_{pg:02}.jpg';pix.save(out/rel,jpg_quality=93)
            f={'number':len(figures)+1,'key':'ons','page':pg,'title':title,'caption':caption,'src':rel,'width':pix.width,'height':pix.height};figures.append(f)
            append_html(gallery,f'<figure><a href="{rel}" target="_blank" rel="noopener"><img src="{rel}" width="{pix.width}" height="{pix.height}" loading="lazy" alt="{html.escape(title)}"/></a><figcaption><strong>Figura {f["number"]} — {html.escape(title)}</strong>{html.escape(caption)}<span class="source">Fonte: ONS, página {pg}. Reprodução do PDF recebido.</span><a href="fontes/ons.pdf#page={pg}">Consultar apresentação original</a></figcaption></figure>')
    s.find(id='ons').append(gallery)
    s.find(id='publication-status').string=f'PRÉVIA DOCUMENTAL 0.3 — INPE/INMET, CEMADEN e ONS incorporados; três verticais, cruzamentos, Anexo I, {len(figures)} reproduções e {len(rows)} registros numéricos. Registro documental atualizado; deliberações e encerramento não informados. NT integral e apresentações hospedadas.'
    for key,label in [('inpe','INPE/INMET'),('cemaden','CEMADEN'),('ons','ONS')]:append_html(s.find(id='fontes'),f'<p class="download-access"><a href="fontes/{key}.pdf">Apresentação integral — {label} · PDF</a></p>')
    append_html(s.find(id='anexo-i'),'<p class="download-access"><a href="documentos/Anexo_I_GAOPS_116_10-11-2026.pdf" download>Consultar somente o Anexo I · PDF</a></p>')
    code=(ROOT/'build_received.py').read_text(encoding='utf-8')
    swaps={
       'Prévia documental 0.2':'Prévia documental 0.3','PRÉVIA DOCUMENTAL 0.2':'PRÉVIA DOCUMENTAL 0.3',
       'INPE/INMET e CEMADEN analisados. ONS ainda não recebido; debate e encerramento não informados.':'INPE/INMET, CEMADEN e ONS analisados. Registro atualizado; debate e encerramento não informados.',
       '24 reproduções identificadas':'35 reproduções identificadas',
       'INPE/INMET e CEMADEN; ONS pendente. Anexo I e 24 reproduções.':'INPE/INMET, CEMADEN e ONS. Registro atualizado; Anexo I e 35 reproduções.'}
    for a,b in swaps.items():
        assert a in code,('Expected renderer text missing',a)
        code=code.replace(a,b)
    mod=types.ModuleType('gaops116_renderer');mod.__file__=str(ROOT/'build_received.py');exec(compile(code,mod.__file__,'exec'),mod.__dict__);mod.LABELS['ons']='ONS'
    analytical=BeautifulSoup(str(s),'html.parser')
    for e in analytical.select('.gallery,.download-access'):e.decompose()
    info=mod.pdf_build(analytical,out,figures)
    (out/'index.html').write_text(str(s),encoding='utf-8')
    manifest={**old,**info,'version':'0.3','status':'Prévia documental: INPE/INMET, CEMADEN e ONS incorporados; registro atualizado; encerramento não informado','generated_at':datetime.now(timezone.utc).isoformat(),'sources':{**old['sources'],'ons':ons},'figures':figures,'figure_count':len(figures),'indicator_rows':len(rows),'pdf_sha256':sha(out/'documentos'/mod.PDF),'annex_sha256':sha(out/'documentos'/mod.ANNEX),'csv_sha256':sha(out/'indicadores.csv')}
    manifest.pop('browser_checks',None)
    (out/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    text=s.get_text(' ',strip=True)
    stale=['ONS aguardado','ONS ainda aguardado','ONS pendente','ONS · pendente','ONS ainda não recebido','incorporar o ONS quando recebido','material ainda não recebido','ONS ainda não foi recebida','dois PDFs recebidos e analisados']
    for x in stale:assert x.lower() not in text.lower(),('Stale HTML status',x)
    with fitz.open(out/'documentos'/mod.PDF) as d:
        text=' '.join(p.get_text() for p in d)
        for x in stale:assert x.lower() not in text.lower(),('Stale PDF status',x)
        assert 'Vertical ONS' in text and '54,0%' in text and 'incorporada nesta revisão' in text
    assert len(s.select('figure'))==35
    assert s.select('main > section')[-1]['id']=='anexo-i'
    assert len(rows)==64
    print('COMPLETE',json.dumps({k:manifest[k] for k in ['version','figure_count','indicator_rows','pdf_pages','annex_pages','pdf_sha256']}),flush=True)
if __name__=='__main__':main()
