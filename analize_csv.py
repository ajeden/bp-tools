import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import subprocess
import sys
import os
import platform
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process and analyze merged CSV files.")
    parser.add_argument('-i', '--input', required=True, nargs='+', help='Input CSV file paths')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file path')
    parser.add_argument('--start-date', help='Minimum date (inclusive) in YYYY-MM-DD format')
    parser.add_argument('--end-date', help='Maximum date (inclusive) in YYYY-MM-DD format')
    return parser.parse_args()

def read_and_merge_files(file_paths,swap_cols=False):
    dfs = [pd.read_csv(file, parse_dates=[0]) for file in file_paths]
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.drop_duplicates(inplace=True)
    if swap_cols:
        cols = combined_df.columns.tolist()
        cols[1], cols[2] = cols[2], cols[1]
        combined_df = combined_df[cols]
    return combined_df

def filter_and_sort_data(df, datetime_col, start_date=None, end_date=None):
    if start_date:
        df = df[df[datetime_col] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df[datetime_col] <= pd.to_datetime(end_date)]
    df.sort_values(by=datetime_col, inplace=True)
    return df

def generate_statistics(df, int_cols, label):
    stats = df[int_cols].describe(percentiles=[0.25, 0.5, 0.75]).loc[['min', '25%', '50%', '75%', 'max']]
    stats.rename(index={'25%': 'q1', '50%': 'median', '75%': 'q3'}, inplace=True)
    stats = stats.T
    print(f"\n{Fore.GREEN + Style.BRIGHT}📊 Statistics for {label}:{Style.RESET_ALL}")
    print(Fore.CYAN + stats.to_string() + Style.RESET_ALL)

    return stats, stats.to_string()

def generate_plot(df, stats_all, stats_before, stats_after, datetime_col, int_cols, output_image):
    df['date_only'] = df[datetime_col].dt.date
    daily_avg = df.groupby('date_only')[int_cols].mean()

    # Fonts
    system = platform.system()

    if system == "Darwin":  # macOS
        plt.rcParams['font.family'] = ['Apple Color Emoji', 'DejaVu Sans', 'sans-serif']
    elif system == "Windows":
        plt.rcParams['font.family'] = ['Segoe UI Emoji', 'DejaVu Sans', 'sans-serif']
    elif system == "Linux":
        plt.rcParams['font.family'] = ['Noto Color Emoji', 'DejaVu Sans', 'sans-serif']
    else:
        plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']  # fallback

    print(f"✅ Font family set for emoji rendering on {system}")

    # Create figure layout
    fig = plt.figure(figsize=(28, 20))
    gs = gridspec.GridSpec(3, 2, height_ratios=[4.5, 1, 0.8])

    # Line plot
    ax1 = plt.subplot(gs[0,:])
    for idx, col in enumerate(int_cols):
        linestyle = ':' if idx == 2 else '-'
        ax1.plot(daily_avg.index, daily_avg[col], label=col, linestyle=linestyle)

    # Format x-axis: more ticks
    locator = mdates.AutoDateLocator(minticks=10, maxticks=40)  # tweak as needed
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))



    # Title and labels
    ax1.set_title("Daily Averages")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Average Value")
    ax1.legend()
    ax1.grid(True)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

    def add_table(ax, stats_df, title, labels_bg_color, scaleX=0.2):
        ax.axis('off')
        ax.text(0.5, 0.95,title, fontsize=14, 
                ha='center',va='bottom',
                transform=ax.transAxes, 
                weight='bold', clip_on=False)

        table = ax.table(cellText=stats_df.values.round(2),
                         rowLabels=stats_df.index,
                         colLabels=stats_df.columns,
                         cellLoc='center',
                         loc='center')
        table.scale(scaleX, 1.2)
        table.auto_set_font_size(False)
        table.set_fontsize(12)

        # Bold headers and row labels
        for (row, col), cell in table.get_celld().items():
            if row == 0 or col == -1:
                cell.set_text_props(weight='bold')
                cell.set_facecolor(labels_bg_color)  # Dark gray background
                cell.get_text().set_color("white")  # White text

    # Add all 3 summary tables
    ax2 = plt.subplot(gs[1,:])
    add_table(ax2, stats_all, "📊 Summary: All Rows","#444444" )

    ax3 = plt.subplot(gs[2,0])
    add_table(ax3, stats_before, "🌅 Summary: Before Midday","#009944",0.5)

    ax4 = plt.subplot(gs[2,1])
    add_table(ax4, stats_after, "🌇 Summary: After Midday","#004499",0.5)

    plt.tight_layout()
    plt.savefig(output_image)
    print(f"\n✅ Line graph with summaries saved as '{output_image}'")

def open_image(path):
    try:
        if sys.platform.startswith('darwin'):
            subprocess.run(['open', path])
        elif os.name == 'nt':
            os.startfile(path)
        elif os.name == 'posix':
            subprocess.run(['xdg-open', path])
    except Exception as e:
        print(f"Could not open image automatically: {e}")

def export_summaries_to_txt(output_path, summaries):
    txt_path = os.path.splitext(output_path)[0] + ".txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=== Summary Tables ===\n\n")
        f.write("📊 All Rows:\n" + summaries['all'] + "\n\n")
        f.write("🌅 Before Midday:\n" + summaries['before'] + "\n\n")
        f.write("🌇 After Midday:\n" + summaries['after'] + "\n")
    print(f"\n📝 Summaries exported to: {txt_path}")

def main():
    args = parse_arguments()

    df = read_and_merge_files(args.input,True)
    datetime_col = df.columns[0]
    int_cols = df.columns[1:4]

    df = filter_and_sort_data(df, datetime_col, args.start_date, args.end_date)

    df.to_csv(args.output, index=False)
    print(f"\n💾 Sorted and merged CSV saved as '{args.output}'")

    stats_all, stats_all_str = generate_statistics(df, int_cols, "all rows")
    stats_before, stats_before_str = generate_statistics(
        df[df[datetime_col].dt.time < pd.to_datetime("12:00").time()],
        int_cols,
        "rows before midday"
    )
    stats_after, stats_after_str = generate_statistics(
        df[df[datetime_col].dt.time >= pd.to_datetime("12:00").time()],
        int_cols,
        "rows after midday"
    )

    output_image = os.path.splitext(args.output)[0] + ".png"
    generate_plot(df, stats_all, stats_before, stats_after, datetime_col, int_cols, output_image)
    open_image(output_image)

    export_summaries_to_txt(args.output, {
        "all": stats_all_str,
        "before": stats_before_str,
        "after": stats_after_str
    })

if __name__ == "__main__":
    main()
