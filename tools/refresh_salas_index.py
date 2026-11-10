#!/usr/bin/env python3
"""Refresh the existing basin index without rewriting any meeting publication.
Keep the historical catalog and discover additional meetings from their manifests.
All links are still validated by build_salas_index before publication.
"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import importlib.util
import json
import re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('salas_legacy', ROOT / 'tools/build_salas_index.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
GROUPS = {
    'gaops': ('Paraíba do Sul · GAOPS', 'paraiba-do-sul'),
    'pantanal': ('Alto Paraguai · Pantanal', 'pantanal'),
    'parana': ('Paraná · Região Hidrográfica', 'parana'),
    'paranapanema': ('Paranapanema', 'paranapanema'),
    'regiao-norte': ('Região Norte', 'regiao-norte'),
    'regiao-sul': ('Região Sul', 'regiao-sul'),
    'sao-francisco': ('São Francisco', 'sao-francisco'),
    'tocantins': ('Tocantins', 'tocantins'),
}
LABELS = {'inpe': 'INPE/INMET', 'inmet': 'INMET', 'cemaden': 'CEMADEN',
          'ons': 'ONS', 'sgb': 'SGB', 'censipam': 'CENSIPAM', 'ana': 'ANA'}


def main():
    catalog = [dict(item) for item in legacy.MEETINGS]
    by_page = {item['page']: item for item in catalog}
    discovered = []
    for folder, (group, slug) in GROUPS.items():
        for manifest_path in sorted((ROOT / folder).glob('*/manifesto.json')):
            page = manifest_path.parent / 'index.html'
            if not page.is_file():
                continue
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            relative = page.relative_to(ROOT).as_posix()
            soup = BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser')
            heading = soup.find('h1')
            title = heading.get_text(' ', strip=True) if heading else manifest.get('meeting', '')
            number = re.search(r'\b\d+\s*ª', title)
            date = manifest.get('date', '')
            if not number or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
                raise ValueError('Unusable meeting metadata: ' + str(manifest_path))
            raw_status = str(manifest.get('status', '')).strip()
            status_lower = raw_status.lower()
            version = str(manifest.get('version', '')).strip()
            if 'nt final' in status_lower:
                state = 'NT final da reunião'
                edition = ('Versão ' + version if version else 'Versão final')
                if 'revis' in status_lower:
                    edition += ' · sujeita à revisão da equipe'
            elif 'prévia' in status_lower or 'previa' in status_lower:
                state = 'Prévia técnica'
                edition = 'Versão ' + version if version else 'Prévia documental'
            else:
                old = by_page.get(relative, {})
                state = old.get('state') or raw_status or 'Publicação documental'
                edition = old.get('edition') or ('Versão ' + version if version else 'Edição publicada')
            if relative in by_page:
                # Retain existing descriptions and dates; only reflect explicit editorial status.
                if 'nt final' in status_lower or 'prévia' in status_lower or 'previa' in status_lower:
                    by_page[relative].update(state=state, edition=edition)
                continue
            institutions = list(dict.fromkeys(LABELS.get(key, key.upper())
                                             for key in manifest.get('sources', {})))
            description = ('Materiais de ' + ', '.join(institutions) + '. ') if institutions else ''
            if isinstance(manifest.get('figure_count'), int):
                description += str(manifest['figure_count']) + ' reproduções identificadas. '
            if isinstance(manifest.get('indicator_rows'), int):
                description += str(manifest['indicator_rows']) + ' registros numéricos. '
            description += 'Consulte a NT para o escopo e as ressalvas documentais.'
            item = dict(group=group, slug=slug, date=date, number=number.group().replace(' ', ''),
                        title=title, page=relative, state=state, edition=edition,
                        description=description)
            catalog.append(item)
            by_page[relative] = item
            discovered.append(relative)
    # Keep the established basin order, and let the renderer sort each basin by date.
    group_order = list(dict.fromkeys(item['group'] for item in legacy.MEETINGS))
    catalog.sort(key=lambda item: group_order.index(item['group']))
    legacy.MEETINGS = catalog
    legacy.main()
    index = ROOT / 'salas/index.html'
    html = index.read_text(encoding='utf-8')
    today = datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y')
    html = html.replace('inventariadas em 29/10/2026', 'índice atualizado em ' + today)
    index.write_text(html, encoding='utf-8')
    records = json.loads((ROOT / 'salas/reunioes.json').read_text(encoding='utf-8'))['records']
    gaops = [item for item in records if item['page'] == 'gaops/116a-2026-11-10/index.html']
    assert len(gaops) == 1, '116ª GAOPS absent or duplicated'
    assert gaops[0]['state'] == 'NT final da reunião', gaops[0]
    assert gaops[0]['pdf'] and gaops[0]['pdf'].endswith('_FINAL.pdf'), gaops[0]
    assert gaops[0]['annex'] and gaops[0]['csv'], gaops[0]
    print('Added manifest-backed meetings:', json.dumps(discovered, ensure_ascii=False))
    print('116ª GAOPS: final HTML, final PDF, Anexo I and indicators verified.')


if __name__ == '__main__':
    main()
