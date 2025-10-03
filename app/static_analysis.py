# app/static_analysis.py
import os
from zipfile import ZipFile
import xml.etree.ElementTree as ET

# Common dangerous permissions to flag
DANGEROUS_PERMS = [
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.READ_CONTACTS",
    "android.permission.ACCESS_FINE_LOCATION",
]

def analyze_apk(apk_path):
    findings = []
    metadata = {"apk": apk_path}

    if not os.path.exists(apk_path):
        return {"metadata": metadata, "findings": [{"type":"error","message":"APK not found"}]}

    try:
        with ZipFile(apk_path, 'r') as z:
            files = z.namelist()

            # detect Flutter
            if "assets/flutter_assets/" in "\n".join(files):
                findings.append({"type":"info","message":"Flutter assets detected"})

            if "AndroidManifest.xml" in files:
                manifest_data = z.read("AndroidManifest.xml")
                try:
                    root = ET.fromstring(manifest_data)
                    pkg = root.attrib.get("package", "unknown")
                    metadata["package"] = pkg
                    findings.append({"type":"info","message":f"Package: {pkg}"})

                    # scan for permissions
                    perms = [e.attrib.get("{http://schemas.android.com/apk/res/android}name") 
                             for e in root.findall("uses-permission")]
                    if perms:
                        findings.append({"type":"info","message":f"Permissions: {perms}"})
                        for p in perms:
                            if p in DANGEROUS_PERMS:
                                findings.append({"type":"warning","message":f"Dangerous permission: {p}"})

                    # check application tag attributes
                    app = root.find("application")
                    if app is not None:
                        if app.attrib.get("{http://schemas.android.com/apk/res/android}debuggable") == "true":
                            findings.append({"type":"warning","message":"App is debuggable"})
                        if app.attrib.get("{http://schemas.android.com/apk/res/android}usesCleartextTraffic") == "true":
                            findings.append({"type":"warning","message":"Cleartext traffic allowed"})

                except Exception as e:
                    findings.append({"type":"warning","message":f"Manifest parse failed: {e}"})
            else:
                findings.append({"type":"warning","message":"No AndroidManifest.xml found"})

    except Exception as e:
        findings.append({"type":"error","message":f"Failed to open APK: {e}"})

    return {"metadata": metadata, "findings": findings}
