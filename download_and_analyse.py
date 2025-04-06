import argparse
import subprocess
import shutil
import os
from datetime import datetime

def run_omblepy_and_rename(script_dir,script_name, model, mac, output_name):
    # Run external script
    print(f"Running {script_name} for '{model}'...")
    subprocess.run(["python", script_name, "-d", model, "-m", mac, "--loggerDebug"], check=True, cwd=script_dir)
    
    # Rename output file
    shutil.move(script_dir+"/"+"user1.csv", output_name)
    print(f"Saved as {output_name}")
    return output_name

def main():
    parser = argparse.ArgumentParser(description="Run external scripts and merge results.")
    parser.add_argument('platform', choices=["M7", "Evolv", "both","none"], help="Choose platform to analyze: M7 or Evolv or both,\nnone if you just want to take input files for analysis")
    args = parser.parse_args()

    today_str = datetime.now().strftime("%Y-%m-%d")
    label = args.platform
    output_base = f"{label}-1-{today_str}.csv"

    # Run external scripts with specific model per platform
    if label == "M7":
        script1 = run_omblepy_and_rename("omblepy-main", "omblepy.py", "hem-7361t", "YOUR-MAC1-HERE", f"M7-1-{today_str}.csv")
    elif label == "Evolv":
        script2 = run_omblepy_and_rename("omblepy-main", "omblepy.py", "hem-7600t", "YOUR-MAC2-HERE", f"Evolv-1-{today_str}.csv")
    elif label == "both":
        script1 = run_omblepy_and_rename("omblepy-main", "omblepy.py", "hem-7361t", "YOUR-MAC1-HERE", f"M7-1-{today_str}.csv")
        script2 = run_omblepy_and_rename("omblepy-main", "omblepy.py", "hem-7600t", "YOUR-MAC2-HERE", f"Evolv-1-{today_str}.csv")
    elif label == "none":
        script1 = f"M7-1-{today_str}.csv"
        script2 = f"Evolv-1-{today_str}.csv"

    # Output file for merged results
    merged_output = f"analiza-{today_str}.csv"

    # Call the main processing script
    print("\nRunning main analysis...")
    subprocess.run([
        "python", "analizuj.py",
        "-i", script1, script2,
        "-o", merged_output
    ], check=True)

    print(f"\nAnalysis complete. Results saved as '{merged_output}' and 'analiza-{today_str}.png'.")

if __name__ == "__main__":
    main()
