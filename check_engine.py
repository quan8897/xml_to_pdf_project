from utils_word import extract_tax_metadata, generate_tax_pdf
import os

print("=== Kiểm tra maTKhai ===")
for f in sorted(os.listdir('problem')):
    if not f.endswith('.xml'): continue
    with open(os.path.join('problem', f), 'rb') as fh:
        xml = fh.read()
    meta = extract_tax_metadata(xml)
    print(f"File: {f}")
    print(f"  maTKhai = {meta['form']!r}")
    print(f"  MST     = {meta['mst']!r}")

print()
print("=== Test PDF size (>200KB = Word template, <150KB = ReportLab fallback) ===")
for f in sorted(os.listdir('problem')):
    if not f.endswith('.xml'): continue
    with open(os.path.join('problem', f), 'rb') as fh:
        xml = fh.read()
    try:
        buf = generate_tax_pdf(xml)
        size = len(buf.getvalue())
        engine = "WORD TEMPLATE" if size > 200000 else "REPORTLAB FALLBACK"
        print(f"  {engine} | {size:,} bytes | {f}")
    except Exception as e:
        print(f"  ERROR: {e} | {f}")
