#!/usr/bin/env python3
"""Build this meeting only: verified sources -> integral HTML/PDF/CSV.

No model calls, no private documents, no modification of earlier publications.
The report text and selected figures are shared by the web and PDF editions.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import fitz
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
BASE = 'https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/eventos-criticos/apresentacoes-das-reunioes/'
DATA = json.loads((ROOT / 'content.json').read_text(encoding='utf-8'))
PDF_NAME = 'NT_Paranapanema_10a_22-10-2026.pdf'
NAME = 'José Aguiar de Lima Jr.'
ROLE = 'Especialista em Geoprocessamento'
UNIT = 'Gabinete da Superintendência de Operações e Eventos Críticos — SOE/ANA'
CSS = '''
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;background:#f2f6f7;color:#253c48;font:17px/1.72 system-ui,-apple-system,Segoe UI,sans-serif;overflow-wrap:anywhere}a{color:#086e83;text-underline-offset:3px}header{background:linear-gradient(115deg,#083c52,#08716f);color:#fff;padding:46px max(24px,calc((100vw - 1160px)/2)) 38px}.eyebrow{font-size:12px;letter-spacing:.13em;text-transform:uppercase;font-weight:750}header h1{font-size:clamp(34px,4.5vw,57px);line-height:1.12;margin:16px 0 20px;max-width:1080px}header .lead{font-size:20px;line-height:1.5}header p{margin:10px 0}.meta{color:#d1e7e9;font-size:14px}.credit{border-left:3px solid #8bd3c0;margin:24px 0;padding:3px 0 3px 18px}.credit p{margin:4px 0;font-size:14px;line-height:1.5}.credit .person{font-size:17px}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}.actions a{display:flex;align-items:center;justify-content:center;border:1px solid #c0dadb;border-radius:7px;background:#fff;color:#07566b;padding:11px 18px;font-weight:650;font-size:15px;text-decoration:none;min-height:50px;text-align:center}.actions .primary{background:#c9f3e8;color:#064f4b;border-color:transparent}.actions a:focus-visible,button:focus-visible{outline:3px solid #e4b641;outline-offset:4px}.print-link{background:none;border:0;color:#d2e8ea;text-decoration:underline;font:13px system-ui;padding:12px 0;cursor:pointer}nav{position:sticky;top:0;z-index:10;background:#fffffff5;border-bottom:1px solid #cedfe3;display:flex;gap:22px;padding:13px max(22px,calc((100vw - 1160px)/2));overflow-x:auto;white-space:nowrap}nav a{text-decoration:none;font-size:14px;font-weight:700}main{max-width:1210px;padding:0 24px;margin:26px auto 55px}.chapter,.contents{background:#fff;border:1px solid #d6e4e7;border-radius:11px;padding:clamp(22px,3vw,36px);margin:24px 0;min-width:0}h2{font-size:28px;line-height:1.25;color:#07536b;margin:0 0 23px}h3{font-size:20px;color:#116e63;line-height:1.35;margin:30px 0 12px}h4{font-size:17px;color:#155b6d}p{margin:14px 0}.tag{font-size:12px;font-weight:750;color:#5e7e87;letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px}.note{background:#edf6f4;border-left:4px solid #118578;padding:15px 19px;margin:22px 0;font-size:15px}.warning{background:#fff7e7;border-left-color:#c2993b}.contents ol{columns:2;column-gap:32px;padding-left:22px}.contents li{padding:5px 0;break-inside:avoid}.contents a{font-size:15px;text-decoration:none}.tablewrap{max-width:100%;overflow-x:auto;margin:20px 0}table{width:100%;border-collapse:collapse;line-height:1.5;font-size:14px}th,td{padding:11px 12px;text-align:left;border:1px solid #d0dfe3;vertical-align:top}th{background:#e5f1ee;color:#07536b}tr:nth-child(even) td{background:#fafcfc}.figures{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;margin:24px 0}.figures figure{min-width:0}.figures figure:first-child{grid-column:1/-1}figure{background:#fff;border:1px solid #cddfe3;border-radius:9px;overflow:hidden;margin:0}figure .image-link{display:block;background:#eaf1f3}figure img{display:block;width:100%;height:auto;cursor:zoom-in}figcaption{font-size:14px;line-height:1.58;padding:17px 20px}figcaption strong{display:block;font-size:16px;color:#07546b;margin-bottom:7px}.source{display:block;font-size:12px;color:#577781;margin:10px 0 6px}.fig-actions{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;font-weight:650}.citation{font-size:.93em;text-decoration:none}.backtop{display:block;text-align:right;font-size:13px;margin-top:20px}.source-items li{margin:13px 0}.small{font-size:13px;color:#5e7882}footer{background:#083e52;color:#dcecef;padding:30px max(24px,calc((100vw - 1160px)/2));font-size:13px}footer a{color:#dcecef}footer .credit{margin:0 0 20px}footer .credit .person{font-size:16px}dialog{width:min(96vw,1700px);max-height:96vh;border:0;border-radius:10px;padding:17px}dialog::backdrop{background:#001d2ae8}dialog img{display:block;width:100%;max-height:80vh;object-fit:contain}dialog button{display:block;margin:0 0 10px auto;padding:8px 15px;border:1px solid #bdd6dc;background:#fff;color:#07536b;font:650 14px system-ui;border-radius:5px;cursor:pointer}#zoom-text{font-size:14px;line-height:1.5}.print-only{display:none}@media(max-width:820px){.figures{grid-template-columns:1fr}.contents ol{columns:1}main{padding:0 14px}.chapter,.contents{padding:22px 18px}body{font-size:16px}h2{font-size:25px}.actions a{width:100%}nav{gap:18px}header .lead{font-size:18px}}@media print{@page{size:A4;margin:17mm 16mm 25mm}html{scroll-behavior:auto}body{background:#fff;font:10.5pt/1.49 Arial,sans-serif;color:#203b47}header{background:white;color:#12465b;padding:17mm 0 0;break-after:page}header h1{font-size:29pt;line-height:1.12;margin:9mm 0}header .lead{font-size:13pt;line-height:1.45}.meta{color:#4b6873;font-size:10pt}.eyebrow{font-size:9pt;color:#2e6877}.credit{border-left-color:#148575;margin:10mm 0 0;padding-left:5mm}.credit p{font-size:10pt}.credit .person{font-size:12pt}nav,.actions,.print-link,.fig-actions,.backtop,dialog,.screen-only{display:none!important}.print-only{display:block}main{max-width:none;margin:0;padding:0}.contents{border:0;margin:0;padding:0;break-after:page}.contents ol{columns:1;padding-left:5mm}.contents li{padding:2mm 0}.contents a{font-size:10.5pt}.chapter{margin:0;padding:0;border:0;border-radius:0;break-before:page}h2{font-size:19pt;line-height:1.25;margin:0 0 6mm;break-after:avoid}h3{font-size:13pt;margin:6mm 0 3mm;break-after:avoid}p{orphans:3;widows:3;margin:3mm 0}.tag{font-size:8pt}.note{font-size:9.5pt;padding:3mm 4mm;margin:4mm 0;break-inside:avoid}.figures{display:block;margin:5mm 0}figure{border:1px solid #cddfe3;border-radius:3mm;margin:4mm 0;break-inside:avoid}figure img{width:100%;max-height:170mm;object-fit:contain}figcaption{font-size:9pt;line-height:1.4;padding:3mm 4mm}figcaption strong{font-size:10pt}.source{font-size:8pt;margin:2mm 0 0}.tablewrap{overflow:visible;margin:4mm 0}table{font-size:8.5pt;line-height:1.4}th,td{padding:2mm}thead{display:table-header-group}tr{break-inside:avoid}.small{font-size:9pt}a{color:inherit;text-decoration:none}footer{background:#fff;color:#42606a;padding:7mm 0 0;font-size:9pt}footer .credit{margin:0;padding-left:4mm}footer .credit p{font-size:9pt}footer .credit .person{font-size:10pt}}
'''
JS = '''
const d=document.querySelector('#zoom');document.querySelectorAll('[data-zoom]').forEach(a=>a.addEventListener('click',e=>{if(!d.showModal)return;e.preventDefault();const f=a.closest('figure');d.querySelector('img').src=a.dataset.zoom;d.querySelector('img').alt=f.querySelector('img').alt;document.querySelector('#zoom-text').textContent=f.querySelector('figcaption').innerText;d.showModal();}));d.querySelector('button').onclick=()=>d.close();d.addEventListener('click',e=>{if(e.target===d)d.close();});
'''
# Selected source pages appear after their corresponding analytical block.
FIGURE_GROUPS = {'cemaden':{0:[2,3,4],1:[5,6,7,8,9],2:[14,16,17,21,22]}, 'ons':{0:[4,11],1:[8,9],2:[15,16,17],3:[20,21],5:[14,19]}}


def esc(value):
    return html.escape(str(value), quote=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paragraphs(text):
    def citation(match):
        code, ref = match.group(1), match.group(2)
        source = 'cemaden' if code == 'C' else 'ons'
        number = re.search(r'\d+', ref)
        page = number.group() if number else '1'
        return f'<a class="citation" href="fontes/{source}.pdf#page={page}" target="_blank" rel="noopener">{esc(match.group())}</a>'
    safe = esc(text)
    return '<p>' + re.sub(r'\[([CO]), ([^\]]+)\]', citation, safe) + '</p>'


def table(spec):
    heads = ''.join('<th scope="col">'+esc(x)+'</th>' for x in spec['headers'])
    rows = ''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in spec['rows'])
    return f'<div class="tablewrap"><table><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table></div>'


def sources(work, local):
    output = work / 'fontes';output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504])))
    metadata = {}
    for key, info in DATA['sources'].items():
        view = BASE + info['file'] + '/view'
        download = BASE + info['file'] + '/@@download/file'
        target = output / (key+'.pdf')
        cached = ROOT / 'fontes' / (key+'.pdf')
        candidate = local / (key+'.pdf') if local else cached
        if candidate.is_file() and digest(candidate)==info['sha256']:
            if candidate.resolve()!=target.resolve():shutil.copyfile(candidate,target)
        else:
            r=session.get(view,timeout=(15,90));r.raise_for_status()
            r=session.get(download,timeout=(15,90));r.raise_for_status()
            if not r.content.startswith(b'%PDF'):raise ValueError('Not a PDF: '+key)
            target.write_bytes(r.content)
        assert digest(target)==info['sha256'], 'Source has changed: '+key
        doc=fitz.open(target);assert len(doc)==info['pages']
        metadata[key]={'institution':info['label'],'code':info['code'],'view':view,'download':download,'sha256':digest(target),'pages':len(doc),'bytes':target.stat().st_size}
        print('SOURCE VERIFIED', key, len(doc), flush=True)
    return metadata


def figures(work):
    out=work/'assets';out.mkdir(exist_ok=True)
    docs={k:fitz.open(work/'fontes'/(k+'.pdf')) for k in DATA['sources']}
    for figure in DATA['figures']:
        page=docs[figure['source']][figure['page']-1]
        scale=1900/page.rect.width
        image=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
        image.save(out/f'{figure["source"]}_{figure["page"]:02d}.png')
    for doc in docs.values():doc.close()
    assert len(list(out.glob('*.png')))==24


def make_html(work, metadata):
    figure_index={(f['source'],f['page']):(i+1,f) for i,f in enumerate(DATA['figures'])}
    used=[]
    def figure(source, page):
        number, item=figure_index[(source,page)];used.append((source,page))
        src=f'assets/{source}_{page:02d}.png'
        return f'<figure id="fig-{number:02d}"><a class="image-link" href="{src}" data-zoom="{src}" aria-label="Ampliar figura {number}"><img src="{src}" alt="{esc(item["title"])} — {esc(metadata[source]["institution"])}; página {page}" width="1900" loading="eager"></a><figcaption><strong>Figura {number:02d} · {esc(item["title"])}</strong>{esc(item["caption"])}<span class="source">Fonte: {esc(metadata[source]["institution"])}, apresentação de 22/10/2026, página {page} do PDF. Reprodução original.</span><span class="fig-actions"><a href="{src}" data-zoom="{src}">Ampliar figura</a><a href="fontes/{source}.pdf#page={page}" target="_blank" rel="noopener">Ver página na apresentação</a></span></figcaption></figure>'
    chapters=[]
    all_paragraphs=[]
    for sec in DATA['sections']:
        blocks=[]
        for idx,block in enumerate(sec['blocks']):
            if block.get('title'):blocks.append('<h3>'+esc(block['title'])+'</h3>')
            for text in block.get('paragraphs',[]):
                blocks.append(paragraphs(text));all_paragraphs.append(text)
            if block.get('table'):blocks.append(table(block['table']))
            pages=FIGURE_GROUPS.get(sec['id'],{}).get(idx,[])
            if pages:blocks.append('<div class="figures">'+''.join(figure(sec['id'],p) for p in pages)+'</div>')
        chapters.append('<section class="chapter" id="'+esc(sec['id'])+'"><h2>'+esc(sec['title'])+'</h2>'+''.join(blocks)+'<a class="backtop" href="#topo">Voltar ao início ↑</a></section>')
    assert len(used)==24 and len(set(used))==24
    toc=''.join(f'<li><a href="#{esc(s["id"])}">{esc(s["title"])}</a></li>' for s in DATA['sections'])
    credit=f'<div class="credit"><p class="person">Supervisionado por <strong>{NAME}</strong></p><p>{ROLE}<br>{UNIT}</p><p>Elaboração com suporte de inteligência artificial (IA).</p></div>'
    nav=[('executivo','Síntese'),('cemaden','CEMADEN'),('ons','ONS'),('cruzamentos','Cruzamentos'),('cenarios','Cenários'),('regulacao','Regulação'),('encaminhamentos','Registro'),('qualidade','Ressalvas'),('fontes','Fontes')]
    links=''.join(f'<a href="#{key}">{label}</a>' for key,label in nav)
    source_list=''.join(f'<li><strong>[{info["code"]}] {esc(info["institution"])}</strong> — {info["pages"]} páginas. <a href="fontes/{key}.pdf" target="_blank" rel="noopener">Apresentação integral</a> · <a href="{esc(info["view"])}" target="_blank" rel="noopener">Registro oficial na ANA</a>.</li>' for key,info in metadata.items())
    page=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="author" content="Supervisão: {NAME} — {ROLE} — Gabinete/SOE/ANA; suporte de IA"><meta name="description" content="Nota Técnica da 10ª reunião do Paranapanema, 22/10/2026: verticais CEMADEN e ONS, 24 figuras originais, cruzamentos, operação e PDF integral."><title>Paranapanema · 10ª reunião · Nota Técnica integral</title><style>{CSS}</style></head><body id="topo"><header><div class="eyebrow">SOE/ANA — Gabinete | Nota Técnica</div><h1>Paranapanema<br>{esc(DATA['subtitle'])}</h1><p class="lead">{esc(DATA['title'])}</p><p><strong>Reunião: {esc(DATA['meeting_date'])}</strong> · Consolidação documental: {esc(DATA['edition_date'])}</p><p class="meta">CEMADEN + ONS · 24 figuras originais · Edição 1.0</p>{credit}<div class="actions" role="group" aria-label="Acesso à Nota Técnica"><a href="#executivo">Ler NT — versão navegável</a><a class="primary" href="documentos/{PDF_NAME}" download>Nota Técnica integral · PDF</a><a href="indicadores.csv" download>Dados e indicadores · CSV</a></div><button class="print-link" onclick="window.print()" type="button">Imprimir / salvar esta página</button><p class="print-only small">{esc(DATA['status'])}</p></header><nav aria-label="Seções da Nota Técnica">{links}</nav><main><section class="contents" id="sumario"><div class="tag">Escopo da edição</div><h2>Conteúdo e fontes</h2><div class="note">{esc(DATA['status'])}</div><p>Dois arquivos publicados foram identificados no acervo da ANA. Isso não confirma o número de instituições participantes nem o conteúdo do debate oral. As recomendações desta NT são análises, não deliberações atribuídas à reunião.</p><ol>{toc}</ol><p class="small">[C] CEMADEN · [O] ONS. Referências de página usam a posição física no PDF, a partir de 1. A versão navegável e o PDF preservam o mesmo conteúdo técnico.</p></section>{''.join(chapters)}<section class="chapter" id="fontes"><h2>9. Fontes, apresentações integrais e rastreabilidade</h2><p>Arquivos oficiais vinculados à reunião de 22/10/2026, acessados pelo registro /view e pelo download do PDF. As cópias foram verificadas por SHA-256; as 24 figuras são reproduções das páginas selecionadas.</p><ul class="source-items">{source_list}</ul><p><a href="{BASE}apresentacoes-das-reunioes" target="_blank" rel="noopener">Acervo oficial de apresentações da ANA</a></p><p><a href="documentos/{PDF_NAME}" download>Nota Técnica integral · PDF</a> · <a href="indicadores.csv" download>Dados e indicadores · CSV</a> · <a href="manifesto.json">Manifesto de fontes e versão</a></p><div class="note warning"><strong>Limite institucional.</strong> Esta consolidação técnica não substitui ata, autorização de operação, ficha de restrição ou ato normativo. A numeração 10ª identifica a reunião, não um número de processo ou de Nota Técnica oficial.</div><p class="small">Foram preservadas as ressalvas editoriais e temporais das fontes. Não foram incorporadas apresentações de outra reunião para preencher lacunas. Arquivos editáveis de trabalho não integram a publicação pública.</p></section></main><footer>{credit}<p>Reunião de 22/10/2026 · Edição documental de 23/10/2026 · Versão 1.0.<br>Repositório pessoal de protótipos; não substitui publicação ou manifestação institucional formal.</p><a href="#topo">Voltar ao início</a></footer><dialog id="zoom" aria-label="Figura ampliada"><button type="button">Fechar ×</button><img alt="Figura ampliada"><p id="zoom-text"></p></dialog><script>{JS}</script></body></html>'''
    path=work/'index.html';path.write_text(page,encoding='utf-8')
    soup=BeautifulSoup(page,'html.parser')
    assert len(soup.select('figure'))==24
    for text in all_paragraphs:assert text in soup.get_text(), 'Paragraph not retained: '+text[:100]
    for img in soup.select('figure img'):assert (work/img['src']).is_file()
    return all_paragraphs


def make_csv(work):
    with (work/'indicadores.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter=';')
        writer.writerow(['instituicao','local','indicador','valor','unidade','periodo','natureza','pagina_fonte','fonte_pdf'])
        for row in DATA['indicators']:
            key='cemaden' if row[0]=='CEMADEN' else 'ons'
            url=BASE+DATA['sources'][key]['file']+'/@@download/file#page='+str(row[7])
            writer.writerow(row+[url])
    assert len(DATA['indicators'])==29


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def render_and_test(work, qa, all_paragraphs):
    from playwright.sync_api import sync_playwright
    qa.mkdir(parents=True,exist_ok=True)
    out=work/'documentos';out.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(work)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f'http://127.0.0.1:{server.server_port}/index.html'
    footer='''<div style="font:8px/1.35 Arial,sans-serif;color:#47626d;width:100%;margin:0 16mm;padding-top:4px;border-top:1px solid #c9dadd;text-align:center">Supervisionado por <strong>José Aguiar de Lima Jr.</strong> · Especialista em Geoprocessamento<br>Gabinete/SOE/ANA · Elaboração com suporte de inteligência artificial (IA)<br>Reunião 22/10/2026 · Edição 23/10/2026 · Página <span class="pageNumber"></span> de <span class="totalPages"></span></div>'''
    try:
        with sync_playwright() as p:
            chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable') or shutil.which('chromium')
            opts={'headless':True,'args':['--no-sandbox']}
            if chrome:opts['executable_path']=chrome
            browser=p.chromium.launch(**opts)
            page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
            page.goto(url,wait_until='networkidle')
            page.wait_for_function("Array.from(document.querySelectorAll('figure img')).every(i=>i.complete&&i.naturalWidth>0)")
            assert page.locator('figure').count()==24
            assert NAME in page.locator('header').inner_text() and NAME in page.locator('footer').inner_text()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
            page.screenshot(path=str(qa/'desktop.png'),full_page=True)
            page.locator('header').screenshot(path=str(qa/'abertura.png'))
            page.locator('.image-link').first.click();assert page.locator('dialog').evaluate('(d)=>d.open');page.keyboard.press('Escape')
            page.emulate_media(media='print')
            assert not page.locator('.actions').is_visible()
            pdf=out/PDF_NAME
            page.pdf(path=str(pdf),format='A4',prefer_css_page_size=True,print_background=True,display_header_footer=True,header_template='<span></span>',footer_template=footer)
            page.emulate_media(media='screen')
            for href in ['documentos/'+PDF_NAME,'indicadores.csv']:
                with page.expect_download() as ev:page.locator('.actions a[href="'+href+'"]').click()
                downloaded=Path(ev.value.path());assert digest(downloaded)==digest(work/href)
            page.locator('.actions a[href="#executivo"]').click();assert page.evaluate('location.hash')=='#executivo'
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
            page.locator('header').screenshot(path=str(qa/'celular.png'))
            browser.close()
    finally:
        server.shutdown();server.server_close()
    doc=fitz.open(work/'documentos'/PDF_NAME)
    text=' '.join(page.get_text() for page in doc)
    normalized=re.sub(r'\s+',' ',text)
    # Confirm chapter titles and distinctive text; HTML already checks every paragraph.
    for sec in DATA['sections']:
        assert re.sub(r'\s+',' ',sec['title']) in normalized, 'Chapter missing from PDF: '+sec['id']
    assert sum(len(page.get_images()) for page in doc)>=24
    for i,page in enumerate(doc):
        t=page.get_text();assert NAME in t and ROLE in t and 'inteligência artificial' in t, 'Missing credit on page '+str(i+1)
        page.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).save(qa/f'pdf-{i+1:02d}.png')
    print('QA PASS',len(doc),'PDF pages; 24 figures; desktop/mobile; downloads; credits on every page.',flush=True)
    return len(doc)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--qa',type=Path,default=Path('/tmp/paranapanema-qa'))
    parser.add_argument('--local-sources',type=Path)
    args=parser.parse_args();work=args.output.resolve();work.mkdir(parents=True,exist_ok=True)
    metadata=sources(work,args.local_sources)
    figures(work);all_paragraphs=make_html(work,metadata);make_csv(work)
    pages=render_and_test(work,args.qa,all_paragraphs)
    manifest={'meeting_date':'2026-10-22','edition_date':'2026-10-23','version':DATA['version'],'generated_at_utc':datetime.now(timezone.utc).isoformat(),'sources':metadata,'institutions':['CEMADEN','ONS'],'figure_count':24,'indicator_rows':29,'pdf_pages':pages,'pdf_sha256':digest(work/'documentos'/PDF_NAME),'formal_decisions_received':False,'scope':'Consolidação das duas apresentações publicadas; não comprova total de participantes.','original_prior_publications_modified':False}
    (work/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copyfile(ROOT/'content.json',work/'content.json')
    print('READY FOR REVIEW:',work,flush=True)

if __name__=='__main__':main()
