import pandas as pd
import sys

# Helpers for time slots
def get_time_slot(h):
    if h < 10: return 'morning'
    if h < 16: return 'midday'
    return 'evening'

try:
    df = pd.read_csv('Evolv-1-2026-01-11-od_2026-01-06.csv')
    df['Date'] = pd.to_datetime(df.iloc[:,0])
    df['Day'] = df['Date'].dt.date
    df['Hour'] = df['Date'].dt.hour
    df['Period'] = df['Hour'].apply(get_time_slot)

    print("Counts per Day/Period:")
    counts = df.groupby(['Day', 'Period']).size()
    print(counts)
    
    # Check Stdev manually for a sample
    print("\nSample StdDev Calculation (Python):")
    for name, group in df.groupby(['Day', 'Period']):
        print(f"\n{name}: count={len(group)}")
        if len(group) > 1:
            print(group.iloc[:, 1:4].std())
        else:
            print("Single value, std=NaN")

except Exception as e:
    print(e)
