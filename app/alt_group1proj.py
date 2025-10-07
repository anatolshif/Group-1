import subprocess
import re
import xml.etree.ElementTree as ET


ADB = r"/Users/useer/AppData/Local/Android/Sdk/platform-tools/adb.exe"
JADX = "C:/Users/useer/Downloads/Security/jadx-1.5.1/bin/jadx.bat"
def fetchMultipleApps():
    #pm_list_packages = subprocess.run([ADB, "shell", "pm", "list", "packages", "-3", "-f"], text=True)
    pm_list_packages = subprocess.check_output([ADB, "shell", "pm", "list", "packages", "-3", "-f"], text=True)
    for package in (pm_list_packages.splitlines()):
        # package:/data/app/~~3yZz2YMGTSgaoNHr_k2fpw==/com.google.android.apps.photos--3_7vfJlMnNMgZMyEXVrvw==/base.apk=com.google.android.apps.photos
        match = re.match(r"package:(.*\.apk)=(.*)", package)
        apk_path = match.group(1)
        package_name = match.group(2)
        subprocess.run([ADB, "pull", apk_path, f"apks/{package_name}.apk"])
        # decompile apk with jadx
        subprocess.run([JADX, "-d", f"decompiled/{package_name}", f"apks/{package_name}.apk"])
        package_names= []
        package_names.append(package_name)

    return package_names



def fridaHook():
    # load script.js into frida
    output = subprocess.run(["frida", "-U", "-l", "script.js", "-F"])
    #print(output)
    

def NetAnalysis():
    subprocess.Popen([])

def StaticAnalysis():
    choice = input('input apk name and make sure it is found in folder called apks or input 1 to fetch(s) 3rd party apps from a connected device:')
    if (choice =='1'):
        packagenames = fetchMultipleApps()
        for i in packagenames:
            find_exported_true(packagenames[i])
    else:
        print(choice)
        match = re.match(r"(.*)(.*\.apk)", choice)
        apk_path = match.group(0)
        package_name = match.group(1)
        #print(apk_path)
        #print(package_name)
        #package_name = choice
        subprocess.run([JADX, "-d", f"decompiled/{package_name}", f"apks/{package_name}.apk"])
        print("finally here")
        manifest_path = f"C:/Users/useer/Documents/Group1Project/Group-1/app/decompiled/{package_name}/resources/AndroidManifest.xml"
        results = find_exported_true(manifest_path)

        if results:
            print(f"\n Found {len(results)} exported components in {package_name}:\n")
            for item in results:
                print(f"- <{item['tag']}>  name: {item['name']}")
        else:
            print(f"\n No components with android:exported=\"true\" found in {package_name}")



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

def logAnalysis():
    pass



if __name__ == "__main__":
    lin1 = "____________________Android App Security Scanner______________________\n"
    lin2 = "options:\n"
    lin3 = "1. Dynamic Instrumentation\n"
    lin4 = "2. Static Analysis\n"
    lin5 = "3. Network Interception\n"
    lin6 = "4. Log Capture\n"
    lin7 = "\n\n\nTo exit, press any other key."
    concat = lin1+lin2+lin3+lin4+lin5+lin6+lin7
    print(concat)
    choice = input("Enter choice:")
    if (choice =='1'):
        print("here")
        fridaHook()
        print("frida called")
    if (choice == '2'):
        StaticAnalysis()

    elif (choice != 1):
        print("Thanks for using this tool.")
