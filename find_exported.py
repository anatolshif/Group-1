import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def find_exported_true(manifest_path):
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        android_ns = "http://schemas.android.com/apk/res/android"
        exported_components = []

        for elem in root.iter():
            exported = elem.attrib.get(f"{{{android_ns}}}exported")
            if exported and exported.lower() == "true":
                name = elem.attrib.get(f"{{{android_ns}}}name", "Unknown")
                exported_components.append({
                    "tag": elem.tag,
                    "name": name
                })

        return exported_components
    except Exception as e:
        print(f" Error reading {manifest_path}: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_exported.py <path-to-AndroidManifest.xml>")
        sys.exit(1)

    manifest_file = Path(sys.argv[1])
    if not manifest_file.exists():
        print(f" File not found: {manifest_file}")
        sys.exit(1)

    results = find_exported_true(manifest_file)

    if results:
        print(f"\n Found {len(results)} exported components in {manifest_file}:\n")
        for item in results:
            print(f"- <{item['tag']}>  name: {item['name']}")
    else:
        print(f"\n No components with android:exported=\"true\" found in {manifest_file}")
