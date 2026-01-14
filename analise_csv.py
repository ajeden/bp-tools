import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import xlsxwriter
import subprocess
import sys
import os
import platform
import json
from datetime import date, datetime, timedelta
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# === i18n Configuration ===
DEFAULT_LANG = 'pl'
CURRENT_LANG = DEFAULT_LANG
TRANSLATIONS = {}

def load_translations(lang):
    """Load translations from external file analise_csv.<lang>"""
    global TRANSLATIONS
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, f"analise_csv.lang-{lang}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            TRANSLATIONS = json.load(f)
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Translation file not found: {file_path}{Style.RESET_ALL}")
        # Try fallback
        if lang != 'en':
             fallback_path = os.path.join(script_dir, "analise_csv.en")
             try:
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    TRANSLATIONS = json.load(f)
             except Exception:
                 sys.exit(1)
        else:
             sys.exit(1)
    except json.JSONDecodeError:
        sys.exit(1)

def t(key, **kwargs):
    """Retrieve translated string."""
    msg = TRANSLATIONS.get(key, key)
    try:
        return msg.format(**kwargs)
    except KeyError:
        return msg 

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process and analyze merged CSV files.")
    parser.add_argument('-i', '--input', required=True, nargs='+', help='Input CSV file paths')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file path')
    parser.add_argument('--start-date', help='Minimum date (inclusive) in YYYY-MM-DD format')
    parser.add_argument('--end-date', help='Maximum date (inclusive) in YYYY-MM-DD format')
    parser.add_argument('--lang', default='pl', help='Language code for output (default: pl)')
    return parser.parse_args()

def read_and_merge_files(file_paths, swap_cols=False):
    dfs = []
    for file in file_paths:
        try:
            df = pd.read_csv(file)
            if df.shape[1] < 4:
                continue
            datetime_col = df.columns[0]
            df[datetime_col] = pd.to_datetime(df[datetime_col], errors='coerce')
            for col in df.columns[1:4]:
                df[col] = pd.to_numeric(df[col], errors='coerce', downcast='integer')
            df.dropna(subset=[df.columns[0], df.columns[1], df.columns[2], df.columns[3]], inplace=True)
            dfs.append(df)
        except Exception as e:
            print(t('error_reading', file=file, e=e))

    if not dfs:
        print(t('no_valid_data'))
        sys.exit(1)

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.drop_duplicates(inplace=True)

    if swap_cols and combined_df.shape[1] >= 3:
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
    # Stats as Rows, Metrics as Columns
    stats = df[int_cols].describe(percentiles=[0.25, 0.5, 0.75]).loc[['min', '25%', '50%', '75%', 'max']]
    
    stats.rename(index={
        'min': t('stat_min'),
        '25%': t('stat_q1'),
        '50%': t('stat_median'),
        '75%': t('stat_q3'),
        'max': t('stat_max')
    }, inplace=True)
    
    stats = stats.T 
    
    print(f"\n{Fore.GREEN + Style.BRIGHT}{t('stats_for', label=label)}{Style.RESET_ALL}")
    print(Fore.CYAN + stats.to_string() + Style.RESET_ALL)

    return stats, stats.to_string()

def generate_plot(df, stats_all, stats_morning, stats_midday, stats_evening, datetime_col, int_cols, output_image):
    # Prepare data for plotting (Daily Averages)
    df['date_only'] = df[datetime_col].dt.date
    daily_avg = df.groupby('date_only')[int_cols].mean()
    
    # Filter daily avg for periods if possible? 
    # Actually, for the daily charts (Morn/Mid/Eve), we should ideally plot the *period* averages, not just total daily.
    # But for now, to keep it simple and robust, let's plot:
    # 1. Overall Chart (All data points or daily avg of all) -> chart_all
    # 2. Daily Chart for Morning -> Filter DF for morn -> groupby date -> plot
    # 3. Daily Chart for Midday -> Filter DF for mid -> groupby date -> plot
    # 4. Daily Chart for Evening -> Filter DF for eve -> groupby date -> plot
    
    def get_period_daily_avg(hour_min, hour_max):
        # hour_max is exclusive, unless it's 24
        if hour_max == 24:
             subset = df[df[datetime_col].dt.hour >= hour_min].copy()
        else:
             subset = df[(df[datetime_col].dt.hour >= hour_min) & (df[datetime_col].dt.hour < hour_max)].copy()
        
        if subset.empty:
            return pd.DataFrame(columns=int_cols)
            
        subset['date_only'] = subset[datetime_col].dt.date
        return subset.groupby('date_only')[int_cols].mean()

    # Data Source for Charts
    data_all = daily_avg # Overall Daily Average
    data_morn = get_period_daily_avg(0, 10)
    data_mid = get_period_daily_avg(10, 16)
    data_eve = get_period_daily_avg(16, 24)

    system = platform.system()
    plt.rcParams['font.family'] = ['Segoe UI Emoji', 'DejaVu Sans', 'sans-serif'] if system == "Windows" else ['DejaVu Sans']

    # Layout: 4 Rows x 2 Cols
    # Col 0: Summary Table (Width 1)
    # Col 1: Chart (Width 3)
    fig = plt.figure(figsize=(24, 24))
    gs = gridspec.GridSpec(4, 2, width_ratios=[1, 3], height_ratios=[1, 1, 1, 1])

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # Sys, Dia, Pulse

    def draw_chart(ax, data, title):
        if data.empty:
            ax.text(0.5, 0.5, t('warning_chart_data'), ha='center', va='center')
            return

        for idx, col in enumerate(int_cols):
            linestyle = '-'
            marker = 'o'
            if idx == 2: linestyle = ':' # Pulse
            ax.plot(data.index, data[col], label=col, linestyle=linestyle, marker=marker, color=colors[idx])

        locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

        ax.set_title(title, fontsize=12, weight='bold')
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)
        if ax.get_subplotspec().is_first_row():
             ax.legend(loc='upper right')

    def draw_table(ax, stats_df, title, header_color):
        ax.axis('off')
        ax.text(0.5, 1.0, title, fontsize=11, ha='center', va='bottom', transform=ax.transAxes, weight='bold')
        
        table_data = stats_df.map(lambda x: round(x, 1) if isinstance(x, (int, float)) else x)
        table = ax.table(cellText=table_data.values, 
                         rowLabels=table_data.index, 
                         colLabels=table_data.columns, 
                         cellLoc='center', 
                         loc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.3)
        
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor(header_color)
            elif col == -1: 
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#f0f0f0')

    # Row 0: All
    ax_t0 = plt.subplot(gs[0, 0]); draw_table(ax_t0, stats_all, t('summary_header_all'), "#444444")
    ax_c0 = plt.subplot(gs[0, 1]); draw_chart(ax_c0, data_all, t('chart_title'))

    # Row 1: Morning
    ax_t1 = plt.subplot(gs[1, 0]); draw_table(ax_t1, stats_morning, t('summary_header_morning'), "#2ca02c")
    ax_c1 = plt.subplot(gs[1, 1]); draw_chart(ax_c1, data_morn, t('chart_title_morning'))

    # Row 2: Midday
    ax_t2 = plt.subplot(gs[2, 0]); draw_table(ax_t2, stats_midday, t('summary_header_midday'), "#ff7f0e")
    ax_c2 = plt.subplot(gs[2, 1]); draw_chart(ax_c2, data_mid, t('chart_title_midday'))

    # Row 3: Evening
    ax_t3 = plt.subplot(gs[3, 0]); draw_table(ax_t3, stats_evening, t('summary_header_afternoon'), "#1f77b4")
    ax_c3 = plt.subplot(gs[3, 1]); draw_chart(ax_c3, data_eve, t('chart_title_evening'))

    plt.tight_layout()
    plt.savefig(output_image)
    print(t('plot_saved', output=output_image))

def export_to_excel_with_chart(output_path, df, stats_all, stats_morning, stats_midday, stats_evening):
    excel_path = os.path.splitext(output_path)[0] + ".xlsx"

    # Enforce numeric types
    for col in [t('col_sys'), t('col_dia'), t('col_hr')]:
        if col in df.columns:
             df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Pre-calculate Day and Period for grouping
    df['Day'] = df[df.columns[0]].dt.date
    df['Hour'] = df[df.columns[0]].dt.hour
    
    def get_period(h):
        if h < 10: return 'morning'
        if 10 <= h < 16: return 'midday'
        return 'evening'
    
    df['Period'] = df['Hour'].apply(get_period)

    # Helper to track column widths
    col_widths = {}
    def update_width(col_idx, value):
        current_w = col_widths.get(col_idx, 0)
        # Estimate width: Length of string representation + padding
        if isinstance(value, (datetime, date)):
            val_len = 12
        elif isinstance(value, float):
            val_len = len(f"{value:.2f}")
        else:
            val_len = len(str(value))
        
        # Cap max width to 50
        new_w = min(max(current_w, val_len + 2), 50)
        col_widths[col_idx] = new_w

    # 1. Calculate Daily Stats (Long Format)
    # Group by [Day, Period] -> Mean, Std
    daily_stats = df.groupby(['Day', 'Period'])[[t('col_sys'), t('col_dia'), t('col_hr')]].agg(['mean', 'std'])
    
    min_date = df['Day'].min()
    max_date = df['Day'].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq='D').date
    
    with pd.ExcelWriter(excel_path, engine='xlsxwriter', datetime_format='YYYY-MM-DD HH:mm') as writer:
        workbook = writer.book
        
        # === Sheet 1: Raw Data ===
        # Export original columns only (drop temp columns)
        raw_cols = [c for c in df.columns if c not in ['Day', 'Hour', 'Period']]
        df[raw_cols].to_excel(writer, sheet_name=t('sheet_data'), index=False)
        data_sheet = writer.sheets[t('sheet_data')]
        date_fmt = workbook.add_format({'num_format': 'YYYY-MM-DD HH:mm'})
        data_sheet.set_column('A:A', 20, date_fmt)

        # === Sheet 2: Summary (Static Tables) ===
        summary_ws = workbook.add_worksheet(t('sheet_summary'))
        writer.sheets[t('sheet_summary')] = summary_ws
        
        # Write Static Summary Tables (Calculated in Python)
        def write_static_table(ws, start_row, start_col, title, stats_df):
            ws.write(start_row, start_col, title, workbook.add_format({'bold': True, 'font_size': 12}))
            # stats_df is [Metrics x Stats] (Transposed in generate_statistics)
            # Write Headers (min, q1...)
            for i, h in enumerate(stats_df.columns):
                ws.write(start_row+1, start_col+1+i, h, workbook.add_format({'bold': True}))
            # Write Rows
            for r_idx, (metric, row) in enumerate(stats_df.iterrows()):
                ws.write(start_row+2+r_idx, start_col, metric, workbook.add_format({'bold': True}))
                for c_idx, val in enumerate(row):
                    ws.write_number(start_row+2+r_idx, start_col+1+c_idx, val)

        # Vertical Stack on Left
        write_static_table(summary_ws, 0, 0, t('summary_header_all'), stats_all)
        write_static_table(summary_ws, 8, 0, t('summary_header_morning'), stats_morning)
        write_static_table(summary_ws, 16, 0, t('summary_header_midday'), stats_midday)
        write_static_table(summary_ws, 24, 0, t('summary_header_afternoon'), stats_evening)

        # === Sheet 3: Chart Data (Static Values) ===
        chart_ws = workbook.add_worksheet(t('sheet_chart_data'))
        writer.sheets[t('sheet_chart_data')] = chart_ws
        
        # --- SECTION 1: LONG FORMAT ---
        cols = [
            t('col_label'), t('col_date_helper'), 
            t('col_sys'), t('col_dia'), t('col_hr'), 
            f"{t('col_sys')}_std", f"{t('col_dia')}_std", f"{t('col_hr')}_std"
        ]
        chart_ws.write_row('A1', cols)
        
        # Header Widths
        for i, c in enumerate(cols): update_width(i, c)
        
        period_map = {
            'morning': t('label_morning'),
            'midday': t('label_midday'),
            'evening': t('label_evening')
        }
        
        # Sort order: Date, then Period (Morn, Mid, Eve)
        row_long = 2
        for d in all_dates:
            d_str = d.strftime('%Y-%m-%d')
            for p_key in ['morning', 'midday', 'evening']:
                if (d, p_key) in daily_stats.index:
                    # Get values
                    stats = daily_stats.loc[(d, p_key)]
                    
                    means = [
                        round(stats[(t('col_sys'), 'mean')], 0),
                        round(stats[(t('col_dia'), 'mean')], 0),
                        round(stats[(t('col_hr'), 'mean')], 0)
                    ]
                    stds = [
                        round(stats[(t('col_sys'), 'std')], 0) if not pd.isna(stats[(t('col_sys'), 'std')]) else 0,
                        round(stats[(t('col_dia'), 'std')], 0) if not pd.isna(stats[(t('col_dia'), 'std')]) else 0,
                        round(stats[(t('col_hr'), 'std')], 0) if not pd.isna(stats[(t('col_hr'), 'std')]) else 0
                    ]
                    
                    label = f"{d_str} {period_map[p_key]}"
                    chart_ws.write(row_long-1, 0, label)
                    chart_ws.write_datetime(row_long-1, 1, d, date_fmt)
                    
                    update_width(0, label)
                    update_width(1, d)

                    # Write Means
                    chart_ws.write_number(row_long-1, 2, means[0])
                    chart_ws.write_number(row_long-1, 3, means[1])
                    chart_ws.write_number(row_long-1, 4, means[2])
                    update_width(2, means[0]); update_width(3, means[1]); update_width(4, means[2])

                    # Write Stds
                    chart_ws.write_number(row_long-1, 5, stds[0])
                    chart_ws.write_number(row_long-1, 6, stds[1])
                    chart_ws.write_number(row_long-1, 7, stds[2])
                    update_width(5, stds[0]); update_width(6, stds[1]); update_width(7, stds[2])
                    
                    row_long += 1
        
        last_row_long = row_long - 1

        # --- SECTION 2: WIDE FORMAT ---
        start_col_wide = 10 
        chart_ws.write(0, start_col_wide, "Date (Wide)")
        update_width(start_col_wide, "Date (Wide)")
        
        wide_headers = []
        for p_key in ['morning', 'midday', 'evening']:
            p_label = period_map[p_key]
            for metric in [t('col_sys'), t('col_dia'), t('col_hr')]:
                wide_headers.append(f"{p_label}_{metric}")
            for metric in [t('col_sys'), t('col_dia'), t('col_hr')]:
                wide_headers.append(f"{p_label}_{metric}_err")
        chart_ws.write_row(0, start_col_wide+1, wide_headers)
        
        for i, h in enumerate(wide_headers):
            update_width(start_col_wide+1+i, h)
        
        row_wide = 2
        for d in all_dates:
            chart_ws.write_datetime(row_wide-1, start_col_wide, d, date_fmt)
            update_width(start_col_wide, d)
            
            col_offset = 0
            for p_key in ['morning', 'midday', 'evening']:
                if (d, p_key) in daily_stats.index:
                    stats = daily_stats.loc[(d, p_key)]
                    
                    # Values
                    v1 = round(stats[(t('col_sys'), 'mean')], 0)
                    v2 = round(stats[(t('col_dia'), 'mean')], 0)
                    v3 = round(stats[(t('col_hr'), 'mean')], 0)

                    chart_ws.write_number(row_wide-1, start_col_wide+1+col_offset, v1)
                    chart_ws.write_number(row_wide-1, start_col_wide+2+col_offset, v2)
                    chart_ws.write_number(row_wide-1, start_col_wide+3+col_offset, v3)
                    
                    update_width(start_col_wide+1+col_offset, v1)
                    update_width(start_col_wide+2+col_offset, v2)
                    update_width(start_col_wide+3+col_offset, v3)

                    # Errors (Default 0 if NaN)
                    conf_std = lambda col: round(stats[(col, 'std')], 0) if not pd.isna(stats[(col, 'std')]) else 0
                    
                    e1 = conf_std(t('col_sys'))
                    e2 = conf_std(t('col_dia'))
                    e3 = conf_std(t('col_hr'))
                    
                    chart_ws.write_number(row_wide-1, start_col_wide+4+col_offset, e1)
                    chart_ws.write_number(row_wide-1, start_col_wide+5+col_offset, e2)
                    chart_ws.write_number(row_wide-1, start_col_wide+6+col_offset, e3)
                    
                    update_width(start_col_wide+4+col_offset, e1)
                    update_width(start_col_wide+5+col_offset, e2)
                    update_width(start_col_wide+6+col_offset, e3)
                
                col_offset += 6 # 3 vals + 3 errs per period
            
            row_wide += 1
        last_row_wide = row_wide - 1

        # Apply Auto-Widths
        for col, width in col_widths.items():
            chart_ws.set_column(col, col, width)

        # === CHARTS ===
        def create_chart(title, cat_sheet, cat_row_start, cat_row_end, cat_col, val_sheet, val_row_start, val_row_end, val_col_start, val_err_col_start, is_date_axis=False):
            chart = workbook.add_chart({'type': 'line'})
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            names = [t('col_sys'), t('col_dia'), t('col_hr')]
            
            for i in range(3):
                chart.add_series({
                    'name': names[i],
                    'categories': [cat_sheet, cat_row_start, cat_col, cat_row_end, cat_col],
                    'values':     [val_sheet, val_row_start, val_col_start+i, val_row_end, val_col_start+i],
                    'line':       {'color': colors[i], 'width': 2.25},
                    'marker':     {'type': 'circle', 'size': 5},
                    'y_error_bars': {
                        'type': 'custom',
                        'plus_values':  [val_sheet, val_row_start, val_err_col_start+i, val_row_end, val_err_col_start+i],
                        'minus_values': [val_sheet, val_row_start, val_err_col_start+i, val_row_end, val_err_col_start+i],
                        'line':         {'color': '#808080', 'transparency': 50}
                    }
                })
            chart.set_title({'name': title})
            
            x_axis_opts = {
                'name': t('axis_x'), 
                'major_gridlines': {'visible': True, 'line': {'width': 0.75, 'dash_type': 'dot'}}
            }
            if is_date_axis:
                x_axis_opts['date_axis'] = True
                x_axis_opts['num_format'] = 'yyyy-mm-dd'
            else:
                 x_axis_opts['text_axis'] = True # For string labels like "2025-01-01 Morning"

            chart.set_x_axis(x_axis_opts)
            chart.set_y_axis({'name': t('axis_y'), 'major_gridlines': {'visible': True}})
            chart.show_blanks_as('span')
            chart.set_legend({'position': 'bottom'})
            chart.set_size({'width': 800, 'height': 400})
            return chart

        # 1. Overall Chart (Long Data)
        if last_row_long > 1:
            chart1 = create_chart(t('chart_title'), t('sheet_chart_data'), 1, last_row_long-1, 0, t('sheet_chart_data'), 1, last_row_long-1, 2, 5, is_date_axis=False)
            summary_ws.insert_chart('H2', chart1)

        # 2. Morning Chart (Wide Data)
        # Morn Values start at K+1=11 (Index 11, 12, 13). Errs at 14, 15, 16.
        if last_row_wide > 1:
            chart2 = create_chart(t('chart_title_morning'), t('sheet_chart_data'), 1, last_row_wide-1, 10, t('sheet_chart_data'), 1, last_row_wide-1, 11, 14, is_date_axis=True)
            summary_ws.insert_chart('H24', chart2) 

            # 3. Midday Chart (Wide Data) - Offset 6
            chart3 = create_chart(t('chart_title_midday'), t('sheet_chart_data'), 1, last_row_wide-1, 10, t('sheet_chart_data'), 1, last_row_wide-1, 17, 20, is_date_axis=True)
            summary_ws.insert_chart('H46', chart3)

            # 4. Evening Chart (Wide Data) - Offset 12
            chart4 = create_chart(t('chart_title_evening'), t('sheet_chart_data'), 1, last_row_wide-1, 10, t('sheet_chart_data'), 1, last_row_wide-1, 23, 26, is_date_axis=True)
            summary_ws.insert_chart('H68', chart4)

    print(t('excel_exported', path=excel_path))

def main():
    global CURRENT_LANG
    args = parse_arguments()
    CURRENT_LANG = args.lang
    load_translations(CURRENT_LANG)

    df = read_and_merge_files(args.input, True)
    
    if len(df.columns) >= 4:
        df.rename(columns={ df.columns[1]: t('col_sys'), df.columns[2]: t('col_dia'), df.columns[3]: t('col_hr') }, inplace=True)
        int_cols = [t('col_sys'), t('col_dia'), t('col_hr')]
    else:
        int_cols = df.columns[1:4]
        
    datetime_col = df.columns[0]
    df = filter_and_sort_data(df, datetime_col, args.start_date, args.end_date)
    df.to_csv(os.path.splitext(args.output)[0] + ".csv", index=False)
    print(t('sorted_saved', output=args.output))

    # Calculate Stats
    stats_all, s_all = generate_statistics(df, int_cols, t('header_all_rows'))
    stats_morning, s_morn = generate_statistics(df[df[datetime_col].dt.hour < 10], int_cols, t('period_morning'))
    stats_midday, s_mid = generate_statistics(df[(df[datetime_col].dt.hour >= 10) & (df[datetime_col].dt.hour < 16)], int_cols, t('period_midday'))
    stats_evening, s_eve = generate_statistics(df[df[datetime_col].dt.hour >= 16], int_cols, t('period_afternoon'))

    export_to_excel_with_chart(args.output, df, stats_all, stats_morning, stats_midday, stats_evening)
    
    # Generate PNG Plot
    output_png = os.path.splitext(args.output)[0] + ".png"
    generate_plot(df, stats_all, stats_morning, stats_midday, stats_evening, datetime_col, int_cols, output_png)

if __name__ == "__main__":
    main()
