# universal_log_capture_fixed.py - Works with ANY Android device
import subprocess
import time
import os
from datetime import datetime

# Your specific ADB path that we know works
ADB_PATH = r"C:\Users\micha\Downloads\platform-tools-latest-windows\platform-tools\adb.exe"

class UniversalLogCapture:
    def __init__(self):
        self.adb_path = ADB_PATH
        self.device_id = None
        self.device_info = {}
        
        # Verify ADB exists
        if not os.path.exists(self.adb_path):
            print(f"❌ ADB not found at: {self.adb_path}")
            print("Please check the ADB path and try again.")
            exit()
        else:
            print(f"✅ ADB found: {self.adb_path}")
    
    def get_all_devices(self):
        """Get all connected Android devices"""
        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if line.strip() and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            
            return devices
        except Exception as e:
            print(f"❌ Error getting devices: {e}")
            return []
    
    def select_device(self):
        """Let user select which device to use"""
        devices = self.get_all_devices()
        
        if not devices:
            print("❌ No Android devices connected!")
            print("\nPlease connect an Android device and:")
            print("1. Enable USB Debugging in Developer Options")
            print("2. Allow USB debugging when prompted")
            return False
        
        print(f"\n📱 Found {len(devices)} device(s):")
        for i, device_id in enumerate(devices, 1):
            info = self.get_device_info(device_id)
            print(f"   {i}. {info.get('model', 'Unknown')} ({device_id})")
        
        if len(devices) == 1:
            self.device_id = devices[0]
            print(f"✅ Auto-selected: {self.device_id}")
        else:
            try:
                choice = int(input(f"\nSelect device (1-{len(devices)}): "))
                if 1 <= choice <= len(devices):
                    self.device_id = devices[choice-1]
                else:
                    print("❌ Invalid selection")
                    return False
            except ValueError:
                print("❌ Invalid input")
                return False
        
        # Get device info for selected device
        self.device_info = self.get_device_info(self.device_id)
        return True
    
    def get_device_info(self, device_id):
        """Get detailed information about a device"""
        info = {
            'id': device_id,
            'model': 'Unknown',
            'android_version': 'Unknown',
            'manufacturer': 'Unknown',
            'brand': 'Unknown',
            'device': 'Unknown'
        }
        
        commands = {
            'model': ["-s", device_id, "shell", "getprop", "ro.product.model"],
            'android_version': ["-s", device_id, "shell", "getprop", "ro.build.version.release"],
            'manufacturer': ["-s", device_id, "shell", "getprop", "ro.product.manufacturer"],
            'brand': ["-s", device_id, "shell", "getprop", "ro.product.brand"],
            'device': ["-s", device_id, "shell", "getprop", "ro.product.device"],
        }
        
        for key, command in commands.items():
            try:
                result = subprocess.run(
                    [self.adb_path] + command,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    info[key] = result.stdout.strip()
            except:
                pass
        
        return info
    
    def display_device_info(self):
        """Display information about the current device"""
        if not self.device_info:
            return
        
        print(f"\n📋 Device Information:")
        print(f"   Model: {self.device_info.get('model', 'Unknown')}")
        print(f"   Android: {self.device_info.get('android_version', 'Unknown')}")
        print(f"   Manufacturer: {self.device_info.get('manufacturer', 'Unknown')}")
        print(f"   Brand: {self.device_info.get('brand', 'Unknown')}")
        print(f"   Device ID: {self.device_id}")
    
    def capture_logs_basic(self, duration=60, output_file=None):
        """Basic log capture for any device"""
        if not self.device_id:
            if not self.select_device():
                return None
        
        model = self.device_info.get('model', 'AndroidDevice')
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in model if c.isalnum() or c in ('-', '_', ' '))
            output_file = f"logs_{safe_name}_{timestamp}.txt"
        
        print(f"\n🎯 Starting Basic Log Capture")
        print(f"   Device: {model}")
        print(f"   Duration: {duration} seconds")
        print(f"   Output: {output_file}")
        print("-" * 50)
        
        try:
            # Clear logs
            subprocess.run([self.adb_path, "-s", self.device_id, "logcat", "-c"])
            print("✅ Log buffer cleared")
            
            # Start capture
            process = subprocess.Popen(
                [self.adb_path, "-s", self.device_id, "logcat", "-v", "time"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Write header
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("ANDROID DEVICE LOGS - UNIVERSAL CAPTURE\n")
                f.write("=" * 60 + "\n")
                f.write(f"Model: {self.device_info.get('model', 'Unknown')}\n")
                f.write(f"Android: {self.device_info.get('android_version', 'Unknown')}\n")
                f.write(f"Manufacturer: {self.device_info.get('manufacturer', 'Unknown')}\n")
                f.write(f"Brand: {self.device_info.get('brand', 'Unknown')}\n")
                f.write(f"Device ID: {self.device_id}\n")
                f.write(f"Capture started: {datetime.now()}\n")
                f.write(f"Duration: {duration} seconds\n")
                f.write("=" * 60 + "\n\n")
            
            # Capture logs
            start_time = time.time()
            line_count = 0
            
            with open(output_file, 'a', encoding='utf-8') as f:
                while (time.time() - start_time) < duration:
                    line = process.stdout.readline()
                    if line:
                        f.write(line)
                        line_count += 1
                        if line_count % 25 == 0:
                            elapsed = time.time() - start_time
                            remaining = duration - elapsed
                            print(f"   📊 {line_count} lines | {remaining:.1f}s remaining")
            
            process.terminate()
            
            print(f"\n✅ Basic Capture Complete!")
            print(f"   📄 {line_count} lines saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def capture_logs_advanced(self, duration=60, log_level="V", include_filters=None, exclude_filters=None):
        """Advanced log capture with filtering for any device"""
        if not self.device_id:
            if not self.select_device():
                return None
        
        model = self.device_info.get('model', 'AndroidDevice')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in model if c.isalnum() or c in ('-', '_', ' '))
        output_file = f"advanced_logs_{safe_name}_{timestamp}.txt"
        
        print(f"\n🎯 Starting Advanced Log Capture")
        print(f"   Device: {model}")
        print(f"   Duration: {duration} seconds")
        print(f"   Log Level: {log_level}")
        print(f"   Output: {output_file}")
        if include_filters:
            print(f"   Include: {', '.join(include_filters)}")
        if exclude_filters:
            print(f"   Exclude: {', '.join(exclude_filters)}")
        print("-" * 50)
        
        try:
            # Clear logs
            subprocess.run([self.adb_path, "-s", self.device_id, "logcat", "-c"])
            
            # Start capture with log level
            process = subprocess.Popen(
                [self.adb_path, "-s", self.device_id, "logcat", "-v", "time", f"*:{log_level}"],
                stdout=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Write header
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("ADVANCED ANDROID DEVICE LOGS\n")
                f.write("=" * 60 + "\n")
                f.write(f"Device: {model}\n")
                f.write(f"Manufacturer: {self.device_info.get('manufacturer', 'Unknown')}\n")
                f.write(f"Android: {self.device_info.get('android_version', 'Unknown')}\n")
                f.write(f"Log Level: {log_level}\n")
                if include_filters:
                    f.write(f"Include Filters: {', '.join(include_filters)}\n")
                if exclude_filters:
                    f.write(f"Exclude Filters: {', '.join(exclude_filters)}\n")
                f.write(f"Capture started: {datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
            
            # Capture with filtering
            start_time = time.time()
            line_count = 0
            
            with open(output_file, 'a', encoding='utf-8') as f:
                while (time.time() - start_time) < duration:
                    line = process.stdout.readline()
                    if line:
                        # Apply filters
                        should_write = True
                        
                        if include_filters and not any(filter_text in line for filter_text in include_filters):
                            should_write = False
                        
                        if exclude_filters and any(filter_text in line for filter_text in exclude_filters):
                            should_write = False
                        
                        if should_write:
                            f.write(line)
                            line_count += 1
                            if line_count % 20 == 0:
                                elapsed = time.time() - start_time
                                print(f"   📊 {line_count} filtered lines | {elapsed:.1f}s elapsed")
            
            process.terminate()
            
            print(f"\n✅ Advanced Capture Complete!")
            print(f"   📄 {line_count} filtered lines saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def real_time_monitor(self, duration=0):
        """Real-time log monitoring for any device"""
        if not self.device_id:
            if not self.select_device():
                return
        
        model = self.device_info.get('model', 'AndroidDevice')
        
        print(f"\n👀 Real-time Log Monitor - {model}")
        print("   Press Ctrl+C to stop anytime")
        print("-" * 50)
        
        try:
            # Clear and start monitoring
            subprocess.run([self.adb_path, "-s", self.device_id, "logcat", "-c"])
            
            process = subprocess.Popen(
                [self.adb_path, "-s", self.device_id, "logcat", "-v", "time"],
                stdout=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            line_count = 0
            start_time = time.time()
            
            while True:
                line = process.stdout.readline()
                if line:
                    line_count += 1
                    print(f"[{line_count}] {line.strip()}")
                
                # Stop if duration specified and time elapsed
                if duration > 0 and (time.time() - start_time) >= duration:
                    break
            
            process.terminate()
            print(f"\n⏹️  Monitoring stopped after {line_count} lines")
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Monitoring stopped by user after {line_count} lines")
            if process:
                process.terminate()
        except Exception as e:
            print(f"❌ Monitor error: {e}")
    
    def quick_capture_presets(self):
        """Quick capture with preset configurations"""
        presets = {
            "1": {"name": "Quick 30s", "duration": 30, "level": "V"},
            "2": {"name": "Errors Only", "duration": 120, "level": "E"},
            "3": {"name": "Warnings+", "duration": 180, "level": "W"},
            "4": {"name": "Security Focus", "duration": 300, "level": "V", "include": ["Security", "Permission", "Auth"]},
            "5": {"name": "Clean Logs", "duration": 240, "level": "V", "exclude": ["dalvikvm", "SystemServer"]}
        }
        
        print("\n🚀 Quick Capture Presets:")
        for key, preset in presets.items():
            print(f"   {key}. {preset['name']} - {preset['duration']}s - Level: {preset['level']}")
        
        choice = input("\nChoose preset (1-5): ").strip()
        
        if choice in presets:
            preset = presets[choice]
            if "include" in preset or "exclude" in preset:
                self.capture_logs_advanced(
                    duration=preset["duration"],
                    log_level=preset["level"],
                    include_filters=preset.get("include"),
                    exclude_filters=preset.get("exclude")
                )
            else:
                self.capture_logs_basic(
                    duration=preset["duration"],
                    output_file=f"preset_{preset['name'].replace(' ', '_').lower()}_{datetime.now().strftime('%H%M%S')}.txt"
                )

def main():
    capture = UniversalLogCapture()
    
    print("=" * 70)
    print("       UNIVERSAL ANDROID LOG CAPTURE - ALL DEVICES")
    print("=" * 70)
    print("Works with: Samsung, Google Pixel, OnePlus, Xiaomi, ZTE,")
    print("Huawei, Sony, Motorola, LG, and ANY Android device!")
    print("=" * 70)
    
    while True:
        # Show current device status
        devices = capture.get_all_devices()
        print(f"\n📱 Connected devices: {len(devices)}")
        for device in devices:
            info = capture.get_device_info(device)
            print(f"   • {info.get('model', 'Unknown')} ({device})")
        
        print("\n" + "=" * 50)
        print("MAIN MENU - UNIVERSAL")
        print("=" * 50)
        print("1. Basic Log Capture (Select Device)")
        print("2. Advanced Log Capture (With Filtering)")
        print("3. Real-time Log Monitor")
        print("4. Quick Capture Presets")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == "1":
            try:
                duration = int(input("Duration in seconds [60]: ") or "60")
                filename = input("Output filename [auto]: ") or None
                capture.capture_logs_basic(duration, filename)
            except ValueError:
                print("❌ Invalid duration")
        
        elif choice == "2":
            try:
                duration = int(input("Duration [60]: ") or "60")
                level = input("Log level (V/D/I/W/E) [V]: ") or "V"
                
                include = input("Include keywords (comma-separated, optional): ").strip()
                include_filters = [f.strip() for f in include.split(',')] if include else None
                
                exclude = input("Exclude keywords (comma-separated, optional): ").strip()
                exclude_filters = [f.strip() for f in exclude.split(',')] if exclude else None
                
                capture.capture_logs_advanced(duration, level, include_filters, exclude_filters)
            except ValueError:
                print("❌ Invalid input")
        
        elif choice == "3":
            try:
                duration = input("Monitor duration in seconds (0 for unlimited) [0]: ").strip()
                duration = int(duration) if duration else 0
                capture.real_time_monitor(duration)
            except ValueError:
                print("❌ Invalid duration")
        
        elif choice == "4":
            capture.quick_capture_presets()
        
        elif choice == "5":
            print("👋 Thank you for using Universal Android Log Capture!")
            break
        
        else:
            print("❌ Invalid choice")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()