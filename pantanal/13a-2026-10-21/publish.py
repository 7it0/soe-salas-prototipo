#!/usr/bin/env python3
"""Responsive web publication; preserve the original DOCX and verified sources."""
from pathlib import Path
import importlib.util
import json
import sys

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pantanal_publication', root / 'build_publication.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.CSS += '''
body{overflow-wrap:anywhere}.chapter,.gallery>figure{min-width:0}.tablewrap{max-width:100%}
@media print{
  header{padding-bottom:5mm}
  .lead{font-size:12pt;line-height:1.4}
  #executivo>.small{display:none}
  .metrics{margin:4mm 0}
  .metric{padding:3mm}
  .note{padding:3mm 4mm;margin:4mm 0}
}
'''
# Recheck the hashes of committed source PDFs instead of fetching them again.
# Preserve the actual URLs discovered during the first successful validation.
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
