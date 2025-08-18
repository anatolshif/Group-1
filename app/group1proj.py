# apk unpacker.
import zipfile
import os
import sys

def unzip_apk(apk_path: str, output_dir: str):
    # Check if the APK file exists
    if not os.path.exists(apk_path):
        print(f"Error: The APK file '{apk_path}' does not exist.")
        sys.exit(1)

    print(f"Unzipping '{apk_path}'...")
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Use the with statement to automatically handle file closing
        with zipfile.ZipFile(apk_path, 'r') as zip_ref:
            # Extract all the contents to the specified directory
            zip_ref.extractall(output_dir)

        print(f"Success! Contents extracted to '{output_dir}'.")
        
    except zipfile.BadZipFile:
        print(f"Error: The file '{apk_path}' is not a valid ZIP file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Define the path to your APK file and the desired output directory
    # Note: Replace 'example.apk' and 'output_apk' with your actual file names
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Assume the APK is in the same directory as the script
    apk_file_name = 'example.apk'
    apk_file_path = os.path.join(script_dir, apk_file_name)
    
    # Define the name of the output directory
    output_directory = 'unzipped_apk_contents'
    
    # Call the function to unzip the file
    unzip_apk(apk_file_path, output_directory)
# a frida script loader.


