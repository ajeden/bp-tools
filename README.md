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






