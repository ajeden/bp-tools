import argparse
import subprocess
import shutil
import os
import configparser
import sys
from datetime import datetime

def validate_mac(mac):
    """Validate MAC address format"""
    if not mac:
        return False
    parts = mac.split(':')
    if len(parts) != 6:
        return False
    try:
        return all(0 <= int(part, 16) <= 255 for part in parts)
    except ValueError:
        return False

def get_mac_from_config(device_type):
    """Get MAC address and user from config file"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    template_path = os.path.join(os.path.dirname(__file__), 'config.ini.template')
    
    # If config.ini doesn't exist, create it from template
    if not os.path.exists(config_path):
        if os.path.exists(template_path):
            shutil.copy(template_path, config_path)
            print("\nCreated config.ini from template. Please edit the file with your device MAC addresses.")
            print("You can find the MAC addresses in Windows Settings > Bluetooth & devices > Device properties")
            sys.exit(1)
        else:
            print("Error: Neither config.ini nor config.ini.template found!")
            sys.exit(1)
    
    config.read(config_path)
    try:
        if device_type == "M7":
            mac = config['devices']['M7_mac']
            user = config['devices'].get('M7_user', 'user1')  # Default to user1 if not specified
            return mac, user
        elif device_type == "Evolv":
            mac = config['devices']['Evolv_mac']
            return mac, None
        else:
            return None, None
            
        # Check if MAC is still using template value
        if mac in ['YOUR-M7-MAC-HERE', 'YOUR-EVOLV-MAC-HERE']:
            print(f"\nError: {device_type} MAC address not configured.")
            print("Please edit config.ini with your device's MAC address.")
            print("You can find the MAC address in Windows Settings > Bluetooth & devices > Device properties")
            sys.exit(1)
            
    except (KeyError, configparser.NoSectionError):
        return None, None

def run_omblepy_and_rename(script_dir, script_name, model, mac, user, output_name):
    """Run external script and rename output"""
    if not validate_mac(mac):
        raise ValueError(f"Invalid MAC address format: {mac}. Format should be XX:XX:XX:XX:XX:XX")
    
    print(f"Running {script_name} for '{model}'...")
    subprocess.run(["python", "-m", "omblepy", "-d", model, "-m", mac, "--loggerDebug"], check=True, cwd=script_dir)
    
    # For M7 device, select which user file to use
    if model == "hem-7361t":
        source_file = f"user{user[-1]}.csv"  # user1.csv or user2.csv
    else:
        source_file = "user1.csv"  # Evolv only uses user1.csv
    
    # Rename output file
    shutil.move(os.path.join(script_dir, source_file), output_name)
    print(f"Saved as {output_name}")
    return output_name

def main():
    parser = argparse.ArgumentParser(description="Run external scripts and merge results.")
    parser.add_argument('platform', choices=["M7", "Evolv", "both", "none"], 
                      help="Choose platform to analyze: M7 or Evolv or both, none if you just want to take input files for analysis")
    parser.add_argument('--m7-mac', help="MAC address for M7 device (format: XX:XX:XX:XX:XX:XX)")
    parser.add_argument('--evolv-mac', help="MAC address for Evolv device (format: XX:XX:XX:XX:XX:XX)")
    parser.add_argument('-u', '--m7-user', '--M7-user', dest='m7_user', choices=["user1", "user2"], 
                      help="Select which user's data to use for M7 device (default: user1)")
    args = parser.parse_args()

    today_str = datetime.now().strftime("%Y-%m-%d")
    label = args.platform

    # Get MAC addresses and user from command line args or config file
    m7_mac, m7_user = get_mac_from_config("M7")
    evolv_mac, _ = get_mac_from_config("Evolv")
    
    # Override config values with command line arguments if provided
    if args.m7_mac:
        m7_mac = args.m7_mac
    if args.evolv_mac:
        evolv_mac = args.evolv_mac
    if args.m7_user:
        m7_user = args.m7_user

    outputfile1 = None
    outputfile2 = None

    try:
        if label == "M7":
            if not m7_mac:
                raise ValueError("M7 MAC address not provided. Use --m7-mac argument or set M7_mac in config.ini")
            outputfile1 = run_omblepy_and_rename("omblepy-main", "omblepy.py", "hem-7361t", m7_mac, m7_user, f"M7-{m7_user}-{today_str}.csv")
        
        elif label == "Evolv":
            if not evolv_mac:
                raise ValueError("Evolv MAC address not provided. Use --evolv-mac argument or set Evolv_mac in config.ini")
            outputfile2 = run_omblepy_and_rename("omblepy-main", "omblepy.py", "hem-7600t", evolv_mac, None, f"Evolv-1-{today_str}.csv")
        
        elif label == "both":
            if not m7_mac:
                raise ValueError("M7 MAC address not provided. Use --m7-mac argument or set M7_mac in config.ini")
            if not evolv_mac:
                raise ValueError("Evolv MAC address not provided. Use --evolv-mac argument or set Evolv_mac in config.ini")
            outputfile1 = run_omblepy_and_rename("omblepy-main", "omblepy.py", "hem-7361t", m7_mac, m7_user, f"M7-{m7_user}-{today_str}.csv")
            outputfile2 = run_omblepy_and_rename("omblepy-main", "omblepy.py", "hem-7600t", evolv_mac, None, f"Evolv-1-{today_str}.csv")
        
        elif label == "none":
            # For 'none' platform, we need to check if any of the input files exist
            outputfile1 = f"M7-{m7_user}-{today_str}.csv"
            outputfile2 = f"Evolv-1-{today_str}.csv"
            
            if not os.path.exists(outputfile1) and not os.path.exists(outputfile2):
                print("\nError: No input files found for 'none' platform.")
                print(f"Please ensure at least one of these files exists in the current directory:")
                print(f"- {outputfile1}")
                print(f"- {outputfile2}")
                sys.exit(1)

        # Output file for merged results
        merged_output = f"analiza-{today_str}.csv"

        # Prepare arguments for the analysis script
        analysis_args = ["python", "analise_csv.py", "-o", merged_output]
        
        # Add input files if they exist
        input_files = []
        if outputfile1 and os.path.exists(outputfile1):
            input_files.append(outputfile1)
        if outputfile2 and os.path.exists(outputfile2):
            input_files.append(outputfile2)
            
        if not input_files:
            print("\nError: No input files found for analysis.")
            sys.exit(1)
            
        # Add all input files at once
        analysis_args.extend(["-i"] + input_files)

        # Call the main processing script
        print("\nRunning main analysis...")
        subprocess.run(analysis_args, check=True)

        print(f"\nAnalysis complete. Results saved as '{merged_output}' and 'analiza-{today_str}.png'.")

    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo find your device's MAC address:")
        print("1. Enable Bluetooth on your device")
        print("2. Put the Omron device in pairing mode")
        print("3. Use Windows Settings > Bluetooth & devices to see available devices")
        print("4. The MAC address will be shown in the device properties")
        sys.exit(1)

if __name__ == "__main__":
    main()
