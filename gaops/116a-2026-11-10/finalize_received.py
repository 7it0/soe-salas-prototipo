#!/usr/bin/env python3
"""Finalize GAOPS 116 only. Preserve source bytes, existing analysis and all figures.
Publication is committed by the workflow only after all checks pass.
"""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, unquote
import argparse, csv, hashlib, html, importlib.util, inspect, json, re, shutil
import requests, fitz
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SITE = 'https://7it0.github.io/soe-salas-prototipo/gaops/116a-2026-11-10/'
BASE = 'https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/eventos-criticos/apresentacoes-das-reunioes/'
ONS_HASH = '7bef207e667eb08c522fe046e2ac9fbdaa618e7b3d1b00c803a82c310b1d9e29'
PDF = 'NT_GAOPS_116_10-11-2026_FINAL.pdf'
ANNEX = 'Anexo_I_GAOPS_116_10-11-2026.pdf'
FINAL_NOTE = 'NT final da reunião — versão 1.0, sujeita a revisão após avaliação da equipe. Eventuais ajustes serão identificados em nova revisão, mantendo este endereço.'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fragment(text):
    return BeautifulSoup(text, 'html.parser')

def replace_section(soup, key, text):
    old = soup.find(id=key)
    assert old is not None, key
    old.replace_with(fragment('<section class="chapter" id="'+key+'">'+text+'</section>').section)

def get_ons(out):
    target = out/'fontes/ons.pdf'
    if target.exists() and sha(target) == ONS_HASH:
        return {'method':'verified_existing_copy','sha256':ONS_HASH,'pages':16,'matches_received_file':True}
    session = requests.Session()
    session.headers['User-Agent'] = 'SOE-publication-source-check/1.0'
    candidates = []
    for listing in [BASE+'apresentacoes-das-reunioes', BASE]:
        try:
            r=session.get(listing,timeout=(8,25));r.raise_for_status()
            for a in BeautifulSoup(r.text,'html.parser').find_all('a',href=True):
                text=unquote(a['href']+' '+a.get_text(' ',strip=True)).lower()
                if 'ons' in text and any(x in text for x in ['116','20261110','10-11-2026','10112026']):
                    candidates.append(urljoin(listing,a['href']))
            if candidates:break
        except requests.RequestException as exc:
            print('Listing:',type(exc).__name__,flush=True)
    candidates += [BASE+'116a-reuniao-gaops-10-11-2026-apresentacao-ons.pdf/view', BASE+'116a-reuniao-gaops-10-11-2026-apresentacao-ons-1.pdf/view']
    for view in list(dict.fromkeys(candidates))[:8]:
        if not view.endswith('/view'):view=view.rstrip('/')+'/view'
        try:
            r=session.get(view,timeout=(8,20));r.raise_for_status()
            page=BeautifulSoup(r.text,'html.parser')
            downloads=[urljoin(view,a['href']) for a in page.find_all('a',href=True) if '@@download' in a['href']]
            downloads.append(view[:-5]+'/@@download/file')
            for url in list(dict.fromkeys(downloads))[:3]:
                rr=session.get(url,timeout=(8,45));rr.raise_for_status()
                if hashlib.sha256(rr.content).hexdigest()!=ONS_HASH:continue
                target.write_bytes(rr.content)
                with fitz.open(target) as d:assert len(d)==16
                return {'method':'official_copy_sha256_equal_to_attachment','view':view,'download':url,'sha256':ONS_HASH,'pages':16,'matches_received_file':True}
        except requests.RequestException as exc:
            print('ONS source:',view,type(exc).__name__,flush=True)
    raise RuntimeError('The exact received ONS PDF was not recovered. No publication may be committed.')

ONS = '''<h2>5. Vertical ONS — hidrologia, armazenamento e operação</h2>
<h3>5.1 Situação hidrológica</h3>
<p>A apresentação confirma a 116ª reunião e a data de 10/11/2026. Seu núcleo é a análise hidrológica e hidráulica do Paraíba do Sul, com vazões naturais em Santa Cecília, armazenamento equivalente, operação dos quatro reservatórios principais e curva de segurança. Não contém novo diagnóstico meteorológico próprio; a integração com chuva e previsões está na seção 6. [O, pp. 1–15]</p>
<p>A vazão natural média em Santa Cecília passou de percentuais inferiores à MLT entre maio e agosto (69%, 79%, 78% e 72%) para 247% em setembro e 230% em outubro. Novembro apresenta 204% da MLT até 09/11. A sequência caracteriza melhora frente à referência mensal da fonte, mas não significa monotonia da vazão diária: os hidrogramas mostram pulsos e recessões. A série de 2014 aparece como comparação histórica, não como previsão para os próximos meses. [O, pp. 3–4]</p>
<p>O percentual relativo à MLT não informa sozinho o valor absoluto da vazão média. Como a lâmina não fornece a base histórica da MLT nem uma tabela mensal em m³/s, esses elementos não foram inferidos de outras reuniões. Tampouco se confundiu vazão natural com vazão defluente, vazão bombeada em Santa Cecília ou água disponível para cada usuário.</p>
<h3>5.2 Indicadores, tendências e consistência temporal</h3>
<div class="tablewrap"><table><thead><tr><th>Indicador</th><th>Valor / período da fonte</th><th>Tratamento</th></tr></thead><tbody>
<tr><td>Vazão natural de Santa Cecília</td><td>Setembro: 247% da MLT; outubro: 230%; novembro: 204% até 09/11.</td><td>Novembro é parcial; meses completos permanecem separados.</td></tr>
<tr><td>Armazenamento equivalente</td><td>57,06% nas páginas 5 e 6.</td><td>Data a confirmar: rodapé 06/09/2026 em curvas que chegam a novembro.</td></tr>
<tr><td>Comparação entre anos</td><td>Curvas 2020–2026 na página 7.</td><td>Rodapé 10/08/2026 preservado; não afirmar ranking com datas desiguais.</td></tr>
<tr><td>Armazenamento observado na simulação</td><td>39,8% em Set; 49,0% em Out; 56,5% em Nov.</td><td>Marcas do gráfico, sem dia de referência especificado.</td></tr>
<tr><td>Armazenamento simulado</td><td>54,0% em Nov-final.</td><td>Resultado condicional; premissas não detalhadas no arquivo.</td></tr>
</tbody></table></div>
<p>O aumento de 49,0% para 56,5% corresponde a 7,5 pontos percentuais entre as marcas outubro e novembro da página 15. A redução de 56,5% para 54,0% corresponde a 2,5 pontos percentuais até Nov-final. São diferenças calculadas a partir dos rótulos; não constituem balanço hídrico reconstituído. O valor 57,06% das páginas 5–6 não deve substituir o 56,5% da página 15 sem confirmação dos cortes. [O, pp. 5–6 e 15]</p>
<h3>5.3 Efeitos sobre reservatórios e operação</h3>
<p><strong>Paraibuna:</strong> o volume útil apresenta recuperação no trecho final da série após o rebaixamento do período seco, acompanhada de pulsos de afluência. As defluências do segmento recente são visualmente menores que em parte dos meses anteriores, mas não há rótulo de valor final que permita fixar uma posição diária exata. [O, p. 9]</p>
<p><strong>Santa Branca:</strong> a série mostra recuperação de armazenamento após o trecho de menores estoques e mudanças na defluência ao longo do ano. A curva de volume de espera é exibida no gráfico. Sua presença não permite inferir margem atual para amortecimento sem posição temporal consistente e sem os demais critérios operativos. [O, p. 10]</p>
<p><strong>Jaguari:</strong> a trajetória de volume útil é crescente no trecho final, em paralelo a afluências com picos e defluências relativamente baixas no gráfico. O painel não discrimina transferência para o Sistema Cantareira/SABESP; não se interpreta a linha de defluência como medida dessa transferência nem como total de todas as saídas. [O, p. 11]</p>
<p><strong>Funil:</strong> há recomposição expressiva desde o fim do período seco, seguida de oscilações do armazenamento e variações de afluência/defluência. A curva de volume de espera é apresentada, mas os dados não sustentam presumir reservatório cheio, risco de inundação ou decisão de alteração de descarga. [O, p. 12]</p>
<p><strong>Inferência operacional:</strong> a melhora agregada precisa ser lida juntamente com a posição de cada reservatório, as contribuições incrementais e as condições a jusante. Uma média equivalente não substitui a análise de Paraibuna, Santa Branca, Jaguari e Funil. Os painéis operativos foram mantidos integralmente, sem produzir números exatos pela estimativa visual das curvas.</p>
<h3>5.4 Riscos e pontos de atenção</h3>
<p>O principal cuidado documental é a divergência entre os rodapés e o horizonte das curvas de armazenamento. As páginas 5–6 dizem 06/09/2026 e a página 7 diz 10/08/2026, embora mostrem evolução posterior. Pode haver rótulo remanescente de edição, mas isso não foi comprovado; a data correta não foi arbitrada nesta NT. [O, pp. 5–7]</p>
<p>O cenário de Nov-final indica estoque inferior à marca Nov mesmo com a recuperação hidrológica recente. Isso não é contradição automática com chuva prevista ou TSI positivo: as variáveis e os horizontes são distintos, e o armazenamento resulta do balanço entre entradas e saídas. O arquivo não informa premissas quantitativas suficientes para reconstituir esse balanço ou avaliar a probabilidade do resultado. [O, p. 15; C, pp. 9 e 12]</p>
<p>A simulação operativa termina em novembro de 2026. Não há neste material curva de estoque de dezembro/janeiro nem avaliação operativa completa de 2027. Os produtos sazonais do INPE/INMET e CEMADEN podem orientar acompanhamento, mas não preenchem essa lacuna documental do ONS. [M, p. 12; C, p. 17; O, p. 15]</p>
<h3>5.5 Implicações regulatórias para ANA/GAOPS</h3>
<p>A apresentação denomina a referência de “Curva de Segurança Paraíba do Sul — Operação Normal”, aplicável de abril a novembro de 2026, com legenda “Curva Captação Suplementar”. Os valores são 57,7% em abril, 56,4% em maio, 50,8% em junho, 44,9% em julho, 38,2% em agosto, 30,8% em setembro, 23,8% em outubro, 16,7% em novembro e 11,6% em Nov-final. Tratam-se dos pontos reproduzidos da fonte, não de nova curva estabelecida por esta NT. [O, p. 14]</p>
<p>Na comparação gráfica, o estoque observado/simulado permanece acima da curva nos pontos apresentados. Essa constatação não é autorização automática de captação suplementar nem declaração de cumprimento integral das regras. O eventual cotejo com a Resolução Conjunta nº 1.382/2015 e demais atos aplicáveis demanda os instrumentos e dados operativos pertinentes; este PDF não os transcreve nem apresenta verificação de conformidade. Não foram importados limites de outras reuniões.</p>
<p>Para a interface CEIVAP/AGEVAP e SABESP, não há neste arquivo quantificação de demandas, bombeamentos ou transferências, nem manifestação institucional específica desses participantes. Qualquer ajuste associado aos usos múltiplos deve ser registrado separadamente quando informado, com fonte e atribuição, sem converter análise técnica em decisão administrativa.</p>
<h3>5.6 Recomendações analíticas e decisões</h3>
<p><strong>Propostas para avaliação da equipe:</strong> confirmar a data dos 57,06% e a referência dos 56,5%; obter as premissas da simulação de 54,0% em Nov-final; acompanhar individualmente os quatro reservatórios e os pontos a jusante; esclarecer dados de transferências/demandas quando necessários; distinguir previsões até janeiro dos cenários operativos apresentados apenas até novembro.</p>
<p><strong>Decisões:</strong> nenhuma nova deliberação específica foi informada pelo responsável para esta consolidação. As recomendações acima são analíticas; não se registrou aprovação de vazão, de captação, de transferência ou de regra em nome do GAOPS.</p>'''

CROSS = '''<h2>6. Cruzamentos técnicos e consequências operacionais</h2>
<p>Os cruzamentos a seguir combinam os três arquivos recebidos. A concordância entre produtos não elimina diferenças de variável, escala, área, corte temporal ou fontes compartilhadas; as interpretações integradas são identificadas como análise desta NT.</p>
<div class="tablewrap"><table><thead><tr><th>Cruzamento</th><th>Convergência / diferença identificada</th><th>Consequência operacional ou cuidado</th></tr></thead><tbody>
<tr><td>INPE/INMET × CEMADEN × ONS — diagnóstico</td><td>Anomalias positivas em setembro/outubro; seis TSI-3 em excesso; Santa Cecília em 247% e 230% da MLT. [M, p. 5; C, p. 6; O, p. 3]</td><td>Convergência qualitativa de recuperação recente; não converter TSI ou vazão natural em volume útil.</td></tr>
<tr><td>TSI-3 × TSI-6 × reservatórios</td><td>Santa Branca, Paraibuna e Ilha dos Pombos estão em excesso no TSI-3 e normais no TSI-6. ONS mostra recuperação não uniforme dos estoques individuais. [C, pp. 5–6; O, pp. 6 e 9–12]</td><td>Memórias e variáveis diferentes; o índice de excesso não significa reservatório cheio.</td></tr>
<tr><td>Chuva prevista × armazenamento simulado</td><td>GEFS indica ≈112 mm em 14 dias; ONS projeta 54,0% em Nov-final, contra 56,5% observado na marca Nov. [C, p. 9; O, p. 15]</td><td>Sem contradição automática: entradas previstas não determinam o saldo de armazenamento. Premissas operativas precisam ser explicitadas.</td></tr>
<tr><td>MHD/GloFAS × vazões ONS</td><td>MHD prevê vazões naturais de 07/11 a 07/12; ONS descreve vazões naturais e operação. Cortes e métricas são diferentes. [C, pp. 11–13; O, pp. 3 e 9–12]</td><td>Comparação quantitativa exige série, horizonte e referência harmonizados; não substituir defluência pelo cenário natural.</td></tr>
<tr><td>Estoque equivalente × curva de segurança</td><td>Na p. 15, Nov: 56,5% versus curva 16,7%; Nov-final: simulação 54,0% versus curva 11,6%. [O, pp. 14–15]</td><td>Condição gráfica acima da referência no horizonte; não é autorização automática ou demonstração de disponibilidade para uso adicional.</td></tr>
<tr><td>57,06% × 56,5% — consistência interna</td><td>57,06% nas pp. 5–6 com rodapé 06/09; 56,5% na marca Nov da p. 15. A p. 7 traz rodapé 10/08.</td><td>Não escolher, promediar ou corrigir silenciosamente. Solicitar a data de cada informação.</td></tr>
<tr><td>Sazonal NDJ × horizonte ONS</td><td>Meteorologia/hidrologia sazonal alcança janeiro/2027; a simulação operativa encerra-se em Nov-final. [M, p. 12; C, p. 17; O, p. 15]</td><td>Há lacuna de projeção operativa para dezembro/janeiro; não extrapolar a trajetória de estoque.</td></tr>
<tr><td>Usos múltiplos × informação recebida</td><td>ONS não fornece quadro de transferências SABESP, bombeamento em Santa Cecília ou demandas CEIVAP/AGEVAP.</td><td>Manter campos não informados; não estimar transferência pela linha de defluência de Jaguari.</td></tr>
<tr><td>Insumos compartilhados</td><td>CEMADEN utiliza precipitação INPE e vazões ONS/ANA no TSI. [C, pp. 2–6]</td><td>Convergência documental não equivale a três confirmações estatisticamente independentes.</td></tr>
</tbody></table></div>
<h3>6.1 Prioridades de acompanhamento</h3>
<p><strong>Curto prazo:</strong> confrontar chuva efetiva com previsões nas áreas contribuintes; observar os pulsos de afluência e as respostas individuais de Paraibuna, Santa Branca, Jaguari e Funil. A classificação de excesso hídrico não é evidência suficiente de cheia com impacto ou esgotamento do volume de espera.</p>
<p><strong>Até o fim de novembro:</strong> avaliar a realização do cenário do ONS e esclarecer seus pressupostos. A comparação com a curva de segurança deve permanecer vinculada ao horizonte e aos instrumentos operativos, sem supor prorrogação automática para meses posteriores.</p>
<p><strong>Para dezembro e janeiro:</strong> acompanhar os sinais sazonais e solicitar cenário operativo específico, caso necessário à avaliação da equipe. O conjunto atual não quantifica uma trajetória de armazenamento para 2027.</p>
<p><strong>Articulação e registro:</strong> manifestações de CEIVAP/AGEVAP, SABESP e demais participantes somente são atribuídas quando documentadas ou relatadas pelo responsável. Nenhum novo encaminhamento vinculante foi presumido nesta edição.</p>'''

REGISTER = '''<h2>7. Registro da reunião e encaminhamentos</h2>
<p><strong>Identificação:</strong> 116ª Reunião do GAOPS, de 10/11/2026, com início programado às 15h00. A análise documental e a publicação incremental foram autorizadas pelo responsável.</p>
<p><strong>Situação documental:</strong> recebidas e analisadas as apresentações INPE/INMET (13 páginas), CEMADEN (17 páginas) e ONS (16 páginas). O material do ONS está incorporado à vertical técnica, aos cruzamentos, às reproduções e ao Anexo I. Não permanece pendência de recebimento do ONS.</p>
<p><strong>Encerramento:</strong> confirmado pelo responsável pelo acompanhamento nesta conversa. Não foram comunicadas deliberações específicas adicionais para inclusão nesta consolidação. O recebimento dos materiais e o encerramento não constituem aprovação de cenários, alteração de regra, determinação de vazão ou autorização de transferência. [R1]</p>
<p><strong>Recomendações analíticas para avaliação da equipe:</strong> confirmar os cortes dos gráficos de armazenamento do ONS; esclarecer as premissas da simulação até Nov-final; completar informações de usos múltiplos e transferências quando necessárias; manter as ressalvas documentais do INPE/INMET e CEMADEN. Não foram arbitrados responsáveis ou prazos institucionais.</p>
<p><strong>Controle de versão:</strong> NT final da reunião — versão 1.0, sujeita a revisão após avaliação da equipe. Eventuais ajustes deverão ser identificados em nova revisão, mantendo o endereço compartilhado. Esta consolidação não substitui a ata nem constitui publicação institucional da ANA.</p>'''

ONS_FIGS = [
 (3,'Santa Cecília — vazões naturais e percentuais da MLT','Novembro parcial até 09/11; não é vazão defluente.'),
 (4,'Santa Cecília — hidrograma de 2026','Comparação com 2014; não é previsão.'),
 (5,'Armazenamento equivalente histórico','57,06%; rodapé 06/09/2026 em curva posterior. Data a confirmar.'),
 (6,'Armazenamentos dos quatro reservatórios e equivalente','Posições individuais distintas; rodapé 06/09/2026 a confirmar.'),
 (7,'Armazenamento equivalente — comparação entre anos','Rodapé 10/08/2026; não atribuir ranking sem harmonizar os cortes.'),
 (9,'Operação da UHE Paraibuna','Afluência, defluência e volume útil; sem rótulo exato de posição final.'),
 (10,'Operação da UHE Santa Branca','Volume de espera é curva de referência; não é margem de amortecimento calculada.'),
 (11,'Operação da UHE Jaguari','A defluência do gráfico não é uma medida de transferência para a SABESP.'),
 (12,'Operação da UHE Funil','Oscilações de estoque e vazões; sem inferência de inundação ou nova determinação.'),
 (14,'Curva de segurança — operação normal','Abril a novembro/2026; curva Captação Suplementar conforme apresentada.'),
 (15,'Simulação do sistema equivalente','Nov: 56,5% observado; Nov-final: 54,0% simulado. Não extrapolar para 2027.')]

def update_analysis(soup):
    soup.find(id='publication-status').string='NT FINAL DA REUNIÃO — versão 1.0. Reunião encerrada, conforme informação do responsável. INPE/INMET, CEMADEN e ONS incorporados; três verticais, cruzamentos, Anexo I, 35 reproduções e 64 registros numéricos. Ressalvas documentais preservadas. Sujeita à revisão da equipe.'
    soup.select_one('nav a[href="#ons"]').string='ONS'
    soup.find(id='pdf-action')['href']='documentos/'+PDF
    soup.find(id='pdf-action').string='NT final da reunião · PDF'
    soup.select_one('header a[href="#executivo"]').string='Ler NT final da reunião no site'
    for p in soup.select('header p.small'):p.string=FINAL_NOTE
    for node in list(soup.find('header').find_all(string=True)):
        if 'início previsto às' in node:node.replace_with(str(node).replace('início previsto às','início programado às'))
    scope=soup.find(id='executivo').find('p',class_='scope')
    scope.clear();scope.append(fragment('<strong>Escopo e encerramento:</strong> esta consolidação reúne INPE/INMET (13 páginas), CEMADEN (17 páginas) e ONS (16 páginas), recebidos para a 116ª GAOPS de 10/11/2026. O responsável confirmou o encerramento. A pendência inicial do ONS está superada. As ressalvas sobre datas de armazenamento permanecem explícitas. NT final da reunião, sujeita à revisão da equipe. [R1]'))
    for p in soup.find(id='executivo').find_all('p'):
        if 'A conclusão operacional permanece condicionada' in p.get_text():
            text=str(p).replace('A conclusão operacional permanece condicionada à incorporação do ONS e às manifestações dos participantes.','O material do ONS está incorporado à avaliação de armazenamento, operação e segurança, com as ressalvas documentais registradas.');p.replace_with(fragment(text).p)
    additions='''<p><strong>ONS — recuperação hidrológica:</strong> Santa Cecília apresenta 247% da MLT em setembro, 230% em outubro e 204% em novembro até 09/11. Há convergência qualitativa com a melhora da chuva e do TSI, sem transformar vazão natural em armazenamento ou disponibilidade adicional. [O, p. 3; M, p. 5; C, pp. 5–6]</p>
<p><strong>Armazenamento e data:</strong> os 57,06% apresentados nas páginas 5–6 do ONS mantêm o rodapé 06/09/2026, embora as curvas avancem até novembro. A página 7 registra 10/08/2026. Os cortes precisam ser confirmados; não se atribui silenciosamente uma data atual a esses valores. [O, pp. 5–7]</p>
<p><strong>Simulação:</strong> a página 15 registra 56,5% observado na marca Nov e 54,0% simulado em Nov-final. A diferença de 2,5 pontos percentuais é cálculo desta análise, não balanço hídrico reconstituído nem intervalo probabilístico. A curva de segurança apresentada é 16,7% em Nov e 11,6% em Nov-final; estar acima dela não constitui autorização automática de captação, transferência ou alteração operativa. O cenário termina em novembro, não sendo extrapolado para 2027. [O, pp. 14–15]</p>'''
    soup.find(id='executivo').find('div',class_='tablewrap').insert_before(fragment(additions))
    for tr in soup.find(id='executivo').select('tbody tr'):
        cells=tr.find_all('td')
        if cells and cells[0].get_text()=='Operação e usos':
            cells[1].string='ONS incorporado: armazenamento equivalente, quatro reservatórios e simulação. Transferências/demandas não quantificadas.'
            cells[2].string='Confirmar cortes e premissas; não estimar transferências pela defluência de Jaguari.'
        if cells and cells[0].get_text()=='Qualidade documental':
            cells[1].string='Percentual de novembro; BAM/MONAN; GloFAS; rodapés de armazenamento ONS.'
    esc=soup.find(id='escopo')
    esc.find('p').insert_after(fragment('<p>[O] identifica o PDF ONS “116ª Reunião GAOPS-10-11-2026-Apresentação ONS.pdf”, com 16 páginas. Valores sem rótulos nos gráficos não foram convertidos em posições diárias exatas.</p>'))
    esc.select_one('tbody').append(fragment('<tr><td>ONS — vazão natural</td><td>Maio–outubro; novembro até 09/11/2026.</td><td>% MLT conforme fonte; base histórica não explicitada na lâmina.</td></tr><tr><td>ONS — armazenamento</td><td>57,06%; rodapés 06/09 e 10/08/2026.</td><td>Cortes a confirmar; curvas com evolução posterior.</td></tr><tr><td>ONS — curva de segurança e simulação</td><td>Abril a novembro/2026; Nov-final.</td><td>Separar observado, referência e simulação. Não extrapolar para 2027.</td></tr>'))
    changes={
      'O confronto com as condições operativas aplicáveis será complementado quando forem recebidos os dados do ONS.':'O confronto documental com o material do ONS está incorporado na seção 6; a apresentação não detalha todos os condicionantes e usos múltiplos.',
      'Confrontar o excesso indicado pelo TSI com volumes, afluências e defluências contemporâneos a serem apresentados pelo ONS;':'Confrontar o excesso indicado pelo TSI com os gráficos operativos recebidos do ONS, preservando ressalvas de data e a ausência de rótulos exatos dos valores finais;'
    }
    for p in soup.select('#inpe p,#cemaden p'):
        text=str(p)
        for old,new in changes.items():text=text.replace(old,new)
        if text!=str(p):p.replace_with(fragment(text).p)
    replace_section(soup,'ons',ONS)
    replace_section(soup,'cruzamentos',CROSS)
    replace_section(soup,'registro',REGISTER)
    sources=soup.find(id='fontes')
    for p in sources.find_all('p'):
        text=p.get_text(' ',strip=True)
        if text.startswith('[R]'):
            p.clear();p.append('[R1] Relato do responsável nesta conversa: encerramento da 116ª GAOPS; autorização de publicação dos materiais recebidos. Nenhuma deliberação específica adicional foi comunicada para inclusão.')
        elif text.startswith('As duas apresentações'):
            p.string='As três apresentações anexadas são a base documental. Referências a NOAA, ECMWF, INMET, INPE e ANA/ONS dentro das lâminas identificam a origem dos produtos/dados e não confirmam participação adicional nesta reunião.'
    sources.append(fragment('<p>[O] ONS: 116ª Reunião GAOPS-10-11-2026-Apresentação ONS.pdf — 16 páginas. Análise hidrológica e hidráulica da bacia do Rio Paraíba do Sul, 10/11/2026. As datas dos rodapés das páginas 5–7 permanecem pendentes de confirmação, não de recebimento.</p><p class="download-access"><a href="fontes/ons.pdf">Apresentação integral — ONS · PDF</a></p>'))


def append_data(out,soup):
    file=out/'indicadores.csv'
    with file.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.reader(f,delimiter=';'))
    assert len(rows)==39,'Unexpected pre-ONS indicator count'
    extra=[]
    def add(local,var,value,unit,period,nature,pg,note):
        row=['ONS',local,var,str(value).replace('.',','),unit,period,nature,str(pg),SITE+f'fontes/ons.pdf#page={pg}',note];extra.append(row)
    monthly=[('Maio',69),('Junho',79),('Julho',78),('Agosto',72),('Setembro',247),('Outubro',230),('Novembro',204)]
    for month,value in monthly:
        partial=month=='Novembro';add('Santa Cecília','Vazão natural relativa à MLT',value,'% MLT',month+'/2026'+(' até 09/11' if partial else ''),'observado_parcial' if partial else 'observado_mensal',3,'Base da MLT não explicitada na lâmina. Não é defluência.')
    add('Sistema equivalente Paraíba do Sul','Armazenamento equivalente apresentado','57,06','% VU equivalente','Data a confirmar: rodapé 06/09/2026; curva até novembro','observado_data_pendente',5,'Valor repetido na p. 6; não atribuído a 09/11 nem reconciliado com 56,5%.')
    curve=[('Abr',57.7,58.5),('Mai',56.4,58.9),('Jun',50.8,55.0),('Jul',44.9,52.1),('Ago',38.2,46.2),('Set',30.8,39.8),('Out',23.8,49.0),('Nov',16.7,56.5),('Nov-final',11.6,54.0)]
    for month,safety,stock in curve:
        add('Sistema equivalente Paraíba do Sul','Curva de segurança — Captação Suplementar',safety,'% VU equivalente',month+'/2026','referencia_operativa_apresentada',14,'Aplicação abril a novembro; não é autorização nem novo limite desta NT.')
        simulated=month=='Nov-final'
        add('Sistema equivalente Paraíba do Sul','Armazenamento simulado' if simulated else 'Armazenamento observado — marca mensal',stock,'% VU equivalente',month+'/2026','simulacao_condicional' if simulated else 'observado_marca_mensal',15,'Sem dia de referência explicitado; premissas da simulação não detalhadas.')
    assert len(extra)==26
    with file.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f,delimiter=';').writerows(rows+extra)
    ann=soup.find(id='anexo-i')
    for p in list(ann.find_all('p')):
        if p.get_text(' ',strip=True).startswith('ONS pendente:'):p.decompose()
    h=ann.find('h3',string=re.compile('I.4'))
    h.string='I.4 ONS — vazões, armazenamento e curva de segurança'
    rainrows=''.join('<tr><td>Santa Cecília — '+month+'/2026'+(' até 09/11' if month=='Novembro' else '')+'</td><td>'+str(value)+'% MLT</td><td>'+('Observado parcial' if month=='Novembro' else 'Observado mensal')+'</td><td>ONS, p. 3. Vazão natural, não defluência.</td></tr>' for month,value in monthly)
    curve_rows=''.join('<tr><td>'+month+'/2026</td><td>'+str(safety).replace('.',',')+'%</td><td>'+str(stock).replace('.',',')+'%</td><td>'+('Simulado' if month=='Nov-final' else 'Observado na marca mensal')+'</td><td>ONS, pp. 14–15; dia de referência não especificado.</td></tr>' for month,safety,stock in curve)
    tables='<div class="tablewrap"><table><thead><tr><th>Recorte / período</th><th>Valor</th><th>Natureza</th><th>Fonte / ressalva</th></tr></thead><tbody>'+rainrows+'<tr><td>Armazenamento equivalente — data a confirmar</td><td>57,06% VU</td><td>Valor apresentado; corte pendente</td><td>ONS, pp. 5–6; rodapé 06/09/2026 em curvas até novembro.</td></tr></tbody></table></div><div class="tablewrap"><table><thead><tr><th>Marca temporal</th><th>Curva de segurança</th><th>Armazenamento</th><th>Natureza do estoque</th><th>Fonte / ressalva</th></tr></thead><tbody>'+curve_rows+'</tbody></table></div><p>As referências da curva não são novas autorizações. O cenário encerra-se em novembro e não é extrapolado para 2027. Não há quadro numérico de demandas ou transferências SABESP/CEIVAP; ausência de dado não é zero. Valores finais sem rótulo nos painéis individuais não foram estimados.</p>'
    h.insert_after(fragment(tables))
    return len(rows)-1+len(extra)


def figures(out,soup,manifest):
    selected=list(manifest['figures'])
    gallery=soup.new_tag('div',attrs={'class':'gallery'})
    with fitz.open(out/'fontes/ons.pdf') as doc:
        for pg,title,caption in ONS_FIGS:
            page=doc[pg-1];pix=page.get_pixmap(matrix=fitz.Matrix(1800/page.rect.width,1800/page.rect.width),alpha=False)
            rel=f'assets/ons_{pg:02}.jpg';pix.save(out/rel,jpg_quality=93)
            f={'number':len(selected)+1,'key':'ons','page':pg,'title':title,'caption':caption,'src':rel,'width':pix.width,'height':pix.height};selected.append(f)
            markup=f'<figure><a href="{rel}" target="_blank" rel="noopener"><img src="{rel}" width="{pix.width}" height="{pix.height}" alt="{html.escape(title)}" loading="lazy"/></a><figcaption><strong>Figura {f["number"]} — {html.escape(title)}</strong>{html.escape(caption)}<span class="source">Fonte: ONS, página {pg}. Reprodução do PDF recebido.</span><a href="fontes/ons.pdf#page={pg}">Consultar apresentação original</a></figcaption></figure>'
            gallery.append(fragment(markup).figure)
    soup.find(id='ons').append(gallery)
    assert len(selected)==35 and len(soup.select('figure'))==35
    return selected


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();out=args.out
    assert out.resolve()!=ROOT.resolve()
    out.mkdir(parents=True,exist_ok=True)
    for directory in ['assets','fontes','documentos']:
        shutil.copytree(ROOT/directory,out/directory,dirs_exist_ok=True)
    (out/'qa').mkdir(exist_ok=True)
    for file in ['index.html','indicadores.csv','manifesto.json']:shutil.copy2(ROOT/file,out/file)
    raw=(out/'index.html').read_bytes()
    current=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert current=='d226d2c38ebacdad0b2b67880c80f70b9b6366fb','Concurrent edit: refresh before publishing'
    m=json.loads((out/'manifesto.json').read_text())
    for key in ['inpe','cemaden']:assert sha(out/'fontes'/f'{key}.pdf')==m['sources'][key]['sha256']
    m['sources']['ons']=get_ons(out)
    soup=BeautifulSoup(raw.decode('utf-8'),'html.parser')
    update_analysis(soup)
    count=append_data(out,soup)
    selected=figures(out,soup,m)
    assert count==64
    txt=soup.get_text(' ',strip=True).lower()
    for obsolete in ['ons aguardado','ons ainda não recebido','ons ainda aguardado','ons · pendente','ons pendente:','encerramento não informado','não há registro de encerramento']:
        assert obsolete not in txt,obsolete
    assert soup.select('main > section')[-1]['id']=='anexo-i'
    spec=importlib.util.spec_from_file_location('original_builder',ROOT/'build_received.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    builder.LABELS['ons']='ONS';builder.PDF=PDF;builder.ANNEX=ANNEX
    code=inspect.getsource(builder.pdf_build)
    edits={
      'Prévia documental 0.2':'NT final da reunião 1.0',
      'PRÉVIA DOCUMENTAL 0.2':'NT FINAL DA REUNIÃO — VERSÃO 1.0',
      'INPE/INMET e CEMADEN analisados. ONS ainda não recebido; debate e encerramento não informados.':'INPE/INMET, CEMADEN e ONS incorporados. Encerramento confirmado pelo responsável. Sujeita à revisão da equipe.',
      '24 reproduções':'35 reproduções',
      'INPE/INMET e CEMADEN; ONS pendente.':'INPE/INMET, CEMADEN e ONS; reunião encerrada.'
    }
    for old,new in edits.items():
        assert old in code,old
        code=code.replace(old,new)
    exec(compile(code,str(ROOT/'build_received.py'),'exec'),builder.__dict__)
    analytical=BeautifulSoup(str(soup),'html.parser')
    for el in analytical.select('.gallery,.download-access'):el.decompose()
    info=builder.pdf_build(analytical,out,selected)
    # Keep the already shared PDF address working, but serve the final contents.
    shutil.copy2(out/'documentos'/PDF,out/'documentos/NT_GAOPS_116_10-11-2026_PREVIA.pdf')
    (out/'index.html').write_text(str(soup),encoding='utf-8')
    for el in soup.select('[href],[src]'):
        for attr in ['href','src']:
            u=el.get(attr,'')
            if not u or u.startswith(('http:','https:','mailto:','#','../../')):continue
            assert (out/unquote(u.split('#')[0])).is_file(),u
    with fitz.open(out/'documentos'/PDF) as d:
        text='\n'.join(page.get_text() for page in d)
        assert 'Encerramento:' in text and 'ONS' in text and '57,06%' in text
        assert 'ONS ainda não recebido' not in text
    m.update({'version':'1.0','status':'NT final da reunião; encerramento confirmado; INPE/INMET, CEMADEN e ONS incorporados; sujeita à revisão da equipe','generated_at':datetime.now(timezone.utc).isoformat(),'figure_count':35,'indicator_rows':64,'figures':selected,**info,'pdf_sha256':sha(out/'documentos'/PDF),'annex_sha256':sha(out/'documentos'/ANNEX),'csv_sha256':sha(out/'indicadores.csv'),'checks':{'source_hashes_match_attachments':True,'all_local_links_exist':True,'old_pending_ons_labels_removed':True,'meeting_closure_recorded':True,'text_and_tables_preserved':info['text_and_tables_preserved']}})
    (out/'manifesto.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in m.items() if k not in ['figures','toc','sources']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
