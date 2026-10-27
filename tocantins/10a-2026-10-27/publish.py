#!/usr/bin/env python3
"""Run the existing builder with a body-only PDF text check.
The content and layout are unchanged. Running headers/footers must not interrupt
comparison of a paragraph that crosses a page boundary.
"""
from pathlib import Path
path=Path(__file__).resolve().with_name('build.py')
source=path.read_text(encoding='utf-8')
old="text=norm(' '.join(p.get_text() for p in d))"
new="text=norm(' '.join(p.get_text(clip=fitz.Rect(40,45,p.rect.width-40,p.rect.height-65)) for p in d))"
if old in source:
    assert source.count(old)==1
    source=source.replace(old,new)
else:
    assert new in source, 'PDF validation code changed; review required'
exec(compile(source,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
