#!/usr/bin/env python3
"""Editorial preflight: maintain analytical content and source figures."""
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parent
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
module.main()
