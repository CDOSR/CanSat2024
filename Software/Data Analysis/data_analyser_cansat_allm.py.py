import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import datetime
import logging
import configparser
import os
import numpy as np
import json

logging.basicConfig(
    filename='app.log',  # log to a file
    filemode='w',  # overwrite the log file if exists
    level=logging.INFO,  # default log level
    format='%(asctime)s - %(levelname)s - %(message)s',  # format of log messages
)

def read_configuration(file_path: str = 'config.ini') -> dict:
    """
    Reads configuration from a configuration file.
    
    Parameters:
        file_path (str): The path to the configuration file. Defaults to 'config.ini'.
        
    Returns:
        dict: Configuration parameters.
    """
    if not os.path.exists(file_path):
        logging.error(f"The configuration file {file_path} does not exist.")
        raise FileNotFoundError(f"{file_path} not found.")

    config = configparser.ConfigParser()
    config.read(file_path)

    try:
        return {
            "file_name": config.get('FILE', 'Name'),
            "launch_time": datetime.datetime(
                config.getint('LAUNCH', 'Year'),
                config.getint('LAUNCH', 'Month'),
                config.getint('LAUNCH', 'Day'),
                config.getint('LAUNCH', 'Hour'),
                config.getint('LAUNCH', 'Minute'),
                config.getint('LAUNCH', 'Second')
            ).timestamp(),
            "start_idx": config.getint('DATA_SLICE', 'Start'),
            "end_idx": config.getint('DATA_SLICE', 'End'),
            "colors": {
                "color1": config.get('COLORS', 'Color1'),
                "color2": config.get('COLORS', 'Color2'),
                "color3": config.get('COLORS', 'Color3'),
            },
            "column_names": {
                "runtime": config.get('COLUMN_NAMES', 'Runtime'),
                "temperature": config.get('COLUMN_NAMES', 'Temperature'),
                "pressure": config.get('COLUMN_NAMES', 'Pressure'),
                "altitude": config.get('COLUMN_NAMES', 'Altitude'),
                "time_of_flight": config.get('COLUMN_NAMES', 'TimeOfFlight')
            },
            "plot_config": {
                "file_format": config.get('PLOT_CONFIG', 'FileFormat'),
                "dpi": config.getint('PLOT_CONFIG', 'DPI'),
                "figure_size": (
                    config.getint('PLOT_CONFIG', 'FigureSizeWidth'),
                    config.getint('PLOT_CONFIG', 'FigureSizeHeight')
                ),
            }
        }

    except configparser.NoOptionError as noe:
        logging.error(f"Configuration reading error: {str(noe)}")
        raise

def validate_dataframe(df: pd.DataFrame, columns: dict):
    """
    Validates that the dataframe contains the expected columns.

    Parameters:
        df (pd.DataFrame): Dataframe to validate.

    Raises:
        ValueError: If expected columns are not present in the dataframe.
    """
    expected_columns = [
        columns["runtime"], 
        columns["temperature"], 
        columns["pressure"], 
        columns["altitude"], 
        columns["time_of_flight"]
    ]
    print(expected_columns)
    logging.info(f"Dataframe columns: {df.columns}")
    missing_columns = [col for col in expected_columns if col not in df.columns]

    print(f"Missing columns: {missing_columns}")

    
    for col in expected_columns:
        print(col, df.columns) 
    if missing_columns:
        logging.error(f"Missing columns in dataframe: {missing_columns}")
        raise ValueError(f"Dataframe does not contain all expected columns. Missing: {missing_columns}")


def load_and_prepare_data(file_name: str, launchtime: float, columns: dict) -> pd.DataFrame:
    try:
        with open(file_name, 'r') as f:
            data = json.load(f)
        
        # Extract relevant information
        records = []
        for item in data:
            record = {
                "runtime": item["epoch"],
                "temperature": item["data"]["temp"]["mcp9808"],
                "pressure": item["data"]["pres"]["bmp280"],
                "altitude": item["data"]["alt"]["lps25h"]
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        logging.info(f"Data columns: {df.columns}")
        logging.info(df.head())
        
        first_runtime = df["runtime"].iloc[0]
        df["time_of_flight"] = launchtime + df["runtime"] - first_runtime
        df["pressure"] = 100 * df["pressure"]  # Converting pressure to Pascals if necessary
        df.index = pd.to_datetime(df["time_of_flight"], unit='s')
        return df
    except Exception as e: 
        logging.error(f"An error occurred: {str(e)}")
        return pd.DataFrame()

def prepare_data_for_plotting(df, start_idx, end_idx, columns):
    df_flight = df.iloc[start_idx:end_idx, :]
    sec_f = pd.to_datetime(df_flight["time_of_flight"], unit='s')
    temp_f = df_flight["temperature"]
    pres_f = df_flight["pressure"] / 100  # Converting back to hPa
    alt_f = pd.to_numeric(df_flight["altitude"], errors='coerce')
    return sec_f, temp_f, pres_f, alt_f

def prepare_plot_elements(sec_f, temp_f, pres_f, alt_f, colors):
    m_fmt = mdates.DateFormatter('%H:%M:%S')
    plt.figure(figsize=config['plot_config']['figure_size'])
    host = host_subplot(111, axes_class=AA.Axes)
    plt.subplots_adjust(right=0.75)
    launch_datetime = pd.to_datetime(sec_f.iloc[0], unit='s')  # converting first second of flight to datetime
    launch_date_str = launch_datetime.strftime('%Y-%m-%d')  # formatting date to string (YYYY-MM-DD)
    plt.title(f'CanSat 2024 Sensor Readings from mission time (GMT Time) [{launch_date_str}]')
    
    par1 = host.twinx()
    par2 = host.twinx()
    
    OFFSET = 60
    new_fixed_axis = par2.get_grid_helper().new_fixed_axis
    par1.axis["right"] = new_fixed_axis(loc="right", axes=par1, offset=(OFFSET, 0))
    par2.axis["right"] = new_fixed_axis(loc="right", axes=par2, offset=(2.5 * OFFSET, 0))
    
    host.set_xlabel('Time [hh:mm:ss]')
    host.set_ylabel('Temperature [°C]', color=colors['color1'])
    par1.set_ylabel('Pressure [hPa]', color=colors['color2'])
    par2.set_ylabel('Altitude [m]', color=colors['color3'])
    host.xaxis.set_major_formatter(m_fmt)
    
    p1, = host.plot(sec_f, temp_f, color=colors['color1'], label='Temperature', linestyle='-', marker='o', markersize=3)
    p2, = par1.plot(sec_f, pres_f, color=colors['color2'], label='Pressure', linestyle='-', marker='o', markersize=3)
    p3, = par2.plot(sec_f, alt_f, color=colors['color3'], label='Altitude', linestyle='-', marker='o', markersize=3)

    par1.yaxis.label.set_color(p2.get_color())
    par1.spines['right'].set_color(p2.get_color())
    par1.tick_params(axis='y', colors=p2.get_color())
    par2.yaxis.label.set_color(p3.get_color())
    par2.spines['right'].set_color(p3.get_color())
    par2.tick_params(axis='y', colors=p3.get_color())

    host.legend()
    
    return host, par1, par2, p1, p2, p3

def configure_plot_appearance(host, par1, par2, p1, p2, p3, pres_min, pres_max, alt_min, alt_max, save_path=None):
    par1.set_ylim([pres_min, pres_max])
    par1.yaxis.set_ticks(range(int(pres_min), int(pres_max) + 10, 5)) 
    par2.set_ylim([alt_min, alt_max])  # Set min and max for altitude
    par2.yaxis.set_ticks(range(int(alt_min), int(alt_max) + 10, 10))  # Set tick interval to 10

    par1.yaxis.label.set_color(p2.get_color())
    host.yaxis.label.set_color(p1.get_color())
    par2.yaxis.label.set_color(p3.get_color())
    par2.spines['right'].set_color(p3.get_color())  # Ensure spine has same color as line and label
    par2.tick_params(axis='y', colors=p3.get_color())  # Ensure ticks have same color as line and label

    plt.draw()
    
    if save_path is not None:
        plt.savefig(save_path, format=config['plot_config']['file_format'], dpi=config['plot_config']['dpi'])

    try:
        plt.show()
    except Exception as e:
        logging.error(f"Could not show the plot due to: {str(e)}")

def plot_data(df: pd.DataFrame, start_idx: int, end_idx: int, colors: dict, columns: dict):
    # Validating index slicing, ensuring that it's in the valid range
    if start_idx < 0 or end_idx > len(df) or start_idx >= end_idx:
        logging.error("Invalid start or end index for plotting.")
        return
    
    sec_f, temp_f, pres_f, alt_f = prepare_data_for_plotting(df, start_idx, end_idx, columns)
    host, par1, par2, p1, p2, p3 = prepare_plot_elements(sec_f, temp_f, pres_f, alt_f, colors)

    # Get min and max altitude (considering NaN values)
    alt_min, alt_max = np.nanmin(alt_f), np.nanmax(alt_f)
    alt_min = (int(alt_min // 10) * 10)  # Round down to nearest 10
    alt_max = (int(alt_max // 10) * 10) + 10  # Round up to nearest 10

    pres_min, pres_max = np.nanmin(pres_f), np.nanmax(pres_f)
    pres_min = (int(pres_min // 10) * 10)  # Round down to nearest 10
    pres_max = (int(pres_max // 10) * 10) + 10  # Round up to nearest 10

    configure_plot_appearance(host, par1, par2, p1, p2, p3, pres_min, pres_max, alt_min, alt_max, save_path="output_plot.png")

if __name__ == "__main__":
    config = read_configuration()
    df = load_and_prepare_data(config['file_name'], config['launch_time'], config['column_names'])
    print(df)
    print(config['column_names'])

    if not df.empty:
        validate_dataframe(df, config['column_names'])
        plot_data(df, config['start_idx'], config['end_idx'], config['colors'], config['column_names'])
    else:
        logging.warning("Dataframe is empty. Visualization is skipped.")
