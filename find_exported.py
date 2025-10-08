import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def find_exported_true(manifest_path):
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        android_ns = "http://schemas.android.com/apk/res/android"
        app_ns = "http://schemas.android.com/apk/res-auto"
        
        # Initialize results dictionary
        results = {
            "package_name": root.get("package", "Unknown"),
            "exported_components": [],
            "permissions": [],
            "uses_permissions": [],
            "is_debuggable": False,
            "is_backup_enabled": False,
            "has_network_security_config": False,
            "flutter_embedding": None,
            "version_code": root.get(f"{{{android_ns}}}versionCode", "Unknown"),
            "version_name": root.get(f"{{{android_ns}}}versionName", "Unknown")
        }

        # Get package name
        package_name = root.get("package", "Unknown")
        
        # Check for debuggable
        application = root.find("application")
        if application is not None:
            debuggable = application.get(f"{{{android_ns}}}debuggable")
            if debuggable and debuggable.lower() == "true":
                results["is_debuggable"] = True
            
            # Check for backup enabled
            allow_backup = application.get(f"{{{android_ns}}}allowBackup")
            if allow_backup and allow_backup.lower() == "true":
                results["is_backup_enabled"] = True
            
            # Check for network security config
            network_security_config = application.get(f"{{{android_ns}}}networkSecurityConfig")
            if network_security_config:
                results["has_network_security_config"] = True
                results["network_security_config_file"] = network_security_config
            
            # Check for Flutter embedding
            meta_data_elements = application.findall("meta-data")
            for meta in meta_data_elements:
                name = meta.get(f"{{{android_ns}}}name")
                value = meta.get(f"{{{android_ns}}}value")
                if name == "flutterEmbedding":
                    results["flutter_embedding"] = value
                    break

        # Find exported components
        for elem in root.iter():
            exported = elem.attrib.get(f"{{{android_ns}}}exported")
            if exported and exported.lower() == "true":
                name = elem.attrib.get(f"{{{android_ns}}}name", "Unknown")
                # Convert relative names to absolute
                if name.startswith("."):
                    name = package_name + name
                elif name.startswith("android."):
                    pass  # Keep as is
                elif "." not in name:
                    name = package_name + "." + name
                
                exported_components.append({
                    "tag": elem.tag,
                    "name": name,
                    "permission": elem.attrib.get(f"{{{android_ns}}}permission", "None")
                })

        # Find permissions declared by the app
        permissions = root.findall("permission")
        for perm in permissions:
            perm_name = perm.get(f"{{{android_ns}}}name", "Unknown")
            protection_level = perm.get(f"{{{android_ns}}}protectionLevel", "Not specified")
            results["permissions"].append({
                "name": perm_name,
                "protection_level": protection_level
            })

        # Find uses-permissions
        uses_permissions = root.findall("uses-permission")
        uses_permissions_sdk = root.findall("uses-permission-sdk-23")
        
        for perm in uses_permissions + uses_permissions_sdk:
            perm_name = perm.get(f"{{{android_ns}}}name", "Unknown")
            max_sdk_version = perm.get(f"{{{android_ns}}}maxSdkVersion", "Not specified")
            results["uses_permissions"].append({
                "name": perm_name,
                "max_sdk_version": max_sdk_version
            })

        return results
        
    except Exception as e:
        print(f" Error reading {manifest_path}: {e}")
        return None

def print_results(results, manifest_file):
    if not results:
        return
    
    print(f"\n{'='*80}")
    print(f"ANDROID MANIFEST ANALYSIS: {manifest_file}")
    print(f"{'='*80}")
    
    # Basic app info
    print(f"\n BASIC APP INFORMATION:")
    print(f"  Package Name: {results['package_name']}")
    print(f"  Version Code: {results['version_code']}")
    print(f"  Version Name: {results['version_name']}")
    
    # Security flags
    print(f"\n SECURITY FLAGS:")
    print(f"  Debuggable: {' YES (Security Risk)' if results['is_debuggable'] else ' No'}")
    print(f"  Backup Enabled: {' YES (Security Risk)' if results['is_backup_enabled'] else ' No'}")
    print(f"  Network Security Config: {' Yes' if results['has_network_security_config'] else ' No'}")
    if results['has_network_security_config']:
        print(f"    Config File: {results.get('network_security_config_file', 'Unknown')}")
    
    # Flutter detection
    print(f"\n FLUTTER DETECTION:")
    if results['flutter_embedding']:
        print(f"  Flutter App:  Yes (Embedding: {results['flutter_embedding']})")
    else:
        print(f"  Flutter App:  No")
    
    # Exported components
    print(f"\n EXPORTED COMPONENTS ({len(results['exported_components'])} found):")
    if results['exported_components']:
        for item in results['exported_components']:
            permission_info = f" (permission: {item['permission']})" if item['permission'] != "None" else ""
            print(f"  - <{item['tag']}>  name: {item['name']}{permission_info}")
    else:
        print("  No components with android:exported=\"true\" found")
    
    # Declared permissions
    print(f"\n DECLARED PERMISSIONS ({len(results['permissions'])} found):")
    if results['permissions']:
        for perm in results['permissions']:
            print(f"  - {perm['name']}")
            print(f"    Protection Level: {perm['protection_level']}")
    else:
        print("  No custom permissions declared")
    
    # Uses permissions
    print(f"\n REQUESTED PERMISSIONS ({len(results['uses_permissions'])} found):")
    if results['uses_permissions']:
        # Group by common permission categories
        dangerous_perms = []
        normal_perms = []
        other_perms = []
        
        dangerous_keywords = ['CAMERA', 'LOCATION', 'MICROPHONE', 'SMS', 'CONTACTS', 
                             'CALENDAR', 'STORAGE', 'PHONE', 'SENSORS']
        
        for perm in results['uses_permissions']:
            perm_name = perm['name']
            if any(keyword in perm_name for keyword in dangerous_keywords):
                dangerous_perms.append(perm)
            elif 'android.permission.' in perm_name:
                normal_perms.append(perm)
            else:
                other_perms.append(perm)
        
        if dangerous_perms:
            print("  DANGEROUS PERMISSIONS:")
            for perm in dangerous_perms:
                max_sdk = f" (maxSdk: {perm['max_sdk_version']})" if perm['max_sdk_version'] != "Not specified" else ""
                print(f"    - {perm['name']}{max_sdk}")
        
        if normal_perms:
            print("   NORMAL PERMISSIONS:")
            for perm in normal_perms[:10]:  # Show first 10 to avoid clutter
                print(f"    - {perm['name']}")
            if len(normal_perms) > 10:
                print(f"    ... and {len(normal_perms) - 10} more normal permissions")
        
        if other_perms:
            print("   OTHER PERMISSIONS:")
            for perm in other_perms:
                print(f"    - {perm['name']}")
    else:
        print("  No uses-permission tags found")

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
        print_results(results, manifest_file)
    else:
        print(f"\n Error analyzing {manifest_file}")