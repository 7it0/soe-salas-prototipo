#!/usr/bin/env python3
"""Build the cross-basin publication index using verified meeting pages.
Only creates salas/index.html and salas/reunioes.json. Does not rewrite NTs.
PDF and data buttons are emitted only for files that really exist.
"""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote
import html, json, posixpath, re
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'salas'
MEETINGS=[
 dict(group='Alto Paraguai · Pantanal',slug='pantanal',date='2026-10-21',number='13ª',title='13ª Reunião de Avaliação das Condições Hidrometeorológicas da Bacia do Alto Paraguai (Pantanal)',page='pantanal/13a-2026-10-21/index.html',state='Consolidação após encerramento',edition='Edição web 2.1',description='Quatro verticais, integração das condições do Pantanal e avaliação da operação de Manso.'),
 dict(group='Paraíba do Sul · GAOPS',slug='paraiba-do-sul',date='2026-10-13',number='115ª',title='115ª Reunião do GAOPS — Paraíba do Sul',page='gaops-20261013/nt-final.html',state='NT consolidada',edition='Versão integral',description='Condições hidrometeorológicas, operação do sistema e integração das apresentações do INPE/INMET, CEMADEN e ONS.'),
 dict(group='Paraná · Região Hidrográfica',slug='parana',date='2026-10-29',number='10ª',title='10ª Reunião em 2026 da Sala de Acompanhamento do Sistema Hídrico da Região Hidrográfica do Paraná',page='parana/10a-2026-10-29/index.html',state='Consolidação documental · debate em aberto',edition='Edição 1.0',description='Três verticais, cruzamentos por sub-bacia e quadro de indicadores dos reservatórios e da operação.'),
 dict(group='Paranapanema',slug='paranapanema',date='2026-10-22',number='10ª',title='10ª Reunião em 2026 da Sala de Acompanhamento do Sistema Hídrico do Rio Paranapanema',page='paranapanema/10a-2026-10-22/index.html',state='Consolidação documental',edition='Revisão 1.1',description='Verticais CEMADEN e ONS, gestão da cascata, cruzamentos técnicos e Anexo I — Reunião em números.'),
 dict(group='Região Norte',slug='regiao-norte',date='2026-10-23',number='4ª',title='4ª Reunião de Avaliação das Condições Hidrometeorológicas da Região Norte',page='regiao-norte/4a-2026-10-23/index.html',state='Consolidação após encerramento',edition='Revisão 1.1',description='Cinco verticais institucionais, análise por bacia, quadro executivo e síntese numérica para a memória anual.'),
 dict(group='Região Norte',slug='regiao-norte',date='2026-09-25',number='3ª',title='3ª Reunião de Avaliação das Condições Hidrometeorológicas da Região Norte',page='index.html',state='NT consolidada',edition='Publicação histórica',description='Síntese integrada de INPE/INMET, CENSIPAM/SipamHidro, SGB/CPRM e ONS. Endereço histórico preservado.'),
 dict(group='Região Sul',slug='regiao-sul',date='2026-10-27',number='9ª',title='9ª Reunião em 2026 da Sala de Crise da Região Sul',page='regiao-sul/9a-2026-10-27/index.html',state='Prévia técnica',edition='Versão 0.2',description='Quatro verticais, acompanhamento de cheias, operação dos reservatórios e Anexo I. Encerramento não registrado nesta edição.'),
 dict(group='São Francisco',slug='sao-francisco',date='2026-10-06',number='10ª',title='10ª Reunião em 2026 da Sala de Acompanhamento do Sistema Hídrico do Rio São Francisco',page='sao-francisco-20261006/index.html',read_page='sao-francisco-20261006/NT_10a_Reuniao_Sao_Francisco_06-10-2026.html',state='NT final',edition='Consolidação da reunião',description='Transição para o período chuvoso, condições hidrológicas, operação dos reservatórios e usos múltiplos.'),
 dict(group='Tocantins',slug='tocantins',date='2026-10-27',number='10ª',title='10ª Reunião em 2026 da Sala de Acompanhamento do Sistema Hídrico do Rio Tocantins',page='tocantins/10a-2026-10-27/index.html',state='Prévia técnica',edition='Versão 0.2',description='Verticais CEMADEN e ONS, operação da cascata e cenários de Serra da Mesa. Apresentação do INMET não recebida nesta edição.'),
]

def esc(value):return html.escape(str(value),quote=True)
def local_ref(page,href):
    u=urlsplit(href)
    if u.scheme or u.netloc:return None
    path=posixpath.normpath(posixpath.join(posixpath.dirname(page),unquote(u.path))) if u.path else page
    if path=='..' or path.startswith('../'):return None
    target=ROOT/path
    if target.is_dir():target=target/'index.html';path=str(target.relative_to(ROOT))
    return path if target.is_file() else None

def href(path):return '../'+path

def assemble():
    records=[]
    for src in MEETINGS:
        item=dict(src);page=ROOT/item['page'];assert page.is_file(),str(page)
        soup=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser')
        item['read_page']=item.get('read_page',item['page'])
        assert (ROOT/item['read_page']).is_file()
        item['pdf']=None;item['csv']=None;item['annex']=None
        for a in soup.select('a[href]'):
            link=a['href'];target=local_ref(item['page'],link)
            if not target:continue
            label=a.get_text(' ',strip=True).lower();name=Path(target).name.lower()
            if name.endswith('.pdf') and ('nt_' in name or 'nota' in label or 'nt completa' in label) and 'anexo' not in name:
                if item['pdf'] is None:item['pdf']=target
            if name=='indicadores.csv':item['csv']=target
        # A newly hosted Paraná PDF is made available without manual catalog edits.
        known=page.parent/'documentos'/'NT_Parana_10a_29-10-2026_CONSOLIDACAO.pdf'
        if item['slug']=='parana' and known.is_file():item['pdf']=str(known.relative_to(ROOT))
        if soup.find(id='anexo-i'):item['annex']=item['page']+'#anexo-i'
        item['date_br']='/'.join(reversed(item['date'].split('-')))
        records.append(item)
    assert len({(x['group'],x['date'],x['number']) for x in records})==len(records)
    return records

CSS='''
:root{--ink:#183847;--teal:#07566a;--muted:#526b76;--line:#d6e3e7;--bg:#f3f7f8;--green:#d5f2e7}*{box-sizing:border-box}html{scroll-padding-top:28px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}a{color:var(--teal)}header{background:linear-gradient(115deg,#073e55,#08746e);color:#fff;padding:48px max(24px,calc((100vw - 1160px)/2)) 36px}.eyebrow{font-size:12px;letter-spacing:.15em;text-transform:uppercase}h1{font-size:clamp(30px,4vw,46px);line-height:1.15;margin:15px 0}.lead{font-size:19px;max-width:850px;margin:18px 0}.credit{border-left:3px solid #9ad9cd;padding-left:16px;font-size:13px;line-height:1.7;margin:24px 0}.credit strong{font-size:16px}.metrics{display:flex;gap:16px;flex-wrap:wrap;margin-top:26px}.metric{background:#ffffff14;border:1px solid #ffffff36;border-radius:7px;padding:12px 19px;min-width:160px}.metric b{display:block;font-size:27px;line-height:1.1}.metric span{font-size:13px}main{max-width:1210px;margin:auto;padding:30px 24px 50px}.overview{background:white;border:1px solid var(--line);border-radius:10px;padding:24px;margin-bottom:28px}h2{font-size:26px;line-height:1.25;color:var(--teal);margin:0 0 12px}h3{font-size:19px;line-height:1.4;margin:12px 0;color:var(--teal)}.basins{display:flex;gap:9px;flex-wrap:wrap;margin:20px 0}.basins a{border:1px solid #bed6dd;border-radius:6px;padding:7px 12px;text-decoration:none;background:#f3f8f9;font-weight:600;font-size:14px}.search{display:flex;align-items:end;gap:12px;flex-wrap:wrap;margin-top:22px}.search label{display:block;font-weight:650;margin-bottom:7px}.search .inputbox{flex:1;min-width:210px}.search input{width:100%;padding:12px 14px;border:1px solid #a7bec7;border-radius:6px;font:inherit}.search button{border:1px solid #a7bec7;padding:12px 16px;background:white;color:var(--teal);border-radius:6px;font:inherit;cursor:pointer}.count,.small{font-size:13px;color:var(--muted)}.basin{margin-top:32px;scroll-margin-top:24px}.basin-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;border-bottom:2px solid #bfd6dc;padding-bottom:8px;margin-bottom:16px}.basin-head h2{margin:0}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.meeting{background:white;border:1px solid var(--line);border-left:4px solid #138696;border-radius:9px;padding:24px;min-width:0}.meta{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:13px}.date{font-weight:700;color:var(--teal)}.badge{background:#e9f4ef;color:#265f4f;padding:2px 9px;border-radius:5px;font-size:12px}.badge.pending{background:#fff1d7;color:#71541d}.description{font-size:15px;color:var(--muted)}.links{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}.links a{display:inline-flex;align-items:center;padding:9px 12px;border:1px solid #bad0d8;border-radius:6px;text-decoration:none;font-size:14px;font-weight:650}.links .read{background:var(--teal);color:white;border-color:var(--teal)}.links .pdf{background:var(--green);color:#145346}.aux{font-size:13px;margin:15px 0 0}.aux a{margin-right:14px}.missing{font-size:13px;color:#7d5a18;margin-top:12px}.note{border-left:3px solid #b0cbd3;padding-left:16px;font-size:14px;color:var(--muted);margin-top:30px}footer{background:#073e55;color:white;padding:28px max(24px,calc((100vw - 1160px)/2));font-size:13px}footer a{color:white}.hidden,[hidden]{display:none!important}a:focus-visible,input:focus-visible,button:focus-visible{outline:3px solid #dcaa38;outline-offset:3px}@media(max-width:720px){.cards{grid-template-columns:1fr}header{padding:32px 20px}main{padding:22px 14px}.overview,.meeting{padding:20px}.basin-head{align-items:start}.metric{min-width:125px;flex:1}.metric b{font-size:24px}.links a{flex:1;justify-content:center}.basins a{font-size:13px}}@media print{header,footer{background:white;color:var(--ink)}.search,.basins{display:none}.cards{display:block}.meeting{break-inside:avoid;margin-bottom:16px}.links .read{background:white;color:var(--teal)}}
'''

JS='''
const normalize=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const input=document.getElementById('busca');const cards=[...document.querySelectorAll('.meeting')];
function filter(){const q=normalize(input.value.trim());let n=0;for(const c of cards){const ok=normalize(c.textContent+' '+c.dataset.group).includes(q);c.hidden=!ok;if(ok)n++;}for(const g of document.querySelectorAll('.basin'))g.hidden=![...g.querySelectorAll('.meeting')].some(c=>!c.hidden);document.getElementById('resultado').textContent=n+' de '+cards.length+' reuniões exibidas';document.getElementById('vazio').hidden=n!==0;}
input.addEventListener('input',filter);document.getElementById('limpar').addEventListener('click',()=>{input.value='';filter();input.focus();});document.querySelectorAll('.basins a').forEach(a=>a.addEventListener('click',()=>{input.value='';filter();}));
'''

def main():
    records=assemble();groups=list(dict.fromkeys(x['group'] for x in records));pdfs=sum(bool(x['pdf']) for x in records)
    navigation=''.join(f'<a href="#{esc(next(x["slug"] for x in records if x["group"]==g))}">{esc(g)}</a>' for g in groups)
    content=[]
    for group in groups:
        batch=sorted([x for x in records if x['group']==group],key=lambda x:x['date'],reverse=True);slug=batch[0]['slug']
        content.append(f'<section class="basin" id="{slug}"><div class="basin-head"><h2>{esc(group)}</h2><span class="small">{len(batch)} '+('reunião' if len(batch)==1 else 'reuniões')+'</span></div><div class="cards">')
        for x in batch:
            pending=('Prévia' in x['state'] or 'em aberto' in x['state']);badge='badge pending' if pending else 'badge'
            links=f'<a class="read" href="{esc(href(x["read_page"]))}">Ler NT integral</a>'
            if x['pdf']:links+=f'<a class="pdf" href="{esc(href(x["pdf"]))}">NT completa · PDF</a>'
            aux=''
            if x['csv']:aux+=f'<a href="{esc(href(x["csv"]))}" download>Dados e indicadores · CSV</a>'
            if x['annex']:aux+=f'<a href="{esc(href(x["annex"]))}">Anexo I — Reunião em números</a>'
            content.append(f'<article class="meeting" data-group="{esc(group)}"><div class="meta"><time class="date" datetime="{x["date"]}">{x["date_br"]}</time><span class="{badge}">{esc(x["state"])}</span></div><h3>{esc(x["title"])}</h3><p class="small">{esc(x["edition"])}</p><p class="description">{esc(x["description"])}</p><div class="links">{links}</div>')
            if not x['pdf']:content.append('<p class="missing">PDF ainda não hospedado neste repositório. A NT integral está disponível para leitura no site.</p>')
            if aux:content.append(f'<p class="aux">{aux}</p>')
            content.append('</article>')
        content.append('</div></section>')
    body=''.join(content)
    page=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Índice das Notas Técnicas das Salas SOE, organizado por bacia e sistema hídrico, com acesso às reuniões e aos PDFs disponíveis."><title>Salas SOE — Índice de reuniões e Notas Técnicas por bacia</title><style>{CSS}</style></head><body id="topo"><header><div class="eyebrow">SOE/ANA · Gabinete · Acervo técnico</div><h1>Salas SOE<br>Reuniões e Notas Técnicas</h1><p class="lead">Índice por bacia, sistema hídrico e região. Escolha a sala e acesse a Nota Técnica específica de cada reunião.</p><div class="credit">Supervisionado por <strong>José Aguiar de Lima Jr.</strong><br>Especialista em Geoprocessamento — Gabinete/SOE/ANA<br>Elaboração com suporte de inteligência artificial (IA).</div><div class="metrics"><div class="metric"><b>{len(groups)}</b><span>bacias / salas</span></div><div class="metric"><b>{len(records)}</b><span>reuniões publicadas</span></div><div class="metric"><b>{pdfs}</b><span>NTs com PDF hospedado</span></div></div></header><main><section class="overview" aria-labelledby="indice"><h2 id="indice">Selecione a bacia ou sala</h2><p>As reuniões mais recentes aparecem primeiro dentro de cada grupo. O rótulo de cada publicação distingue consolidações documentais de prévias técnicas.</p><nav class="basins" aria-label="Bacias e salas">{navigation}</nav><div class="search"><div class="inputbox"><label for="busca">Buscar no acervo</label><input id="busca" type="search" placeholder="Bacia, sistema, número ou data da reunião" autocomplete="off"></div><button id="limpar" type="button">Limpar</button></div><p class="count" id="resultado" role="status" aria-live="polite">{len(records)} de {len(records)} reuniões exibidas</p></section><p id="vazio" hidden>Nenhuma reunião corresponde à busca. Tente outra bacia, número ou data.</p>{body}<aside class="note"><strong>Escopo deste índice.</strong> Publicações de reuniões localizadas no repositório <em>soe-salas-prototipo</em>, inventariadas em 29/10/2026. Versões navegáveis e páginas de abertura da mesma reunião não são contadas em duplicidade. Estudos técnicos, tutoriais e boletins temáticos não integram esta listagem. Publicações mantidas apenas em outros ambientes ainda não estão inventariadas aqui.<br><strong>Uso.</strong> O estado editorial é o informado em cada publicação; não representa homologação institucional. Os links de PDF aparecem somente quando o arquivo existe no repositório.</aside></main><footer><strong>Protótipo técnico em ambiente pessoal — não constitui publicação institucional da ANA.</strong><br>Supervisão: José Aguiar de Lima Jr. · Especialista em Geoprocessamento — Gabinete/SOE/ANA · Suporte de IA.<br><a href="#topo">Voltar ao índice de bacias</a></footer><script>{JS}</script></body></html>'''
    OUT.mkdir(exist_ok=True);(OUT/'index.html').write_text(page,encoding='utf-8')
    summary={'updated_at':datetime.now(timezone.utc).isoformat(),'scope':'Reuniões publicadas neste repositório','meetings':len(records),'basins':len(groups),'hosted_pdfs':pdfs,'records':records}
    (OUT/'reunioes.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    # Check all catalog destinations, including anchors, before publication.
    soup=BeautifulSoup(page,'html.parser')
    for a in soup.select('a[href]'):
        link=a['href']
        if link.startswith('#'):assert soup.find(id=link[1:]),link;continue
        u=urlsplit(link);dest=(OUT/unquote(u.path)).resolve();assert dest.is_relative_to(ROOT) and dest.is_file(),link
        if u.fragment:assert BeautifulSoup(dest.read_text(encoding='utf-8'),'html.parser').find(id=u.fragment),link
    print(json.dumps({k:summary[k] for k in ['meetings','basins','hosted_pdfs']},ensure_ascii=False))
    print('Todos os destinos locais do índice foram verificados.')

if __name__=='__main__':main()
