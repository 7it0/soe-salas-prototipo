#!/usr/bin/env python3
"""Editorial preflight: preserve analysis, figures and valid public PDF links."""
from pathlib import Path
from urllib.parse import urlsplit
import importlib.util
import hashlib
import fitz

ROOT=Path(__file__).resolve().parent
SITE='https://7it0.github.io/soe-salas-prototipo/paranapanema/10a-2026-10-22/'
spec=importlib.util.spec_from_file_location('paranapanema_build',ROOT/'build.py')
assert spec and spec.loader
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
# Number figures in actual reading order, not in original source-page order.
lookup={(item['source'],item['page']):item for item in module.DATA['figures']}
ordered=[]
for section in module.DATA['sections']:
    for index,block in enumerate(section['blocks']):
        for page in module.FIGURE_GROUPS.get(section['id'],{}).get(index,[]):
            ordered.append(lookup[(section['id'],page)])
assert len(ordered)==24 and len({(f['source'],f['page']) for f in ordered})==24
module.DATA['figures']=ordered
module.CSS+='\n@media print{p{break-inside:avoid}.tablewrap{break-inside:avoid}footer p{break-inside:avoid}}\n'

original_render=module.render_and_test

def finalize_pdf_links(work,qa,all_paragraphs):
    count=original_render(work,qa,all_paragraphs)
    path=work/'documentos'/module.PDF_NAME
    pdf=fitz.open(path)
    before_text=[page.get_text() for page in pdf]
    before_render=[hashlib.sha256(page.get_pixmap(matrix=fitz.Matrix(.5,.5),alpha=False).samples).hexdigest() for page in pdf]
    corrected=0
    for page in pdf:
        for link in page.get_links():
            uri=link.get('uri','')
            parts=urlsplit(uri)
            if parts.hostname in ('127.0.0.1','localhost'):
                link['uri']=SITE+parts.path.lstrip('/')
                if parts.query:link['uri']+='?'+parts.query
                if parts.fragment:link['uri']+='#'+parts.fragment
                page.update_link(link)
                corrected+=1
    metadata=pdf.metadata
    metadata.update({'title':'Nota Técnica — 10ª Reunião do Paranapanema — 22/10/2026',
                     'author':'Supervisão: José Aguiar de Lima Jr. — Especialista em Geoprocessamento — Gabinete/SOE/ANA; suporte de IA',
                     'subject':'Consolidação documental CEMADEN e ONS; edição de 23/10/2026',
                     'keywords':'Paranapanema, SOE, ANA, CEMADEN, ONS, hidrologia, reservatórios'})
    pdf.set_metadata(metadata)
    temporary=path.with_suffix('.checked.pdf')
    pdf.save(temporary,garbage=4,deflate=True)
    pdf.close()
    temporary.replace(path)
    verified=fitz.open(path)
    assert len(verified)==count
    assert [page.get_text() for page in verified]==before_text
    after_render=[hashlib.sha256(page.get_pixmap(matrix=fitz.Matrix(.5,.5),alpha=False).samples).hexdigest() for page in verified]
    assert before_render==after_render, 'Visual content changed while fixing links'
    for page in verified:
        for link in page.get_links():
            assert urlsplit(link.get('uri','')).hostname not in ('127.0.0.1','localhost')
    verified.close()
    print('PDF LINKS VERIFIED:',corrected,'public URLs; all page text and rendered content unchanged.',flush=True)
    return count

module.render_and_test=finalize_pdf_links
module.main()
