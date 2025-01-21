import cudf
import dask_cudf
import dask.bag as db
from dask_cuda import LocalCUDACluster
from dask.distributed import Client
from pathlib import Path
import re

# Function to split a line based on more than 2 spaces
def custom_split(line):
    return re.split(r' {2,}', line.strip())

# Function to read log file and convert to cudf DataFrame
def read_log_cudf(file_path, date_column=None, date_format="%d-%b-%Y %H:%M:%S"):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract header and data using custom split function
    header = custom_split(lines[0])
    data = [custom_split(line) for line in lines[1:] if line.strip()]

    # Create cuDF DataFrame
    df = cudf.DataFrame(data, columns=header)

    # Convert date column to datetime format if specified
    if date_column in df.columns:
        df[date_column] = cudf.to_datetime(df[date_column], format=date_format, errors="coerce")
    return df

# Function to write a DataFrame to Excel (optional: use cudf CSV instead)
def write_to_csv(dataframe, output_path):
    dataframe.to_csv(output_path, index=False)
    print(f"Data written to {output_path}")

# Function to process a single log file
def process_file(file_path):
    if "test1" in file_path.name:
        return read_log_cudf(file_path, date_column="SYS_DATE")
    else:
        return read_log_cudf(file_path, date_column="TIME")

if __name__ == "__main__":
    # Set up Dask with CUDA cluster
    cluster = LocalCUDACluster()
    client = Client(cluster)

    log_directory = Path("./new_logs")  # Directory containing log files
    log_files = list(log_directory.glob("test*.log"))

    # Use Dask Bag to process files in parallel
    dask_bag = db.from_sequence(log_files, npartitions=len(log_files)).map(process_file)

    # Compute the results on GPU workers
    processed_files = dask_bag.compute()

    # Separate results into test.log and test1.log DataFrames
    all_logs_df = cudf.concat([df for df in processed_files if "TIME" in df.columns])
    all_logs_df1 = cudf.concat([df for df in processed_files if "SYS_DATE" in df.columns])

    # Write individual results to CSV (or Excel)
    if not all_logs_df.empty:
        write_to_csv(all_logs_df, "output_test.csv")
    if not all_logs_df1.empty:
        write_to_csv(all_logs_df1, "output_test1.csv")

    # Example merge function using GPU
    if not all_logs_df.empty and not all_logs_df1.empty:
        merged_df = dask_cudf.merge(
            all_logs_df,
            all_logs_df1.rename(columns={"SYS_DATE": "TIME"}),
            left_on="INSTANCE_NAME",
            right_on="DB_NAME",
            how="inner",
        ).drop(columns=["DB_NAME"])

        # Write merged DataFrame to CSV
        write_to_csv(merged_df, "final_output.csv")

    client.close()
