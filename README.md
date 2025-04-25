# 📊  bp-tools CSV Analyzer: Time-Series Summary & Visualization

## ✅ What This Script Does

This Python script processes and visualizes time-series CSV data. It includes the following features:

- 📥 **Accepts multiple input CSV files**
  - Merges them into a single dataset
  - Removes duplicates automatically

- 📅 **Filters data by date range**
  - Optional `--start-date` and `--end-date` arguments
  - Dates in format: `YYYY-MM-DD`

- 🔃 **Sorts and prepares time-series data**
  - First column must be `datetime`
  - Next 3 columns should be numeric (e.g. temperature, pressure, etc.)

- 📊 **Generates summary statistics**
  - Full dataset
  - Rows **before midday**
  - Rows **after midday**

- 📈 **Creates a PNG chart**
  - Line plot of daily averages (3 series)
  - Includes 3 summary tables directly in the plot

- 🖥️ **Prints summaries in the terminal**
  - Colored, nicely formatted output using `colorama`

- 📄 **Exports a textual report**
  - Saves a `.txt` file with all 3 summary tables
  - Saves a `.xslx` file with all data and plot


# Usage
```bash
analize_csv.py [-h] -i INPUT [INPUT ...] -o OUTPUT [--start-date START_DATE] [--end-date END_DATE]
```
where:

`-h` is quick help

`-i INPUT` is a list of CSV files to process

`-o OUTPUT` is a filename to be outputted:
- CSV with sorted, deduplicated rows 
- PNG plot and summary
- TXT summaries
- XSLX Excel file with all above

optionally:

`--start-date` and `--end-date` to filter date range

## Expected input file format
Expected input is as created by default by [Omblepy](https://github.com/userx14/omblepy), namely:
```csv
datetime,dia,sys,bpm,mov,ihb
2025-03-30 08:41:10,80,120,70,0,0
```

## 🧩 Output Files

- `merged_output.csv` – Cleaned, merged CSV
- `merged_output.png` – Plot with line graph and 3 summary tables
- `merged_output.txt` – Text-based version of all 3 summaries


## 🚀 Example Usage

```bash
python analyze_csv.py -i input1.csv input2.csv -o merged_output.csv --start-date 2024-01-01 --end-date 2024-12-31
```

## Required Python libs
Install the following libraries:
```bash
pip install pandas matplotlib colorama xlsxwriter
```

# Extra script `download_and_analyze.py`
This is quick and dirty script to download data from my devices and run the analysis.
The script `download_and_analyze.py` relays on having [Omblepy](https://github.com/userx14/omblepy) handy with Omron devices already paired with your computer. See Omblepy's readme for details on how to do that.

# BP Tools

A set of tools for downloading and analyzing blood pressure data from Omron devices.

## Features

- Download data from Omron M7 and Evolv blood pressure monitors
- Support for multiple users on M7 device (user1 and user2)
- Generate comprehensive analysis including:
  - CSV files with merged data
  - PNG files with graphs
  - Excel files with tables and charts
  - TXT files with statistical summaries

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bp-tools.git
cd bp-tools
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Clone the omblepy repository:
```bash
git clone https://github.com/userx14/omblepy.git omblepy-main
```
so it is cloned to omblepy-main subdirectory.

4. Configure your devices:
   - Copy `config.ini.template` to `config.ini`
   - Edit `config.ini` with your device MAC addresses
   - For M7 device, you can specify the user (user1 or user2)

## Usage

### Download and Analyze Data

To download data from devices and analyze:

```bash
# For M7 device (default user1)
python download_and_analyse.py M7

# For M7 device with specific user
python download_and_analyse.py M7 --m7-user user2

# For Evolv device
python download_and_analyse.py Evolv

# For both devices
python download_and_analyse.py both

# For both devices with specific M7 user
python download_and_analyse.py both --m7-user user2
```

### Analyze Existing Data

To analyze existing CSV files without downloading new data:

```bash
python download_and_analyse.py none
```

### Command Line Arguments

- `platform`: Choose platform to analyze (M7, Evolv, both, none)
- `--m7-mac`: MAC address for M7 device (format: XX:XX:XX:XX:XX:XX)
- `--evolv-mac`: MAC address for Evolv device (format: XX:XX:XX:XX:XX:XX)
- `--m7-user`: User selection for M7 device (user1 or user2)

## Configuration

Edit `config.ini` to set your device MAC addresses and M7 user preference:

```ini
[devices]
# M7 device MAC address (format: XX:XX:XX:XX:XX:XX)
M7_mac = YOUR-M7-MAC-HERE
# M7 user selection (user1 or user2)
M7_user = user1

# Evolv device MAC address (format: XX:XX:XX:XX:XX:XX)
Evolv_mac = YOUR-EVOLV-MAC-HERE
```

## Finding Device MAC Addresses

1. Enable Bluetooth on your device
2. Put the Omron device in pairing mode
3. Use Windows Settings > Bluetooth & devices to see available devices
4. The MAC address will be shown in the device properties

You can also find your device MAC addresses through omblepy, see "Pairing for Universal Blood Pressure Manager (UBPM)" in Omblepy README file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.






