#!/usr/bin/env python3
"""Apply the GAOPS NT toolbar to the Pantanal publication, without editing its content.

Runs after the existing document builder. The technical main, footer, credits,
figures and PDF are preserved. CSV downloads contain only documented indicators.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import shutil
import threading
from decimal import Decimal
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
LABELS = ['Baixar NT completa · PDF', 'Ler NT integral', 'Baixar indicadores · CSV']
CSS = '''
/* NT actions v1.0: reference gaops-20261013/nt-final.html. */
header .nt-actions{display:flex;align-items:stretch;flex-wrap:wrap;gap:12px;margin-top:24px}
header .nt-actions .button{display:inline-flex;align-items:center;justify-content:center;min-height:50px;border:1px solid #b9d4d8;border-radius:7px;background:#fff;color:#07556b;padding:11px 18px;font:650 16px/1.65 system-ui,sans-serif;text-align:center;text-decoration:none;cursor:pointer;box-sizing:border-box;max-width:100%}
header .nt-actions .button.primary{background:#c9f3e8;border-color:transparent;color:#064f4b}
header .nt-actions .button:hover{background:#edf7f5;border-color:#75aaa9}
header .nt-actions .button.primary:hover{background:#b5eadb;border-color:transparent}
header .nt-actions .button:focus-visible,header .nt-print-button:focus-visible{outline:3px solid #ffe095;outline-offset:4px}
header .nt-secondary-actions{margin-top:10px}
header .nt-print-button{border:0;border-radius:0;background:transparent;color:#d6e9ed;padding:4px 0;font:400 13px/1.5 system-ui,sans-serif;text-decoration:underline;text-underline-offset:3px;cursor:pointer}
@media(max-width:520px){header .nt-actions .button{width:100%}}
@media print{header .nt-actions,header .nt-secondary-actions{display:none!important}}
'''

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def local_target(work: Path, href: str) -> Path:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        raise ValueError('Toolbar downloads must use local publication files')
    path = (work / parts.path).resolve()
    if not path.is_relative_to(work.resolve()):
        raise ValueError('Download path outside the meeting directory')
    if not path.is_file():
        raise FileNotFoundError(path)
    return path

def apply(work: Path) -> dict:
    index = work / 'index.html'
    soup = BeautifulSoup(index.read_text(encoding='utf-8'), 'html.parser')
    before_main = str(soup.main)
    before_footer = str(soup.footer)
    before_credit = str(soup.header.select_one('.supervision-credit'))
    before_images = [img['src'] for img in soup.select('figure img')]
    assert len(before_images) == 18
    toolbar = soup.header.select_one('.header-links')
    assert toolbar is not None, 'Missing publication toolbar'
    pdf_link = toolbar.select_one('a[href$=".pdf"]')
    assert pdf_link is not None, 'Missing original PDF link'
    pdf_href = pdf_link['href']
    pdf = local_target(work, pdf_href)
    assert pdf.read_bytes().startswith(b'%PDF')
    original_pdf_hash = sha(pdf)
    csv_source = ROOT / 'indicadores.csv'
    csv_output = work / 'indicadores.csv'
    if csv_source.resolve() != csv_output.resolve():
        shutil.copyfile(csv_source, csv_output)
    with csv_output.open(encoding='utf-8-sig', newline='') as f:
        records = list(csv.DictReader(f, delimiter=';'))
    assert len(records) == 18
    for row in records:
        assert row['instituicao'] and row['periodo'] and row['tipo'] and row['fonte_url']
        assert Decimal(row['valor'].replace(',', '.')).is_finite()
        assert int(row['pagina_fonte']) > 0
    assert soup.find(id='executivo') is not None
    toolbar.clear()
    toolbar['class'] = ['header-links', 'buttons', 'nt-actions']
    toolbar['role'] = 'group'
    toolbar['aria-label'] = 'Acesso à Nota Técnica e aos indicadores'
    toolbar['data-nt-actions-version'] = '1.0'
    entries = [(LABELS[0], pdf_href, 'primary'), (LABELS[1], '#executivo', ''), (LABELS[2], 'indicadores.csv', '')]
    for label, href, extra_class in entries:
        a = soup.new_tag('a', href=href)
        a['class'] = ['button'] + ([extra_class] if extra_class else [])
        a.string = label
        if href != '#executivo':
            a['download'] = Path(href).name
        if href == pdf_href:
            a['title'] = 'Nota Técnica integral em PDF — edição web com identificação de supervisão e suporte de IA'
        elif href == 'indicadores.csv':
            a['title'] = '18 indicadores documentados, com fonte, período e natureza do dado'
        toolbar.append(a)
    old_print = soup.header.select_one('.nt-secondary-actions')
    if old_print:
        old_print.decompose()
    secondary = soup.new_tag('div', attrs={'class': 'nt-secondary-actions screen-only'})
    print_button = soup.new_tag('button', attrs={'type': 'button', 'class': 'nt-print-button', 'onclick': 'window.print()'})
    print_button.string = 'Imprimir / salvar PDF'
    secondary.append(print_button)
    toolbar.insert_after(secondary)
    old_style = soup.find('style', id='nt-actions-style')
    if old_style:
        old_style.decompose()
    style = soup.new_tag('style', id='nt-actions-style')
    style.string = CSS
    soup.head.append(style)
    assert str(soup.main) == before_main, 'Technical main changed'
    assert str(soup.footer) == before_footer, 'Footer changed'
    assert str(soup.header.select_one('.supervision-credit')) == before_credit, 'Supervision credit changed'
    assert [img['src'] for img in soup.select('figure img')] == before_images
    assert sha(pdf) == original_pdf_hash, 'PDF changed'
    assert [a.get_text() for a in toolbar.select('a')] == LABELS
    index.write_text(str(soup), encoding='utf-8')
    manifest_file = work / 'manifesto.json'
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    manifest['navigation'] = {'component': 'botoes-nt', 'version': '1.0', 'reference': 'gaops-20261013/nt-final.html', 'actions': LABELS, 'indicator_rows': 18, 'technical_content_changed': False, 'supervision_credit_changed': False, 'pdf_changed_by_toolbar': False}
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('TOOLBAR: GAOPS labels/order/style; 18 CSV rows; all technical content, credits and PDF unchanged.', flush=True)
    return {'pdf_href': pdf_href, 'pdf_sha256': original_pdf_hash, 'csv_rows': len(records)}

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def browser_qa(work: Path, checks: dict) -> None:
    from playwright.sync_api import sync_playwright
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(work)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    qa = Path('/tmp/pantanal-publication-qa')
    qa.mkdir(exist_ok=True)
    url = f'http://127.0.0.1:{server.server_port}/index.html'
    try:
        with sync_playwright() as p:
            executable = shutil.which('google-chrome') or shutil.which('google-chrome-stable') or shutil.which('chromium')
            options = {'headless': True, 'args': ['--no-sandbox']}
            if executable:
                options['executable_path'] = executable
            browser = p.chromium.launch(**options)
            page = browser.new_page(viewport={'width':1440, 'height':1000}, accept_downloads=True)
            page.goto(url, wait_until='networkidle')
            page.wait_for_function("Array.from(document.querySelectorAll('figure img')).every(i=>i.complete && i.naturalWidth>0)")
            assert page.locator('figure img').count() == 18
            buttons = page.locator('header .nt-actions a')
            assert buttons.all_text_contents() == LABELS
            heights = buttons.evaluate_all('(els)=>els.map(e=>e.getBoundingClientRect().height)')
            assert max(heights)-min(heights) <= 1
            assert buttons.nth(0).evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(201, 243, 232)'
            assert buttons.nth(1).evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(255, 255, 255)'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
            page.locator('header').screenshot(path=str(qa / 'botoes-computador.png'))
            with page.expect_download() as pdf_event:
                buttons.nth(0).click()
            download = pdf_event.value
            assert sha(Path(download.path())) == checks['pdf_sha256']
            with page.expect_download() as csv_event:
                buttons.nth(2).click()
            downloaded_csv = Path(csv_event.value.path())
            with downloaded_csv.open(encoding='utf-8-sig', newline='') as f:
                assert len(list(csv.DictReader(f, delimiter=';'))) == checks['csv_rows']
            buttons.nth(1).click()
            assert page.evaluate('location.hash') == '#executivo'
            page.locator('header').scroll_into_view_if_needed()
            page.set_viewport_size({'width':390, 'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
            assert buttons.all_text_contents() == LABELS
            page.locator('header').screenshot(path=str(qa / 'botoes-celular.png'))
            page.emulate_media(media='print')
            assert not page.locator('header .nt-actions').is_visible()
            assert not page.locator('header .nt-secondary-actions').is_visible()
            browser.close()
        print('TOOLBAR QA PASSED: both downloads, integral-reading anchor, desktop/mobile layout and print visibility.', flush=True)
    finally:
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--skip-browser', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    checks = apply(output)
    if not args.skip_browser:
        browser_qa(output, checks)
