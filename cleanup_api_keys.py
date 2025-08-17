#!/usr/bin/env python3
"""
Clean up hardcoded API keys from Python files
Replace with environment variable references for security
"""

import os
import re
import glob

# API keys to replace (partial matches for security)
API_KEY_PATTERNS = [
    r'API_KEY = "sk_[a-f0-9]+"',
    r'ELEVENLABS_API_KEY = "sk_[a-f0-9]+"',
    r'API_KEY = "sk-proj-[A-Za-z0-9]+"'
]

# Replacement template
REPLACEMENT_TEMPLATE = '''API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is required")'''

def clean_file(filepath):
    """Clean API keys from a single file"""
    print(f"Cleaning: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace all API key patterns
    for pattern in API_KEY_PATTERNS:
        if re.search(pattern, content):
            print(f"  Found API key pattern: {pattern}")
            content = re.sub(pattern, 'API_KEY = os.getenv(\'ELEVENLABS_API_KEY\')', content)
    
    # Add environment check if API_KEY is used but no check exists
    if 'API_KEY' in content and 'if not API_KEY:' not in content and 'os.getenv' in content:
        # Find the line with API_KEY = os.getenv and add check after it
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'API_KEY = os.getenv' in line and 'if not API_KEY:' not in lines[i+1:i+3]:
                lines.insert(i+1, 'if not API_KEY:')
                lines.insert(i+2, '    raise ValueError("ELEVENLABS_API_KEY environment variable is required")')
                break
        content = '\n'.join(lines)
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Updated {filepath}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {filepath}")
        return False

def main():
    """Clean all Python files in the project"""
    project_root = r"c:\Users\Isaia\Documents\3D Printing\Projects\Button"
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(project_root):
        # Skip node_modules directories
        if 'node_modules' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to check")
    
    updated_count = 0
    for filepath in python_files:
        if clean_file(filepath):
            updated_count += 1
    
    print(f"\n✅ Cleanup complete! Updated {updated_count} files.")
    print("Remember to set ELEVENLABS_API_KEY environment variable before running these scripts.")

if __name__ == "__main__":
    main()
