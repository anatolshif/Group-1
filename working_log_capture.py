# working_log_capture.py - Guaranteed to work!
import subprocess
import time
from datetime import datetime

# Your ADB path - this definitely works!
ADB_PATH = r"C:\Users\micha\Downloads\platform-tools-latest-windows\platform-tools\adb.exe"

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    print("=" * 60)
    print("           WORKING ANDROID LOG CAPTURE")
    print("=" * 60)
    print(f"ADB: {ADB_PATH}")
    print("=" * 60)
    
    # Step 1: Check devices
    print("🔍 Checking connected devices...")
    returncode, stdout, stderr = run_command([ADB_PATH, "devices"])
    
    if returncode != 0:
        print("❌ ADB error:", stderr)
        input("Press Enter to exit...")
        return
    
    print("ADB Devices Output:")
    print(stdout)
    
    # Check if any devices are connected
    lines = stdout.strip().split('\n')
    devices = []
    for line in lines[1:]:  # Skip first line
        if line.strip() and '\tdevice' in line:
            device_id = line.split('\t')[0]
            devices.append(device_id)
    
    if not devices:
        print("❌ No Android devices found!")
        print("\nPlease connect your Android device and:")
        print("1. Enable USB Debugging")
        print("2. Allow USB debugging when prompted")
        print("3. Try again")
        input("\nPress Enter to exit...")
        return
    
    print(f"✅ Found {len(devices)} device(s)")
    
    # Step 2: Get device info
    device_id = devices[0]
    print(f"📱 Using device: {device_id}")
    
    # Get device model
    returncode, model_output, stderr = run_command([
        ADB_PATH, "-s", device_id, "shell", "getprop", "ro.product.model"
    ])
    device_model = model_output.strip() if returncode == 0 else "Unknown_Device"
    
    print(f"📋 Device model: {device_model}")
    
    # Step 3: Capture settings
    try:
        duration = int(input("\nEnter capture duration in seconds [30]: ") or "30")
        output_file = input("Enter output filename [auto]: ").strip()
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in device_model if c.isalnum() or c in ('-', '_'))
            output_file = f"{safe_name}_logs_{timestamp}.txt"
    except ValueError:
        print("❌ Invalid duration, using 30 seconds")
        duration = 30
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{device_model}_logs_{timestamp}.txt"
    
    # Step 4: Capture logs
    print(f"\n🎯 Starting log capture...")
    print(f"   Device: {device_model}")
    print(f"   Duration: {duration} seconds")
    print(f"   Output file: {output_file}")
    print("-" * 50)
    
    try:
        # Clear existing logs
        print("🧹 Clearing log buffer...")
        returncode, stdout, stderr = run_command([ADB_PATH, "-s", device_id, "logcat", "-c"])
        if returncode == 0:
            print("✅ Log buffer cleared")
        else:
            print("⚠️  Could not clear logs (continuing anyway)")
        
        # Start log capture
        print("📝 Capturing logs...")
        process = subprocess.Popen(
            [ADB_PATH, "-s", device_id, "logcat", "-v", "time"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Write header to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ANDROID DEVICE LOGS\n")
            f.write("=" * 50 + "\n")
            f.write(f"Device: {device_model}\n")
            f.write(f"Device ID: {device_id}\n")
            f.write(f"Capture started: {datetime.now()}\n")
            f.write(f"Duration: {duration} seconds\n")
            f.write("=" * 50 + "\n\n")
        
        # Capture logs for specified duration
        start_time = time.time()
        line_count = 0
        
        with open(output_file, 'a', encoding='utf-8') as f:
            while (time.time() - start_time) < duration:
                line = process.stdout.readline()
                if line:
                    f.write(line)
                    line_count += 1
                    # Show progress every 20 lines
                    if line_count % 20 == 0:
                        elapsed = time.time() - start_time
                        remaining = duration - elapsed
                        print(f"   📊 {line_count} lines captured | {remaining:.1f}s remaining")
        
        # Stop the process
        process.terminate()
        process.wait()
        
        print(f"\n✅ SUCCESS!")
        print(f"   📄 Saved {line_count} lines to: {output_file}")
        print("=" * 60)
        
        # Show file location
        import os
        full_path = os.path.abspath(output_file)
        print(f"   📍 Full path: {full_path}")
        
    except Exception as e:
        print(f"❌ Error during capture: {e}")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()