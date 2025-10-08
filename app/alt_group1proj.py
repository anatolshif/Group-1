import subprocess
import re
import xml.etree.ElementTree as ET
import find_exported

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
    lin2 = '''
    For network Analysis you can perform packet capture or setup MITM
    
    option 1)
    For packet capture, run this command as root in adb:
    emulator -tcpdump packets.cap -avd <device name>

    option 2)
    For MITM using Burpsuite, you need to install portswiggers cert as system cert since most apps only trust system certificates.
    this can be done by running the scripts provided in the scripts folder.
    '''
    print(lin2)
    result = subprocess.run([ADB, "shell", "getprop", "ro.build.version.release"], capture_output=True,text=True, check=True)
    android_version = int(result.stdout.strip())
    if (android_version>13):
        subprocess.run([ADB, "push", "/Users/useer/Documents/Group1Project/Group-1/app/scripts/Android14&above.sh", "/data/local/tmp/portswiggercertassystemcert.sh"])
    elif(android_version<=13):
        subprocess.run([ADB, "push", "/Users/useer/Documents/Group1Project/Group-1/app/scripts/belowAndroid14.sh", "/data/local/tmp/portswiggercertassystemcert.sh"])
    
    Lin3 = '''
    The neccessary script has been pushed into /data/local/tmp
    Now all you have to do is install portswigger certificate as user certificate and run the script.
    It will move it into System Certificates allowing you to Intercept network traffic.
    '''
    print(Lin3)
    
    #subprocess.Popen([ADB, "push", "/scripts/belowAndroid14.sh", "/data/local/tmp/belowAndroid14.sh"])

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
        results = find_exported.find_exported_true(manifest_path)
        find_exported.print_results(results, manifest_path)
        # if results:
        #     print(f"\n Found {len(results)} exported components in {package_name}:\n")
        #     for item in results:
        #         print(f"- <{item['tag']}>  name: {item['name']}")
        # else:
        #     print(f"\n No components with android:exported=\"true\" found in {package_name}")



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
    
    lin1 = r'''               
                       _            _     _ 
        /\            | |          (_)   | |     /\                                            
       /  \  ____   _ | | ____ ___  _  _ | |    /  \  ____  ____                               
      / /\ \|  _ \ / || |/ ___) _ \| |/ || |   / /\ \|  _ \|  _ \                              
     | |__| | | | ( (_| | |  | |_| | ( (_| |  | |__| | | | | | | |                             
     |______|_| |_|\____|_|   \___/|_|\____|  |______| ||_/| ||_/                              
                                                     |_|   |_|                                 
        _                           _                 _                                       
       | |                         (_)_              | |                                      
        \ \   ____ ____ _   _  ____ _| |_ _   _       \ \   ____ ____ ____  ____   ____  ____ 
         \ \ / _  ) ___) | | |/ ___) |  _) | | |       \ \ / ___) _  |  _ \|  _ \ / _  )/ ___)
     _____) | (/ ( (___| |_| | |   | | |_| |_| |   _____) | (__( ( | | | | | | | ( (/ /| |    
    (______/ \____)____)\____|_|   |_|\___)__  |  (______/ \____)_||_|_| |_|_| |_|\____)_|    
                                         (____/                                               
    '''
    lin2 = '''
    options:\n
    1. Dynamic Instrumentation\n
    2. Static Analysis\n
    3. Network Interception\n
    4. Log Capture\n
    \n\n\nTo exit, press any other key.'''
    
    print(lin1+lin2)
    choice = input("Enter choice:")
    if (choice =='1'):
        #print("here")
        fridaHook()
        #print("frida called")
    if (choice == '2'):
        StaticAnalysis()
    if (choice == '3'):
        NetAnalysis()

    elif (choice != 1):
        print("Thanks for using this tool.")
