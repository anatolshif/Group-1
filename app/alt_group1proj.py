import subprocess
import re

ADB = r"/Users/useer/AppData/Local/Android/Sdk/platform-tools/adb.exe"
JADX = "C:/Users/useer/Downloads/Security/jadx-1.5.1/bin/jadx.bat"
def fetchMultipleApps():
    #pm_list_packages = subprocess.run([ADB, "shell", "pm", "list", "packages", "-3", "-f"], text=True)

    pm_list_packages = subprocess.check_output([ADB, "shell", "pm", "list", "packages", "-f"], text=True)
    for package in (pm_list_packages.splitlines()):
        # package:/data/app/~~3yZz2YMGTSgaoNHr_k2fpw==/com.google.android.apps.photos--3_7vfJlMnNMgZMyEXVrvw==/base.apk=com.google.android.apps.photos
        match = re.match(r"package:(.*\.apk)=(.*)", package)
        apk_path = match.group(1)
        package_name = match.group(2)
        subprocess.run([ADB, "pull", apk_path, f"apks/{package_name}.apk"])
        # decompile apk with jadx
        subprocess.run([JADX, "-d", f"decompiled/{package_name}", f"apks/{package_name}.apk"])



def fridaHook():
    # load script.js into frida
    output = subprocess.run(["frida", "-U", "-l", "script.js", "-F"])
    #print(output)
    

def NetAnalysis():
    subprocess.Popen([])

def staticAnalysis():
    pass

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
    elif (choice != 1):
        print("Thanks for using this tool.")
