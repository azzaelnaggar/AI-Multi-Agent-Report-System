# tools/pdf_tool.py
# Input
# md_text: Markdown text to convert
# out_filename: desired output PDF name (but we’ll fallback to HTML)

# Output
# Returns a string path pointing to the generated HTML file.

import markdown2
from pathlib import Path

def md_to_pdf(md_text: str, out_filename: str = "outputs/report.pdf") -> str:
    Path("outputs").mkdir(exist_ok=True)
    html = markdown2.markdown(md_text)
    # For now, just save as HTML since weasyprint is not working on Windows
    html_filename = out_filename.replace('.pdf', '.html')
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html)
    return html_filename
