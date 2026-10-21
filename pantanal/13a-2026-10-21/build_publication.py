#!/usr/bin/env python3
"""Publish only this meeting. Keep the original DOCX untouched.

The public index is replaced only after source PDFs, figures, links and the
printable web edition have passed validation. No credentials are logged.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
import fitz
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
BASE = 'https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/eventos-criticos/apresentacoes-das-reunioes/'
LISTING = BASE + 'apresentacoes-das-reunioes'
DATA = json.loads((ROOT / 'publicacao.json').read_text(encoding='utf-8'))
SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'SOE-publication-source-check/2.0 (+https://7it0.github.io/soe-salas-prototipo/)'})
SESSION.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))

CSS = '''
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;background:#f1f5f6;color:#243d49;font:17px/1.7 system-ui,-apple-system,Segoe UI,sans-serif}a{color:#087184;text-underline-offset:3px}header{background:linear-gradient(115deg,#073c52,#076d73);color:white;padding:48px max(24px,calc((100vw - 1160px)/2)) 42px}header h1{font-size:clamp(32px,4.5vw,54px);line-height:1.12;margin:16px 0 20px;max-width:1100px}header p{max-width:1050px;margin:10px 0}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:750}.lead{font-size:21px}.hero-meta{font-size:14px;color:#cce9ed}.header-links{display:flex;flex-wrap:wrap;gap:14px;margin-top:24px}header a,header button{color:white;background:transparent;border:1px solid #74a8b2;border-radius:6px;padding:9px 15px;text-decoration:none;font:600 14px system-ui;cursor:pointer}nav{position:sticky;top:0;background:#fffffff5;border-bottom:1px solid #cbdcdf;z-index:10;display:flex;gap:22px;padding:14px max(20px,calc((100vw - 1160px)/2));overflow-x:auto;white-space:nowrap}nav a{font-size:14px;font-weight:700;text-decoration:none}main{max-width:1210px;padding:0 24px;margin:28px auto 60px}.chapter{background:white;border:1px solid #d8e5e8;border-radius:12px;margin:26px 0;padding:clamp(22px,3vw,36px)}h2{color:#07546a;font-size:29px;line-height:1.25;margin:4px 0 22px}h3{color:#0b716b;font-size:20px;margin:28px 0 12px}p{margin:14px 0}.section-tag{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#65808a;font-weight:750}.note{background:#f0f7f7;border-left:4px solid #138577;padding:16px 20px;margin:22px 0;font-size:15px}.note.warning{background:#fff8e9;border-left-color:#be933e}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}.metric{padding:18px;border-top:4px solid #138577;background:#f0f7f7;border-radius:6px}.metric b{font-size:28px;line-height:1.2;display:block;color:#07546a;margin:5px 0}.metric span{font-size:13px;display:block}.metric small{font-size:12px;color:#56727b}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;margin:22px 0 8px}.gallery figure:first-child{grid-column:1/-1}figure{margin:0;border:1px solid #cfdee2;border-radius:9px;overflow:hidden;background:#fff}figure a.image-link{display:block;background:#e9f0f2}figure img{display:block;width:100%;height:auto;cursor:zoom-in}figcaption{padding:17px 20px;font-size:14px;line-height:1.6}figcaption strong{display:block;color:#07546a;font-size:16px;margin-bottom:7px}.figsource{display:block;color:#607a83;font-size:12px;margin-top:9px}.figlinks{display:flex;gap:20px;flex-wrap:wrap;margin-top:9px}.figlinks a{font-size:13px;font-weight:650}.tablewrap{overflow-x:auto;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.55}th,td{border:1px solid #d4e0e4;text-align:left;vertical-align:top;padding:12px}th{background:#e4f1ee;color:#07546a}ul{padding-left:22px}.equation{font:600 16px/1.8 ui-monospace,monospace;white-space:normal;background:#edf5f5;padding:18px;border-radius:6px}.badge{display:inline-block;background:#e8f3ef;color:#0a6d58;padding:4px 10px;border-radius:30px;font-size:12px;font-weight:700}.source-list li{margin:12px 0}.small{font-size:13px;color:#617983}footer{background:#083e51;color:#d6e9ed;padding:28px max(24px,calc((100vw - 1160px)/2));font-size:13px}footer a{color:#d6e9ed}dialog{border:0;border-radius:10px;padding:18px;width:min(96vw,1600px);max-height:96vh}dialog::backdrop{background:#021d2be8}dialog img{width:100%;max-height:81vh;object-fit:contain}dialog button{display:block;margin:0 0 10px auto;padding:8px 15px;background:#fff;color:#07546a;border:1px solid #c4d9df;border-radius:5px;font:600 14px system-ui;cursor:pointer}#zoom-caption{font-size:14px;line-height:1.5}.backtop{display:block;text-align:right;margin-top:18px;font-size:13px}.screen-only{}.print-only{display:none}@media(max-width:820px){.metrics{grid-template-columns:repeat(2,1fr)}.gallery{grid-template-columns:1fr}.gallery figure:first-child{grid-column:auto}main{padding:0 14px}.chapter{padding:22px 18px}h2{font-size:25px}nav{gap:18px}body{font-size:16px}}@media(max-width:440px){.metrics{grid-template-columns:1fr}.lead{font-size:18px}}@media print{@page{size:A4;margin:16mm}body{background:white;font-size:10pt;line-height:1.5}header{background:white;color:#153f50;padding:0 0 10mm}header h1{font-size:25pt}.hero-meta{color:#4d6871}nav,.header-links,.screen-only,dialog,.figlinks,.backtop{display:none!important}.print-only{display:block}main{margin:0;padding:0;max-width:none}.chapter{padding:0;border:0;border-radius:0;margin:0 0 8mm;break-before:page}#executivo{break-before:auto}h2{font-size:19pt}h3{font-size:13pt}p{orphans:3;widows:3}.gallery{display:block}figure{break-inside:avoid;margin:5mm 0;border:1px solid #d0dadd}figure img{max-height:175mm;object-fit:contain}figcaption{font-size:9pt;padding:3mm 4mm}figcaption strong{font-size:10pt}.figsource{font-size:8pt}.metrics{grid-template-columns:repeat(2,1fr)}table{font-size:8.5pt}tr{break-inside:avoid}footer{background:white;color:#516d77;padding:5mm 0;font-size:8pt}.note{font-size:9.5pt}.equation{font-size:10pt}a{color:inherit;text-decoration:none}}
'''

SCRIPT = '''
const modal=document.querySelector('#zoom');
for(const a of document.querySelectorAll('[data-zoom]')){a.addEventListener('click',e=>{if(!modal.showModal)return;e.preventDefault();const fig=a.closest('figure');modal.querySelector('img').src=a.dataset.zoom;modal.querySelector('img').alt=fig.querySelector('img').alt;document.querySelector('#zoom-caption').textContent=fig.querySelector('figcaption').textContent;modal.showModal();});}
modal.querySelector('button').onclick=()=>modal.close();modal.addEventListener('click',e=>{if(e.target===modal)modal.close();});
window.addEventListener('beforeprint',()=>document.querySelectorAll('img').forEach(i=>i.loading='eager'));
'''

def esc(value):
    return html.escape(str(value), quote=True)

def allowed(url):
    host = (urlparse(url).hostname or '').lower()
    return host == 'gov.br' or host.endswith('.gov.br')

def retrieve(url):
    if not allowed(url):
        raise ValueError('Unexpected source host')
    result = SESSION.get(url, timeout=(15, 60))
    result.raise_for_status()
    if not allowed(result.url):
        raise ValueError('Unexpected redirect')
    return result

def discover():
    result = {}
    try:
        page = retrieve(LISTING)
        soup = BeautifulSoup(page.text, 'html.parser')
        for key, source in DATA['sources'].items():
            found = []
            for a in soup.select('a[href]'):
                url = urljoin(LISTING, a['href'])
                text = unquote((url + ' ' + a.get_text(' ', strip=True)).lower())
                dated = any(x in text for x in ['20261021', '21102026', '21_10_2026', '21/10/2026', 'outubro26'])
                named = key in text or (key == 'inmet' and 'inpe' in text)
                if allowed(url) and dated and named:
                    found.append(url)
            result[key] = list(dict.fromkeys(found))
    except requests.RequestException as error:
        print('Listing unavailable; using deterministic source paths:', type(error).__name__, flush=True)
    return result

def download_source(key, source, discovered, dest):
    candidates = discovered.get(key, []) + [BASE + source['filename'] + '/view']
    candidates = list(dict.fromkeys(candidates))
    attempts = []
    for entry in candidates:
        view = entry if entry.endswith('/view') else entry.split('/@@download')[0].rstrip('/') + '/view'
        downloads = []
        try:
            response = retrieve(view)
            if response.content.startswith(b'%PDF'):
                downloads.append(response.url)
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
                downloads.extend(urljoin(view, a['href']) for a in soup.select('a[href]') if '@@download' in a['href'])
        except requests.RequestException as error:
            attempts.append(view + ': ' + type(error).__name__)
        downloads.append(view.removesuffix('/view') + '/@@download/file')
        for url in dict.fromkeys(downloads):
            try:
                response = retrieve(url)
                raw = response.content
                if not raw.startswith(b'%PDF'):
                    raise ValueError('Source is not a PDF')
                actual = hashlib.sha256(raw).hexdigest()
                if actual != source['sha256']:
                    raise ValueError('PDF differs from the uploaded meeting source: ' + actual)
                pdf = fitz.open(stream=raw, filetype='pdf')
                if len(pdf) != source['pages']:
                    raise ValueError('Page count mismatch')
                dest.write_bytes(raw)
                return {'institution': source['label'], 'view': view, 'download': response.url, 'sha256': actual, 'pages': len(pdf), 'bytes': len(raw)}
            except (requests.RequestException, ValueError) as error:
                attempts.append(url + ': ' + str(error))
    raise RuntimeError('Could not validate ' + key + '\n' + '\n'.join(attempts))

def get_sources(work, local):
    directory = work / 'fontes'
    directory.mkdir(parents=True, exist_ok=True)
    available = discover() if local is None else {}
    metadata = {}
    for key, source in DATA['sources'].items():
        path = directory / (key + '.pdf')
        if local:
            matches = [p for p in local.glob('*.pdf') if hashlib.sha256(p.read_bytes()).hexdigest() == source['sha256']]
            if not matches:
                raise RuntimeError('Missing local source: ' + key)
            shutil.copyfile(matches[0], path)
            metadata[key] = {'institution': source['label'], 'view': BASE + source['filename'] + '/view', 'download': BASE + source['filename'] + '/@@download/file', 'sha256': source['sha256'], 'pages': source['pages'], 'bytes': path.stat().st_size}
        else:
            metadata[key] = download_source(key, source, available, path)
        print('SOURCE VERIFIED:', key, source['pages'], 'pages', flush=True)
    return metadata

def render_figures(work):
    asset_dir = work / 'assets'
    asset_dir.mkdir(exist_ok=True)
    count = 0
    for section in DATA['sections']:
        key = section['id']
        pdf = fitz.open(work / 'fontes' / (key + '.pdf'))
        for item in section['figures']:
            page = pdf[item['page'] - 1]
            matrix = fitz.Matrix(1800 / page.rect.width, 1800 / page.rect.width)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            path = asset_dir / f'{key}_{item["page"]:02d}.png'
            pix.save(path)
            if path.stat().st_size < 1000:
                raise RuntimeError('Invalid figure: ' + str(path))
            count += 1
    if count != 18:
        raise RuntimeError('Expected 18 DOCX figures, found ' + str(count))
    print('FIGURES VERIFIED:', count, flush=True)

def make_html(work, metadata):
    sections = []
    figure_number = 0
    for number, section in enumerate(DATA['sections'], 1):
        key = section['id']
        content = ''.join('<p>' + esc(p) + '</p>' for p in section['paragraphs'])
        figures = []
        for figure in section['figures']:
            figure_number += 1
            src = f'assets/{key}_{figure["page"]:02d}.png'
            pdf = f'fontes/{key}.pdf#page={figure["page"]}'
            caption = f'<strong>Figura {figure_number:02d} · {esc(figure["title"])}</strong>{esc(figure["caption"])}<span class="figsource">Fonte: {esc(metadata[key]["institution"])}, apresentação de 21/10/2026, página {figure["page"]}. Reprodução do gráfico original.</span>'
            figures.append(f'<figure id="fig-{figure_number:02d}"><a class="image-link" href="{src}" data-zoom="{src}" aria-label="Ampliar {esc(figure["title"])}"><img src="{src}" alt="{esc(figure["title"])} — {esc(metadata[key]["institution"])}; página {figure["page"]}" width="1800" loading="eager"></a><figcaption>{caption}<span class="figlinks"><a href="{src}" data-zoom="{src}">Ampliar figura</a><a href="{pdf}" target="_blank" rel="noopener">Ver página na apresentação original</a></span></figcaption></figure>')
        sections.append(f'<section class="chapter" id="{key}"><div class="section-tag">Vertical {number:02d} · {len(figures)} figuras originais</div><h2>{esc(section["title"])}</h2>{content}<h3>Evidências gráficas da instituição</h3><div class="gallery">{"".join(figures)}</div><a class="backtop" href="#topo">Voltar ao início ↑</a></section>')
    followup = ''.join(f'<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>Recomendação de acompanhamento; não deliberação formal registrada.</td></tr>' for a,b in DATA['followup'])
    source_links = ''.join(f'<li><strong>{esc(item["institution"])}</strong> — {item["pages"]} páginas. <a href="fontes/{key}.pdf" target="_blank" rel="noopener">Abrir apresentação integral</a> · <a href="{esc(item["view"])}" target="_blank" rel="noopener">Página oficial da ANA</a></li>' for key,item in metadata.items())
    crossings = ''.join('<p>' + esc(p) + '</p>' for p in DATA['crossings'])
    content = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="13ª reunião do Pantanal, 21/10/2026: conteúdo integral da Nota Técnica, quatro verticais, 18 figuras originais, cruzamentos e estratégia de Manso."><title>Pantanal · 13ª reunião · Nota Técnica integral</title><style>{CSS}</style></head><body id="topo"><header><div class="eyebrow">SOE/ANA · Gabinete | Acompanhamento técnico</div><h1>Alto Paraguai · Pantanal<br>Condições hidrometeorológicas e operação de Manso</h1><p class="lead"><strong>{esc(DATA['title'])}</strong></p><p>{esc(DATA['date'])} · Consolidação após o encerramento da reunião</p><p class="hero-meta">Conteúdo da NT final · 4 verticais · 18 figuras originais · Edição web 2.0</p><div class="header-links"><a href="documentos/NT_Pantanal_13a_21102026_WEB.pdf" download>Baixar PDF desta edição web</a><button type="button" onclick="window.print()">Imprimir / salvar PDF</button></div></header><nav aria-label="Navegação da Nota Técnica"><a href="#executivo">Síntese</a><a href="#inmet">INMET/INPE</a><a href="#cemaden">CEMADEN</a><a href="#sgb">SGB</a><a href="#ons">ONS</a><a href="#manso">Estratégia de Manso</a><a href="#cruzamentos">Cruzamentos</a><a href="#encaminhamentos">Encaminhamentos</a><a href="#fontes">Fontes</a></nav><main>
<section class="chapter" id="executivo"><div class="section-tag">Leitura executiva</div><h2>Retomada das chuvas, persistência da seca hidrológica</h2><p>{esc(DATA['summary'])}</p><div class="metrics"><div class="metric"><span>Ladário · cota observada</span><b>123 cm</b><small>CEMADEN · 21/10/2026</small></div><div class="metric"><span>Porto Murtinho · cota observada</span><b>320 cm</b><small>CEMADEN · 21/10/2026</small></div><div class="metric"><span>Manso · volume útil observado</span><b>71,9%</b><small>ONS · 20/10 · página 11</small></div><div class="metric"><span>Manso · volume útil projetado</span><b>65,4%</b><small>ONS · cenário até 30/11</small></div></div><div class="note"><strong>Escopo e registro.</strong> {esc(DATA['status'])}</div><p class="small">A análise e as 18 figuras selecionadas da NT final são apresentadas abaixo, por instituição. As legendas explicativas e os recursos de navegação pertencem a esta edição web. O DOCX final anteriormente entregue permanece inalterado.</p></section>
{''.join(sections)}
<section class="chapter" id="manso"><div class="section-tag">Leitura operacional</div><h2>Estratégia para Manso: comparar cenários, preservar os usos a jusante</h2><p>A proposta analítica registrada na NT é comparar a operação com defluência de 95 m³/s, a alternativa de 80 m³/s e uma trajetória variável. Não há registro recebido de aprovação, pela reunião, de uma redução de defluência.</p><div class="tablewrap"><table><thead><tr><th>Cenário</th><th>Informação disponível</th><th>Condição de interpretação</th></tr></thead><tbody><tr><td>95 m³/s</td><td>Cenário apresentado pelo ONS; afluência média de 63 m³/s e volume final de 65,4% até 30/11.</td><td>Resultado condicional às premissas do modelo e à operação simulada.</td></tr><tr><td>80 m³/s</td><td>Alternativa sugerida para comparação; mínimo informado na apresentação com referência à FSARH 5645/2024.</td><td>Não há volume final simulado fornecido para esta alternativa. Mínimo informado não significa autorização automática para operar nesse valor.</td></tr><tr><td>Defluência variável</td><td>Alternativa adaptativa para avaliação conforme afluências, previsões e condições a jusante.</td><td>Requer simulação, critérios explícitos e verificação das restrições pertinentes.</td></tr></tbody></table></div><h3>Ordem de grandeza do armazenamento preservado</h3><div class="equation">ΔV = (95 − 80) × 86.400 × 41 / 1.000.000<br>ΔV = 53,136 hm³ ≈ 1,80 ponto percentual de 2.951 hm³</div><p class="small">Estimativa incremental simplificada, adotando 41 dias e mantendo os demais termos iguais. Não representa uma previsão de volume final, não reproduz a simulação do ONS e não quantifica efeitos hidráulicos a jusante.</p><div class="note warning"><strong>Limite da recomendação.</strong> A preservação de armazenamento precisa ser confrontada com as necessidades e restrições a jusante. Não se transfere automaticamente para Manso uma regra de operação de outro sistema hídrico.</div></section>
<section class="chapter" id="cruzamentos"><div class="section-tag">Integração entre instituições</div><h2>Cruzamentos técnicos e consequências operacionais</h2>{crossings}<div class="tablewrap"><table><thead><tr><th>Cruzamento</th><th>Consequência para a interpretação</th></tr></thead><tbody><tr><td>INMET/INPE × CEMADEN</td><td>Retomada pluviométrica e TSI de longo período podem coexistir; chuva recente não apaga a memória hidrológica acumulada.</td></tr><tr><td>SGB × CEMADEN</td><td>Comparar estação, data e indicador. Os registros de 20/10 e 21/10 não são observações simultâneas; índices de seca não são percentis de cota.</td></tr><tr><td>Previsões meteorológicas × ONS</td><td>Chuva prevista sobre a bacia ampla não equivale à afluência específica de Manso. O cenário de operação continua consumindo estoque nas premissas apresentadas.</td></tr><tr><td>Horizonte de 180 dias × operação corrente</td><td>A amplitude de cenários de Ladário orienta vigilância e atualização; não define uma vazão diária de operação do reservatório.</td></tr></tbody></table></div></section>
<section class="chapter" id="encaminhamentos"><div class="section-tag">Pós-reunião</div><h2>Quadro de acompanhamento e encaminhamentos técnicos</h2><div class="tablewrap"><table><thead><tr><th>Referência institucional</th><th>Acompanhamento proposto na NT</th><th>Status</th></tr></thead><tbody>{followup}</tbody></table></div><h3>Registro da reunião</h3><p>{esc(DATA['record'])}</p></section>
<section class="chapter" id="fontes"><div class="section-tag">Documentação e rastreabilidade</div><h2>Fontes e apresentações integrais</h2><p>Os gráficos foram reproduzidos das apresentações da reunião de 21/10/2026. As quatro cópias abaixo foram verificadas por SHA-256 em relação aos arquivos usados na consolidação técnica. Os cortes de observação e previsão permanecem os de cada instituição.</p><ul class="source-list">{source_links}</ul><p><a href="documentos/NT_Pantanal_13a_21102026_WEB.pdf" download>Baixar PDF integral desta edição web</a> · <a href="manifesto.json">Consultar manifesto das fontes e da publicação</a></p><div class="note"><strong>Documento de referência preservado.</strong> NT_Pantanal_13a_21102026_FINAL.docx, já entregue ao usuário. O PDF acessível nesta página é a exportação da edição web, com as mesmas 18 figuras e com as legendas e quadros de leitura aqui apresentados; não substitui nem altera o DOCX original.</div><p class="small">Edição web 2.0: substitui a síntese reduzida por uma publicação completa das quatro verticais e das figuras selecionadas. Fontes e anexos permanecem ao final; não antecedem o conteúdo técnico.</p></section>
</main><footer><strong>Elaboração técnica — Gabinete/SOE/ANA | com suporte de IA | 21/10/2026</strong><br>Repositório pessoal de protótipos. Esta publicação não substitui ato administrativo, ata ou manifestação institucional formal.<br><a href="#topo">Voltar ao início</a></footer><dialog id="zoom" aria-label="Figura ampliada"><button type="button">Fechar ×</button><img alt="Figura ampliada"><p id="zoom-caption"></p></dialog><script>{SCRIPT}</script></body></html>'''
    (work / 'index.html').write_text(content, encoding='utf-8')
    soup = BeautifulSoup(content, 'html.parser')
    figures = soup.select('figure img')
    assert len(figures) == 18
    for image in figures:
        assert (work / image['src']).is_file(), image['src']
    for section in DATA['sections']:
        for text in section['paragraphs']:
            assert text in soup.get_text(' ', strip=True)
    print('HTML VERIFIED: four complete verticals; 18 local figures; original NT paragraphs retained.', flush=True)

def make_pdf_and_qa(work):
    from playwright.sync_api import sync_playwright
    out = work / 'documentos'
    out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        chrome = shutil.which('google-chrome') or shutil.which('google-chrome-stable') or shutil.which('chromium')
        options = {'headless': True, 'args': ['--no-sandbox']}
        if chrome:
            options['executable_path'] = chrome
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        page.goto((work / 'index.html').as_uri(), wait_until='networkidle')
        page.wait_for_function("Array.from(document.querySelectorAll('figure img')).every(i=>i.complete && i.naturalWidth>0)")
        assert page.locator('figure img').count() == 18
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
        qa = Path('/tmp/pantanal-publication-qa')
        qa.mkdir(exist_ok=True)
        page.screenshot(path=str(qa / 'desktop.png'), full_page=True)
        page.locator('#inmet .image-link').first.click()
        assert page.locator('dialog').evaluate('(d)=>d.open')
        page.keyboard.press('Escape')
        page.emulate_media(media='print')
        page.pdf(path=str(out / 'NT_Pantanal_13a_21102026_WEB.pdf'), format='A4', print_background=True, prefer_css_page_size=True)
        page.emulate_media(media='screen')
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(qa / 'mobile.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
        browser.close()
    doc = fitz.open(out / 'NT_Pantanal_13a_21102026_WEB.pdf')
    assert len(doc) >= 10
    assert sum(len(page.get_images()) for page in doc) >= 18
    print('PDF VERIFIED:', len(doc), 'pages; all figures present. DESKTOP/MOBILE QA passed.', flush=True)
    return len(doc)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-sources', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / '_staging')
    args = parser.parse_args()
    work = args.output.resolve()
    work.mkdir(parents=True, exist_ok=True)
    metadata = get_sources(work, args.local_sources)
    render_figures(work)
    make_html(work, metadata)
    pages = make_pdf_and_qa(work)
    manifest = {'publication_version': DATA['version'], 'meeting': '2026-10-21 / 13ª Pantanal', 'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'figure_count': 18, 'pdf_pages': pages, 'original_docx_modified': False, 'sources': metadata}
    (work / 'manifesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('READY FOR ATOMIC PUBLICATION:', str(work), flush=True)

if __name__ == '__main__':
    main()
