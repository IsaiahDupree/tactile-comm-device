#!/usr/bin/env python3
"""
Convert the Tactile Communication Device User Guide from Markdown to Word-compatible HTML
"""

import os
import re

def markdown_to_html(md_content):
    """Simple markdown to HTML converter for basic formatting"""
    
    # Convert headers
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md_content, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # Convert bold text
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Convert italic text
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Convert code blocks
    html = re.sub(r'```([^`]+)```', r'<pre>\1</pre>', html, flags=re.DOTALL)
    
    # Convert horizontal rules
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
    
    # Convert unordered lists
    lines = html.split('\n')
    in_list = False
    result_lines = []
    
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            content = line.strip()[2:]  # Remove '- '
            result_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            result_lines.append(line)
    
    if in_list:
        result_lines.append('</ul>')
    
    html = '\n'.join(result_lines)
    
    # Convert paragraphs (simple approach)
    paragraphs = html.split('\n\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith('<'):
            para = f'<p>{para}</p>'
        formatted_paragraphs.append(para)
    
    return '\n\n'.join(formatted_paragraphs)

def main():
    # Read the markdown file
    md_file = 'DEVICE_GUIDE.md'
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find {md_file}")
        return
    
    # Convert markdown to HTML
    html_content = markdown_to_html(md_content)
    
    # Create a complete HTML document with Word-compatible styling
    html_doc = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Tactile Communication Device - User Guide</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 1in;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            page-break-before: avoid;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
            margin-top: 30px;
            page-break-before: avoid;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 25px;
        }}
        p {{
            margin: 10px 0;
            text-align: justify;
        }}
        code {{
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: Consolas, 'Courier New', monospace;
            font-size: 90%;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border: 1px solid #e9ecef;
            font-family: Consolas, 'Courier New', monospace;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        strong {{
            color: #2c3e50;
        }}
        hr {{
            border: none;
            border-top: 2px solid #bdc3c7;
            margin: 30px 0;
        }}
        .page-break {{
            page-break-before: always;
        }}
        @media print {{
            body {{ margin: 0.5in; }}
            h1, h2, h3 {{ page-break-after: avoid; }}
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>'''
    
    # Save as HTML file
    output_file = 'Tactile_Communication_Device_Guide.html'
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_doc)
        
        print(f"Successfully converted to HTML: {output_file}")
        print("\nTo convert to Word document:")
        print("1. Open the HTML file in Microsoft Word")
        print("2. Go to File > Save As")
        print("3. Choose 'Word Document (*.docx)' as the file type")
        print("4. Click Save")
        
    except Exception as e:
        print(f"Error writing HTML file: {e}")

if __name__ == "__main__":
    main()
