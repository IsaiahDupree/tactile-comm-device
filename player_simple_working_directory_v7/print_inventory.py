def print_inventory(title, inv):
    """Show a factual summary (only keys that actually have files)"""
    print(f"\n=== {title} ===")
    any_files = False
    for k, files in inv.items():
        if files:
            any_files = True
            print(f"{k}: {len(files)} file(s)")
            for f in files[:5]:
                print(f"  • {f['name']} ({f['size']} bytes)")
    if not any_files:
        print("(no files found)")
