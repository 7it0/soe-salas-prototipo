#!/usr/bin/env python3
"""Publish the meeting with explicit human supervision and AI-support credits.

Editorial changes only. Preserve all technical paragraphs and 18 source figures.
The original DOCX remains untouched.
"""
from pathlib import Path
import importlib.util
import json
import shutil
import sys
from bs4 import BeautifulSoup
import fitz

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pantanal_publication', root / 'build_publication.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

NAME = 'José Aguiar de Lima Jr.'
ROLE = 'Especialista em Geoprocessamento'
UNIT = 'Gabinete da Superintendência de Operações e Eventos Críticos — SOE/ANA'
AI = 'Elaboração com suporte de inteligência artificial (IA).'
module.DATA['version'] = '2.1'
module.CSS += '''
body{overflow-wrap:anywhere}.chapter,.gallery>figure{min-width:0}.tablewrap{max-width:100%}
.supervision-credit{border-left:3px solid #87d1c6;padding:4px 0 4px 18px;margin:24px 0 16px;max-width:1050px}
.supervision-credit p{margin:5px 0;font-size:15px;line-height:1.5}
.supervision-credit .credit-name{font-size:18px}
.supervision-credit .credit-ai{font-size:13px;color:#d6e9ed}
footer .supervision-credit{margin:0 0 20px;padding:0 0 0 15px}
footer .supervision-credit .credit-name{font-size:16px}
footer .supervision-credit p{font-size:13px}
footer .editorial-revision{display:block;font-size:12px;margin-top:12px;color:#c5dce1}
@media print{
  header{padding:22mm 0 5mm;break-after:page}
  .lead{font-size:12pt;line-height:1.4}
  #executivo>.small{display:none}
  .metrics{margin:4mm 0}
  .metric{padding:3mm}
  .note{padding:3mm 4mm;margin:4mm 0}
  .supervision-credit{border-left-color:#138577;margin-top:8mm;padding-left:5mm;break-inside:avoid}
  .supervision-credit p{font-size:10pt;color:#243d49}
  .supervision-credit .credit-name{font-size:12pt}
  .supervision-credit .credit-ai{font-size:9pt;color:#536f78}
  footer .supervision-credit .credit-name{font-size:10pt}
  footer .supervision-credit p{font-size:9pt}
  footer .editorial-revision{color:#536f78}
}
'''

original_make_html = module.make_html

def add_supervision_credits(work, metadata):
    original_make_html(work, metadata)
    path = work / 'index.html'
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    original_main_text = soup.main.get_text(' ', strip=True)
    original_images = [img['src'] for img in soup.select('figure img')]
    credit_html = (
        '<div class="supervision-credit" aria-label="Supervisão técnica e suporte de IA">'
        f'<p class="credit-name">Supervisionado por <strong>{NAME}</strong></p>'
        f'<p>{ROLE}<br>{UNIT}</p>'
        f'<p class="credit-ai">{AI}</p></div>'
    )
    opening_credit = BeautifulSoup(credit_html, 'html.parser').div
    soup.header.select_one('.header-links').insert_before(opening_credit)
    soup.header.select_one('.hero-meta').string = 'Conteúdo da NT final · 4 verticais · 18 figuras originais · Edição web 2.1'
    soup.footer.clear()
    footer_credit = BeautifulSoup(credit_html, 'html.parser').div
    soup.footer.append(footer_credit)
    extra = BeautifulSoup(
        '<p>21 de outubro de 2026 · Consolidação técnica da 13ª reunião do Pantanal.<br>'
        'Repositório pessoal de protótipos. Esta publicação não substitui ato administrativo, ata ou manifestação institucional formal.</p>'
        '<span class="editorial-revision">Revisão editorial 2.1: identificação de supervisão e suporte de IA. Conteúdo técnico e figuras preservados.</span>'
        '<p><a href="#topo">Voltar ao início</a></p>', 'html.parser')
    for element in list(extra.contents):
        soup.footer.append(element)
    author = soup.new_tag('meta', attrs={'name': 'author', 'content': f'Supervisão: {NAME} — {ROLE} — Gabinete/SOE/ANA; suporte de IA'})
    soup.head.append(author)
    assert soup.main.get_text(' ', strip=True) == original_main_text, 'Technical content changed unexpectedly'
    assert [img['src'] for img in soup.select('figure img')] == original_images
    assert len(original_images) == 18
    assert NAME in soup.header.get_text() and NAME in soup.footer.get_text()
    assert ROLE in soup.header.get_text() and ROLE in soup.footer.get_text()
    path.write_text(str(soup), encoding='utf-8')
    print('EDITORIAL QA: named supervision in opening and footer; technical main and 18 images unchanged.', flush=True)

module.make_html = add_supervision_credits

PDF_FOOTER = '''<div style="font-family:Arial,sans-serif;font-size:9px;line-height:1.35;color:#45616b;width:100%;margin:0 16mm;border-top:1px solid #ccdadd;padding-top:4px;text-align:center;">
<div>Supervisionado por <strong>José Aguiar de Lima Jr.</strong> · Especialista em Geoprocessamento</div>
<div>Gabinete · Superintendência de Operações e Eventos Críticos — SOE/ANA</div>
<div>Elaboração com suporte de inteligência artificial (IA) · 21/10/2026 · Página <span class="pageNumber"></span> de <span class="totalPages"></span></div>
</div>'''

def make_pdf_and_qa(work):
    from playwright.sync_api import sync_playwright
    out = work / 'documentos'
    out.mkdir(exist_ok=True)
    qa = Path('/tmp/pantanal-publication-qa')
    qa.mkdir(exist_ok=True)
    pdf_path = out / 'NT_Pantanal_13a_21102026_WEB.pdf'
    with sync_playwright() as p:
        chrome = shutil.which('google-chrome') or shutil.which('google-chrome-stable') or shutil.which('chromium')
        options = {'headless': True, 'args': ['--no-sandbox']}
        if chrome:
            options['executable_path'] = chrome
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport={'width':1440, 'height':1000}, device_scale_factor=1)
        page.goto((work / 'index.html').as_uri(), wait_until='networkidle')
        page.wait_for_function("Array.from(document.querySelectorAll('figure img')).every(i=>i.complete && i.naturalWidth>0)")
        assert page.locator('figure img').count() == 18
        assert page.locator('header .supervision-credit').count() == 1
        assert page.locator('footer .supervision-credit').count() == 1
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
        page.screenshot(path=str(qa / 'desktop.png'), full_page=True)
        page.locator('header').screenshot(path=str(qa / 'creditos-abertura.png'))
        page.locator('footer').screenshot(path=str(qa / 'creditos-rodape.png'))
        page.locator('#inmet .image-link').first.click()
        assert page.locator('dialog').evaluate('(d)=>d.open')
        page.keyboard.press('Escape')
        page.emulate_media(media='print')
        page.pdf(path=str(pdf_path), format='A4', print_background=True,
                 prefer_css_page_size=True, display_header_footer=True,
                 header_template='<span></span>', footer_template=PDF_FOOTER)
        page.emulate_media(media='screen')
        page.set_viewport_size({'width':390, 'height':844})
        page.screenshot(path=str(qa / 'mobile.png'), full_page=True)
        page.locator('header').screenshot(path=str(qa / 'creditos-celular.png'))
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
        browser.close()
    pdf = fitz.open(pdf_path)
    assert len(pdf) >= 10
    assert sum(len(page.get_images()) for page in pdf) >= 18
    for i, page in enumerate(pdf):
        text = page.get_text()
        assert NAME in text, f'Supervision credit missing from PDF page {i+1}'
        assert ROLE in text, f'Role missing from PDF page {i+1}'
        assert 'inteligência artificial' in text, f'AI credit missing from PDF page {i+1}'
    pdf[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5), alpha=False).save(qa / 'pdf-abertura.png')
    pdf[-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5), alpha=False).save(qa / 'pdf-final.png')
    print('PDF VERIFIED:', len(pdf), 'pages; supervision, role and AI credit on every page; 18 figures; responsive QA passed.', flush=True)
    return len(pdf)

module.make_pdf_and_qa = make_pdf_and_qa

# Revalidate committed source PDFs and preserve the previously verified URLs.
previous_path = root / 'manifesto.json'
cached_sources = root / 'fontes'
if previous_path.is_file() and cached_sources.is_dir() and '--local-sources' not in sys.argv:
    previous = json.loads(previous_path.read_text(encoding='utf-8'))['sources']
    original_get_sources = module.get_sources
    def checked_cached_sources(work, local):
        current = original_get_sources(work, local)
        for key, value in current.items():
            old = previous.get(key, {})
            if old.get('sha256') == value['sha256']:
                value['view'] = old['view']
                value['download'] = old['download']
        return current
    module.get_sources = checked_cached_sources
    sys.argv.extend(['--local-sources', str(cached_sources)])
module.main()
