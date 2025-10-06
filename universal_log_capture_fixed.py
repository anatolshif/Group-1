# universal_log_capture_final.py 
import subprocess
import time
import os
import re
from datetime import datetime

# Your ADB path
ADB_PATH = r"C:\Users\micha\Downloads\platform-tools-latest-windows\platform-tools\adb.exe"

class LogCapture:
    def __init__(self):
        self.adb_path = ADB_PATH
        self.device_id = None
        self.device_info = {}
        
        # Verify ADB exists
        if not os.path.exists(self.adb_path):
            print(f"ADB not found at: {self.adb_path}")
            exit()
        else:
            print(f"ADB found: {self.adb_path}")
    
    def get_all_devices(self):
        """Get all connected Android devices"""
        try:
            result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True)
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if line.strip() and '\tdevice' in line:
                    devices.append(line.split('\t')[0])
            return devices
        except:
            return []
    
    def select_device(self):
        """Let user select which device to use"""
        devices = self.get_all_devices()
        if not devices:
            print("No Android devices connected!")
            return False
        
        if len(devices) == 1:
            self.device_id = devices[0]
            return True
        else:
            print(f"📱 Found {len(devices)} devices:")
            for i, device in enumerate(devices, 1):
                print(f"   {i}. {device}")
            try:
                choice = int(input(f"Select device (1-{len(devices)}): "))
                self.device_id = devices[choice-1]
                return True
            except:
                return False
    
    def get_device_info(self):
        """Get device information"""
        if not self.device_id:
            return {}
        
        info = {}
        commands = {
            'model': ["shell", "getprop", "ro.product.model"],
            'android_version': ["shell", "getprop", "ro.build.version.release"],
        }
        
        for key, command in commands.items():
            try:
                result = subprocess.run([self.adb_path, "-s", self.device_id] + command, 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info[key] = result.stdout.strip()
            except:
                info[key] = "Unknown"
        
        return info
    
    def get_installed_apps(self, count=30):
        """Get list of installed apps"""
        if not self.device_id:
            if not self.select_device():
                return []
        
        try:
            result = subprocess.run([self.adb_path, "-s", self.device_id, "shell", "pm", "list", "packages"],
                                  capture_output=True, text=True, timeout=15)
            
            packages = []
            for line in result.stdout.split('\n'):
                if line.startswith('package:'):
                    packages.append(line.replace('package:', '').strip())
            
            # Get app labels
            apps_with_labels = []
            print("📦 Getting app information...")
            
            for i, package in enumerate(packages[:count]):
                label_result = subprocess.run([self.adb_path, "-s", self.device_id, "shell", "pm", "dump", package],
                                            capture_output=True, text=True, timeout=5)
                
                app_label = package
                if label_result.returncode == 0:
                    for dump_line in label_result.stdout.split('\n'):
                        if "label=" in dump_line.lower():
                            match = re.search(r'label=(.+)', dump_line, re.IGNORECASE)
                            if match:
                                app_label = f"{match.group(1).strip()} ({package})"
                                break
                
                apps_with_labels.append((package, app_label))
                print(f"   🔍 {i+1}/{min(len(packages), count)}", end='\r')
            
            print(f"\n✅ Found {len(packages)} apps")
            return apps_with_labels
            
        except:
            return []
    
    def search_apps(self, search_term):
        """Search for apps by name or package"""
        all_apps = self.get_installed_apps(100)
        matching_apps = []
        search_lower = search_term.lower()
        
        for package, label in all_apps:
            if search_lower in package.lower() or search_lower in label.lower():
                matching_apps.append((package, label))
        
        return matching_apps
    
    def capture_app_logs(self, package_name, duration=60):
        """Capture logs for specific app"""
        if not self.device_id:
            if not self.select_device():
                return
        
        device_info = self.get_device_info()
        model = device_info.get('model', 'AndroidDevice')
        
        # Get app label
        app_label = package_name
        label_result = subprocess.run([self.adb_path, "-s", self.device_id, "shell", "pm", "dump", package_name],
                                    capture_output=True, text=True)
        if label_result.returncode == 0:
            for line in label_result.stdout.split('\n'):
                if "label=" in line.lower():
                    match = re.search(r'label=(.+)', line, re.IGNORECASE)
                    if match:
                        app_label = match.group(1).strip()
                        break
        
        # Ask for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in app_label if c.isalnum() or c in ('-', '_', ' '))[:30]
        default_filename = f"app_logs_{safe_name}_{timestamp}.txt"
        
        filename = input(f"Output filename [{default_filename}]: ").strip()
        if not filename:
            filename = default_filename
        
        print(f"\n🎯 Starting App Log Capture")
        print(f"   App: {app_label}")
        print(f"   Package: {package_name}")
        print(f"   Device: {model}")
        print(f"   Duration: {duration} seconds")
        print(f"   Output: {filename}")
        print("-" * 50)
        
        try:
            subprocess.run([self.adb_path, "-s", self.device_id, "logcat", "-c"])
            print("✅ Log buffer cleared")
            
            process = subprocess.Popen([self.adb_path, "-s", self.device_id, "logcat", "-v", "time"],
                                     stdout=subprocess.PIPE, text=True, bufsize=1)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"APP LOGS: {app_label}\n")
                f.write(f"Package: {package_name}\n")
                f.write(f"Device: {model}\n")
                f.write(f"Time: {datetime.now()}\n")
                f.write("=" * 40 + "\n\n")
            
            start_time = time.time()
            line_count = 0
            
            with open(filename, 'a', encoding='utf-8') as f:
                while (time.time() - start_time) < duration:
                    line = process.stdout.readline()
                    if line and package_name in line:
                        f.write(line)
                        line_count += 1
                        if line_count % 10 == 0:
                            elapsed = time.time() - start_time
                            remaining = duration - elapsed
                            print(f"   📊 {line_count} app lines | {remaining:.1f}s remaining")
            
            process.terminate()
            print(f"\n✅ App Capture Complete!")
            print(f"   📄 {line_count} lines → {filename}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def capture_device_logs(self, duration=60):
        """Capture general device logs"""
        if not self.device_id:
            if not self.select_device():
                return
        
        device_info = self.get_device_info()
        model = device_info.get('model', 'AndroidDevice')
        
        # Ask for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in model if c.isalnum() or c in ('-', '_', ' '))
        default_filename = f"device_logs_{safe_name}_{timestamp}.txt"
        
        filename = input(f"Output filename [{default_filename}]: ").strip()
        if not filename:
            filename = default_filename
        
        print(f"\n🎯 Starting Device Log Capture")
        print(f"   Device: {model}")
        print(f"   Duration: {duration} seconds")
        print(f"   Output: {filename}")
        print("-" * 50)
        
        try:
            subprocess.run([self.adb_path, "-s", self.device_id, "logcat", "-c"])
            print("✅ Log buffer cleared")
            
            process = subprocess.Popen([self.adb_path, "-s", self.device_id, "logcat", "-v", "time"],
                                     stdout=subprocess.PIPE, text=True, bufsize=1)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"DEVICE LOGS: {model}\n")
                f.write(f"Time: {datetime.now()}\n")
                f.write("=" * 40 + "\n\n")
            
            start_time = time.time()
            line_count = 0
            
            with open(filename, 'a', encoding='utf-8') as f:
                while (time.time() - start_time) < duration:
                    line = process.stdout.readline()
                    if line:
                        f.write(line)
                        line_count += 1
                        if line_count % 25 == 0:
                            elapsed = time.time() - start_time
                            remaining = duration - elapsed
                            print(f"   📊 {line_count} device lines | {remaining:.1f}s remaining")
            
            process.terminate()
            print(f"\n✅ Device Capture Complete!")
            print(f"   📄 {line_count} lines → {filename}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def real_time_monitor(self):
        """Real-time log monitor"""
        if not self.device_id:
            if not self.select_device():
                return
        
        device_info = self.get_device_info()
        model = device_info.get('model', 'AndroidDevice')
        
        print(f"\n👀 Real-time Monitor - {model}")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        try:
            subprocess.run([self.adb_path, "-s", self.device_id, "logcat", "-c"])
            process = subprocess.Popen([self.adb_path, "-s", self.device_id, "logcat", "-v", "time"],
                                     stdout=subprocess.PIPE, text=True, bufsize=1)
            
            line_count = 0
            while True:
                line = process.stdout.readline()
                if line:
                    line_count += 1
                    print(f"[{line_count}] {line.strip()}")
        
        except KeyboardInterrupt:
            print(f"\n⏹️  Monitoring stopped - {line_count} lines")
            if process:
                process.terminate()
        except Exception as e:
            print(f"❌ Monitor error: {e}")

def main():
    capture = LogCapture()
    
    print("=" * 70)
    print("           UNIVERSAL ANDROID LOG CAPTURE")
    print("=" * 70)
    
    while True:
        devices = capture.get_all_devices()
        print(f"\n📱 Connected devices: {len(devices)}")
        for device in devices:
            info = capture.get_device_info()
            print(f"   • {info.get('model', 'Unknown')} ({device})")
        
        print("\n" + "=" * 50)
        print("MAIN MENU - SIMPLE CHOICE")
        print("=" * 50)
        print("1. 📱 Capture SPECIFIC APP logs")
        print("2. 🔧 Capture GENERAL DEVICE logs")
        print("3. 🔍 Browse/Search Apps")
        print("4. 👀 Real-time Monitor")
        print("5. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n🎯 You selected: CAPTURE SPECIFIC APP LOGS")
            print("\n🔍 How do you want to select an app?")
            print("1. Enter package name manually")
            print("2. Browse installed apps")
            print("3. Search for apps")
            print("4. Go back to main menu")
            
            method = input("\nChoose method (1-4): ").strip()
            
            if method == "1":
                package = input("Enter app package name: ").strip()
                if package:
                    try:
                        duration = int(input("Duration in seconds [60]: ") or "60")
                        capture.capture_app_logs(package, duration)
                    except ValueError:
                        print("❌ Invalid duration")
                else:
                    print("❌ No package name provided")
            
            elif method == "2":
                apps = capture.get_installed_apps(30)
                if apps:
                    print(f"\n📦 Installed Apps (showing {len(apps)}):")
                    for i, (package, label) in enumerate(apps, 1):
                        print(f"   {i}. {label}")
                    
                    try:
                        app_choice = int(input(f"\nSelect app (1-{len(apps)}): "))
                        if 1 <= app_choice <= len(apps):
                            package, _ = apps[app_choice-1]
                            duration = int(input("Duration in seconds [60]: ") or "60")
                            capture.capture_app_logs(package, duration)
                        else:
                            print("❌ Invalid selection")
                    except ValueError:
                        print("❌ Invalid input")
                else:
                    print("❌ No apps found")
            
            elif method == "3":
                search = input("Enter app name or package to search for: ").strip()
                if search:
                    matching_apps = capture.search_apps(search)
                    if matching_apps:
                        print(f"\n🔍 Found {len(matching_apps)} matching apps:")
                        for i, (package, label) in enumerate(matching_apps, 1):
                            print(f"   {i}. {label}")
                        
                        try:
                            app_choice = int(input(f"\nSelect app (1-{len(matching_apps)}): "))
                            if 1 <= app_choice <= len(matching_apps):
                                package, _ = matching_apps[app_choice-1]
                                duration = int(input("Duration in seconds [60]: ") or "60")
                                capture.capture_app_logs(package, duration)
                            else:
                                print("❌ Invalid selection")
                        except ValueError:
                            print("❌ Invalid input")
                    else:
                        print("❌ No apps found matching your search")
                else:
                    print("❌ No search term provided")
            
            elif method == "4":
                continue
            else:
                print("❌ Invalid choice")
        
        elif choice == "2":
            print("\n🔧 You selected: CAPTURE GENERAL DEVICE LOGS")
            try:
                duration = int(input("Duration in seconds [60]: ") or "60")
                capture.capture_device_logs(duration)
            except ValueError:
                print("❌ Invalid duration")
        
        elif choice == "3":
            print("\n🔍 Browse/Search Apps")
            apps = capture.get_installed_apps(50)
            if apps:
                print(f"\n📦 All Installed Apps ({len(apps)}):")
                for i, (package, label) in enumerate(apps, 1):
                    print(f"   {i:2d}. {label}")
            else:
                print("❌ No apps found")
        
        elif choice == "4":
            print("\n👀 Real-time Monitor")
            capture.real_time_monitor()
        
        elif choice == "5":
            print("\n👋 Thank you for using Android Log Capture!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-5.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
