"""
Convert Markdown to DOCX via HTML with GitHub-like styling.
Uses LibreOffice headless for the HTML→DOCX step.
"""
import os, subprocess, sys
os.chdir('/home/user/audio')

import markdown

GITHUB_CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #24292e;
    max-width: 980px;
    margin: 40px auto;
    padding: 0 40px;
}
h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.25;
    margin-top: 24px;
    margin-bottom: 16px;
}
h1 {
    font-size: 2em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid #eaecef;
}
h2 {
    font-size: 1.5em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid #eaecef;
}
h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
h5 { font-size: 0.875em; }
h6 { font-size: 0.85em; color: #6a737d; }

p { margin-top: 0; margin-bottom: 16px; }

ul, ol {
    padding-left: 2em;
    margin-top: 0;
    margin-bottom: 16px;
}
li { margin-top: 0.25em; }
li + li { margin-top: 4px; }

table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 16px;
    display: table;
    overflow: auto;
}
table th {
    font-weight: 600;
    background-color: #f6f8fa;
    padding: 6px 13px;
    border: 1px solid #dfe2e5;
}
table td {
    padding: 6px 13px;
    border: 1px solid #dfe2e5;
}
table tr:nth-child(even) { background-color: #f6f8fa; }
table tr:hover { background-color: #f0f3f6; }

code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 85%;
    background-color: rgba(27,31,35,0.05);
    padding: 0.2em 0.4em;
    border-radius: 3px;
}
pre {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 85%;
    background-color: #f6f8fa;
    border-radius: 3px;
    padding: 16px;
    overflow: auto;
    line-height: 1.45;
    margin-bottom: 16px;
}
pre code {
    background: transparent;
    padding: 0;
}

blockquote {
    padding: 0 1em;
    color: #6a737d;
    border-left: 0.25em solid #dfe2e5;
    margin: 0 0 16px 0;
}

strong { font-weight: 600; }
em { font-style: italic; }

hr {
    height: 0.25em;
    padding: 0;
    margin: 24px 0;
    background-color: #e1e4e8;
    border: 0;
}

/* Red flag blockquotes */
blockquote strong { color: #d73a49; }
"""

def convert(md_path, docx_path):
    with open(md_path, encoding='utf-8') as f:
        md_text = f.read()

    html_body = markdown.markdown(
        md_text,
        extensions=['tables', 'fenced_code', 'attr_list', 'md_in_html']
    )

    html_full = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{GITHUB_CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    html_path = md_path.replace('.md', '_github.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_full)

    print(f"HTML written: {html_path}")

    # LibreOffice headless conversion
    result = subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'docx',
        '--outdir', os.path.dirname(docx_path),
        html_path
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.returncode != 0:
        print("STDERR:", result.stderr)
        sys.exit(1)

    # LibreOffice names it based on html filename
    generated = html_path.replace('.html', '.docx')
    if generated != docx_path:
        os.rename(generated, docx_path)

    print(f"DOCX written: {docx_path}")

convert(
    '/home/user/audio/KNO_Richtlijnen_Uitgebreid.md',
    '/home/user/audio/KNO_Richtlijnen_Uitgebreid.docx'
)
