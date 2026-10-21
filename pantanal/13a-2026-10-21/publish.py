#!/usr/bin/env python3
"""Run publication with responsive wrapping for long document names."""
from pathlib import Path
import importlib.util

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pantanal_publication', root / 'build_publication.py')
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
module.CSS += '\nbody{overflow-wrap:anywhere}.chapter,.gallery>figure{min-width:0}.tablewrap{max-width:100%}\n'
module.main()
