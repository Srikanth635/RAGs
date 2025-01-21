import pandas as pd
import os
from pathlib import Path
import re

# Function to split a line based on more than 2 spaces
def custom_split(line):
    return re.split(r' {2,}', line.strip())

# Function to read and convert test.log file to a pandas DataFrame
def read_test_log(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract header and data using custom split function
    header = custom_split(lines[0])
    data = [custom_split(line) for line in lines[1:] if line.strip()]
    # Create DataFrame
    df = pd.DataFrame(data, columns=header)

    # Convert TIME column to datetime format
    if 'TIME' in df.columns:
        df['TIME'] = pd.to_datetime(df['TIME'], format="%d-%b-%Y %H:%M:%S")

        # Format it to the desired output: YYYY-MM-DD HH:MM:SS
        df['TIME'] = df['TIME'].dt.strftime("%Y-%m-%d %H:%M:%S")

    return df

def read_test1_log(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract header and data using custom split function
    header = custom_split(lines[0])
    data = [custom_split(line) for line in lines[1:] if line.strip()]

    # Create DataFrame
    df = pd.DataFrame(data, columns=header)

    # Convert SYS_DATE column to datetime format if it exists
    if 'SYS_DATE' in df.columns:
        df['SYS_DATE'] = pd.to_datetime(df['SYS_DATE'], format="%d-%b-%Y %H:%M:%S")

        # Format it to the desired output: YYYY-MM-DD HH:MM:SS
        df['SYS_DATE'] = df['SYS_DATE'].dt.strftime("%Y-%m-%d %H:%M:%S")

    return df

# Function to write a DataFrame to Excel
def write_to_excel(dataframe, output_path, sheet_name="Sheet1"):
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

def merge_dataframes(df1, df2):
    # Rename SYS_DATE to TIME in df2
    if 'SYS_DATE' in df2.columns:
        df2 = df2.rename(columns={'SYS_DATE': 'TIME'})

    # Merge the two DataFrames on DB_NAME == INSTANCE_NAME
    merged_df = pd.merge(df1, df2, left_on='INSTANCE_NAME', right_on='DB_NAME', how='inner')
    merged_df = merged_df.drop(columns=['DB_NAME'])
    if 'HOST_NAME_x' in merged_df.columns and 'HOST_NAME_y' in merged_df.columns:
        merged_df = merged_df.drop(columns=['HOST_NAME_y'])
        merged_df = merged_df.rename(columns={'HOST_NAME_x': 'HOST_NAME'})
    return merged_df

if __name__ == '__main__':
    log_directory = Path('./new_logs')   ##give path of log files
    log_files = list(log_directory.glob('test*.log'))
    output = 'output.xlsx'
    output1 = 'output1.xlsx'
    out = 'final_output.xlsx'

    all_logs_df = pd.DataFrame()
    all_logs_df1 = pd.DataFrame()
    for log_file in log_files:
        if not "test1" in log_file.name:
            print(f"Processing file: {log_file}")
            df = read_test_log(log_file)
            all_logs_df = pd.concat([all_logs_df, df], ignore_index=True)
        else:
            print(f"Processing file: {log_file}")
            df = read_test1_log(log_file)
            all_logs_df1 = pd.concat([all_logs_df1, df], ignore_index=True)

    write_to_excel(all_logs_df, output)
    print(f"All log data written to {output}")
    # Write the consolidated DataFrame to Excel
    write_to_excel(all_logs_df1, output1)
    print(f"All log data written to {output1}")

    merged_df = merge_dataframes(all_logs_df, all_logs_df1)
    print("Merged DataFrame:")
    print(merged_df)
    out = 'final_output.xlsx'
    write_to_excel(merged_df, out)
    print(f"All log data written to {out}")
