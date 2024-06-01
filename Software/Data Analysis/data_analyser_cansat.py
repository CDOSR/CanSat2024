import os
import datetime
import logging
import configparser
import json

import folium
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm, rcParams
import seaborn as sns

CONFIG_FILE_NAME = 'config_base.ini'

# Assuming ESP32 epoch starts on 1994-01-01
esp32_epoch_start = datetime.datetime(2000, 1, 1)
unix_epoch_start = datetime.datetime(1970, 1, 1)
epoch_offset = (esp32_epoch_start - unix_epoch_start).total_seconds()

logging.basicConfig(
    filename='CanSat24_base_app.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

attribute_units = {
    'temperature': '°C',
    'pressure': 'hPa',
    'speed': 'm/s',
    'humidity': '%',
    'altitude': 'm',
    'co2': '400 - 65000 ppm',
    'tvoc': '0 - 65000 ppb',
}

def convert_ddm_to_dd(ddm_value):
    if pd.isna(ddm_value):
        return np.nan
    
    direction = ddm_value[-1]
    ddm_value = ddm_value[:-1]
    
    try:
        parts = ddm_value.split('.')
        degrees = int(parts[0][:-2])
        minutes = float(parts[0][-2:] + '.' + parts[1])
        
        decimal_degrees = degrees + minutes / 60.0
        
        if direction in ['S', 'W']:
            decimal_degrees *= -1
        
        return decimal_degrees
    except (ValueError, IndexError):
        return np.nan


def process_gps_data(df, lat_col, lon_col):
    df[lat_col] = df[lat_col].apply(convert_ddm_to_dd)
    df[lon_col] = df[lon_col].apply(convert_ddm_to_dd)
    return df

def read_configuration(file_path: str = CONFIG_FILE_NAME) -> dict:
    if not os.path.exists(file_path):
        logging.error(f"The configuration file {file_path} does not exist.")
        raise FileNotFoundError(f"Configuration file {file_path} not found.")
    else:
        logging.info(f"The configuration file {file_path} has been loaded successfully.")
    
    config = configparser.ConfigParser()
    
    try:
        config.read(file_path)
    except configparser.MissingSectionHeaderError:
        logging.error(f"The configuration file {file_path} is missing section headers.")
        raise
    except configparser.ParsingError as pe:
        logging.error(f"Error parsing the configuration file {file_path}: {str(pe)}")
        raise
    
    try:
        column_categories = {}
        for category, section_name in config['CATEGORIES'].items():
            try:
                columns = {key: value for key, value in config[section_name.upper()].items()}
            except KeyError:
                logging.error(f"Section {section_name} not found in the configuration file.")
                raise
            column_categories[category] = columns

        try:
            raw_line_styles = config.get('PLOT_CONFIG', 'LineStyles')
            line_styles = {key: val for key, val in (item.split(":") for item in raw_line_styles.split(','))}
        except (configparser.NoOptionError, ValueError):
            logging.warning("LineStyles improperly configured or not found, using defaults.")
            line_styles = {}

        configuration = {
            "file_name": config.get('FILE', 'Name'),
            "column_categories": column_categories,
            "launch_time": datetime.datetime(
                config.getint('LAUNCH', 'Year'),
                config.getint('LAUNCH', 'Month'),
                config.getint('LAUNCH', 'Day'),
                config.getint('LAUNCH', 'Hour'),
                config.getint('LAUNCH', 'Minute'),
                config.getint('LAUNCH', 'Second')
            ).timestamp(),
            "data_slice": {
                "start": config.getint('DATA_SLICE', 'Start'),
                "end": config.getint('DATA_SLICE', 'End'),
            },
            "plot_config": {
                "file_format": config.get('PLOT_CONFIG', 'FileFormat'),
                "dpi": config.getint('PLOT_CONFIG', 'DPI'),
                "figure_size": (
                    config.getint('PLOT_CONFIG', 'FigureSizeWidth'),
                    config.getint('PLOT_CONFIG', 'FigureSizeHeight')
                ),
                "label_font_size": config.getint('PLOT_CONFIG', 'LabelFontSize'),
                "title_font_size": config.getint('PLOT_CONFIG', 'TitleFontSize'),
                "line_styles": line_styles
            },
            "plot": {
                "x0": config.getfloat('PLOT', 'x0'),
                "x1": config.getfloat('PLOT', 'x1'),
                "title": config.get('PLOT', 'Title'),
                "xlabel": config.get('PLOT', 'XLabel'),
                "ylabel": config.get('PLOT', 'YLabel'),
            },
            "color_palettes": {
                "palette1": config.get('COLOR_PALETTES', 'palette1'),
                "palette1_colors": config.getint('COLOR_PALETTES', 'palette1_colors'),
            },
            "output": {
                "plot_path": config.get('OUTPUT', 'PlotPath'),
            }
        }
        logging.info(f"Configuration from {file_path} has been read successfully.")
        return configuration
    except (configparser.NoOptionError, configparser.NoSectionError) as e:
        logging.error(f"Error reading configuration from {file_path}: {str(e)}")
        raise
    except ValueError as ve:
        logging.error(f"Invalid value in the configuration file {file_path}: {str(ve)}")
        raise

def get_dynamic_path(base_path: str, launch_datetime: datetime.datetime) -> str:
    file_name, file_extension = os.path.splitext(base_path)
    timestamp = launch_datetime.strftime("%Y%m%d-%H%M%S")
    return f"{file_name}_{timestamp}{file_extension}"

def setup_plotting():
    try:
        fpath = os.path.join(matplotlib.get_data_path(), "fonts/ttf/Roboto-Regular.ttf")
        prop = fm.FontProperties(fname=fpath)
    except FileNotFoundError:
        logging.warning("Roboto font not found, using default font.")
        prop = fm.FontProperties()

    rcParams['font.family'] = "roboto"
    rcParams['pdf.fonttype'] = 42 
    rcParams['ps.fonttype'] = 42 

    sns.set(style="darkgrid")
    plt.rcParams["xtick.major.size"] = 4
    plt.rcParams["ytick.major.size"] = 8
    
    return prop

def basic_data_checks(df: pd.DataFrame):
    if df.isnull().values.any():
        logging.warning("NaN values detected.")
        return False
    
    for column in df.select_dtypes(include=[np.number]).columns:
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        if np.any(z_scores > 3):
            logging.warning(f"Outliers detected in column {column}.")
            return False

    logging.info("Basic data checks passed.")
    return True

def pre_processing_checks(df, melted_df, value_vars):
    if len(df) * len(value_vars) != len(melted_df):
        logging.warning("Data loss or duplication detected during melting.")
        return False

    logging.info("Pre-processing checks passed.")
    return True

def get_time_columns_from_config(file_path: str = CONFIG_FILE_NAME):
    config = configparser.ConfigParser()
    config.read(file_path)
    time_columns = [config.get('TIME_COLUMNS', key) for key in config.options('TIME_COLUMNS')]
    return time_columns

def load_and_prepare_data(filepath: str, time_columns, custom_dict=None, **kwargs) -> pd.DataFrame:
    try:
        dfall = pd.read_json(filepath, **kwargs)

        logging.info(f"Initial columns after loading JSON: {dfall.columns.tolist()}")

        for col in ['data', 'esp']:
            if col in dfall.columns:
                dfall = dfall.copy()
                
                def parse_json(entry):
                    expanded_entry = {}
                    if isinstance(entry, dict):
                        for key, value in entry.items():
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    if isinstance(sub_value, dict):
                                        for inner_key, inner_value in sub_value.items():
                                            expanded_entry[f"{key}_{sub_key}_{inner_key}"] = inner_value
                                    else:
                                        expanded_entry[f"{key}_{sub_key}"] = sub_value
                            else:
                                expanded_entry[key] = value
                    elif isinstance(entry, str):
                        try:
                            entry = json.loads(entry)
                            for key, value in entry.items():
                                if isinstance(value, dict):
                                    for sub_key, sub_value in value.items():
                                        if isinstance(sub_value, dict):
                                            for inner_key, inner_value in sub_value.items():
                                                expanded_entry[f"{key}_{sub_key}_{inner_key}"] = inner_value
                                        else:
                                            expanded_entry[f"{key}_{sub_key}"] = sub_value
                                else:
                                    expanded_entry[key] = value
                        except json.JSONDecodeError:
                            return pd.Series()
                    return pd.Series(expanded_entry)
                
                df_expanded = dfall[col].apply(parse_json)
                dfall = pd.concat([dfall.drop(columns=[col]), df_expanded], axis=1)

        logging.info(f"Columns after expanding 'data' and 'esp': {dfall.columns.tolist()}")

        if custom_dict:
            relevant_columns = [val for val in custom_dict.values() if val in dfall.columns]
            df = dfall[relevant_columns]
        else:
            df = dfall

        logging.info(f"Columns after applying custom dictionary: {df.columns.tolist()}")

        # Convert time columns to datetime format
        esp32_epoch_start = datetime.datetime(2000, 1, 1)
        unix_epoch_start = datetime.datetime(1970, 1, 1)
        epoch_offset = (esp32_epoch_start - unix_epoch_start).total_seconds()

        for column in time_columns:
            if column in dfall.columns:
                if column == 'epoch':
                    # Adjust the 'epoch' values by adding the offset
                    df.loc[:, column] = dfall[column].apply(lambda x: datetime.datetime.fromtimestamp(x + epoch_offset))
                else:
                    df.loc[:, column] = pd.to_datetime(df[column], errors='coerce')

        logging.info(f"Final columns in the DataFrame: {df.columns.tolist()}")
        
        logging.info(f"Data from {filepath} JSON has been read successfully.")
        
        
    except FileNotFoundError:
        logging.error(f"Data file {filepath} not found.")
        raise
    except ValueError as e:
        logging.error(f"Error loading data file {filepath}: {e}")
        raise
    
    return df

def prepare_data_for_plotting(df: pd.DataFrame, attribute, launch_datetime: datetime.datetime) -> pd.DataFrame:
    if 'epoch' not in df.columns:
        logging.error("The 'epoch' column is missing from the DataFrame.")
        raise KeyError("The 'epoch' column is missing from the DataFrame.")
    
    df['epoch'] = pd.to_datetime(df['epoch'])
    
    launchtime = launch_datetime.timestamp()
    launch_datetime = pd.to_datetime(launch_datetime)
    firstRuntime = df['epoch'].iloc[0]
    launchtime = pd.to_datetime(launchtime)
    firstRuntime = pd.to_datetime(firstRuntime)

    df['epoch'] = df['epoch'] - firstRuntime

    df['TimeOfFlight'] = launchtime + df['epoch']
    df['TimeOfFlight'] = launchtime + pd.to_timedelta(df['epoch']) - firstRuntime
    
    df.index = launch_datetime + df['TimeOfFlight']
    return df

def prepare_plot_elements(df: pd.DataFrame, attribute, valuevars) -> pd.DataFrame:
    # Ensure value_vars exist in DataFrame columns
    valuevars = [var for var in valuevars if var in df.columns]

    # Check for missing value_vars
    missing_vars = set(value_vars) - set(df.columns)
    if missing_vars:
        logging.warning(f"The following value_vars are missing from the DataFrame and will be skipped: {missing_vars}")

    # Replace 'none' with NaN for existing value_vars
    for var in valuevars:
        df[var] = df[var].replace('none', np.nan)
        # Handle strings with 'M' suffix and convert to float
        df[var] = df[var].apply(lambda x: float(str(x).replace('M', '')) if isinstance(x, str) else x)

    # Convert 'epoch' column to Unix timestamp
    df['epoch'] = df['epoch'].astype('int64') // 10**9

    dfAlt = pd.melt(df, id_vars='epoch', value_vars=valuevars)
    
    return dfAlt

def configure_plot_appearance(ax, x0, x1):
    ax.axvspan(x0, x1, color='#66DDF4', alpha=0.5)
    xlim = ax.get_xlim()
    ax.set_xlim(xlim)
    
    ax.set_xlabel('Time of Flight [s]', fontsize=14)
    ax.set_ylabel('Temperature [°C]', fontsize=14)
    return ax

def create_plot(dfAlt: pd.DataFrame):
    sns.set_palette(sns.color_palette("RdPu_r", n_colors=4))
    sns.despine(top=True, offset=40, trim=True)
    ax = sns.lineplot(x='epoch', y='value', hue='variable', data=dfAlt)
    
    return ax

def customize_plot(ax, x0: float, x1: float, figure_size: tuple,
                   title: str, xlabel: str, ylabel: str,
                   label_font_size: int, title_font_size: int,
                   line_styles: dict):
    ax.axvspan(x0, x1, color='#66DDF4', alpha=0.5)
    ax.set_xlabel(xlabel, fontsize=label_font_size)
    ax.set_ylabel(ylabel, fontsize=label_font_size)
    ax.set_title(title, fontsize=title_font_size)
    ax.figure.set_size_inches(*figure_size)

    if line_styles:
        for line, style in zip(ax.lines, line_styles.values()):
            if style == "line":
                line.set_linestyle("-")
            elif style == "dash":
                line.set_linestyle("--")

def display_plot():
    plt.show()

def save_plot(file_path: str, file_format: str, dpi: int):
    plt.savefig(file_path, format=file_format, dpi=dpi)

def clean_column(df, column_name):
    df[column_name] = df[column_name].replace('None', np.nan).astype(float)
    return df

def plot_coordinates_on_map(coordinates_df, map_file="map.html"):
    if 'gps_gps1_latitude' not in coordinates_df.columns or 'gps_gps1_longitude' not in coordinates_df.columns:
        raise ValueError("Dataframe must contain 'latitude' and 'longitude' columns.")
    
    m = folium.Map(
        location=[coordinates_df['gps_gps1_latitude'].mean(), coordinates_df['gps_gps1_longitude'].mean()], 
        zoom_start=13
    )

    for _, row in coordinates_df.iterrows():
        folium.Marker(
            location=[row['gps_gps1_latitude'], row['gps_gps1_longitude']],
        ).add_to(m)
    
    m.save(map_file)
    logging.info(f"Map saved as {map_file}")

if __name__ == "__main__":
    prop = setup_plotting()

    config_params = read_configuration('config_base.ini')

    attributes = ["temperature", "pressure", "humidity", "altitude", "uv"]

    file_name = config_params['file_name']

    column_categories = config_params['column_categories'] 
    launch_time_params = config_params['launch_time']
    launch_datetime = datetime.datetime.fromtimestamp(launch_time_params)
    time_columns = get_time_columns_from_config()
    df_gps = load_and_prepare_data(file_name, time_columns, column_categories['position'])

    # Convert GPS data from DDM to DD
    df_gps = process_gps_data(df_gps, 'gps_gps1_latitude', 'gps_gps1_longitude')

    for attribute in attributes:
        time_columns = get_time_columns_from_config()
        df = load_and_prepare_data(file_name, time_columns, column_categories[attribute])

        df = prepare_data_for_plotting(df, attribute, launch_datetime)
        x0, x1 = config_params['plot']['x0'], config_params['plot']['x1'] 

        if attribute in column_categories:
            value_vars = [v for k, v in column_categories[attribute].items()] 

        # Filter out non-existent columns
        value_vars = [var for var in value_vars if var in df.columns] 
          
        dfAlt = prepare_plot_elements(df, attribute, value_vars)

        if basic_data_checks(df) and pre_processing_checks(df, dfAlt, value_vars):
            logging.info("All checks passed, proceed to plotting.")
        else:
            logging.warning("Checks failed. Review warnings and adjust data/pre-processing.")
        
        ax = create_plot(dfAlt)

        plot_config = config_params['plot_config']
        figure_size = plot_config['figure_size']
        label_font_size = plot_config['label_font_size']
        title_font_size = plot_config['title_font_size']
        line_styles = config_params['plot_config']['line_styles']

        plot_params = config_params['plot']
        title = f"{attribute.capitalize()} {plot_params['title']}"
        xlabel = plot_params['xlabel']
        unit = attribute_units.get(attribute, '')
        ylabel = f"{attribute.capitalize()} ({unit})"
        
        customize_plot(ax, x0, x1, figure_size, title, xlabel, ylabel, label_font_size, title_font_size, line_styles)
        
        display_plot()

        file_format = plot_config['file_format']
        dpi = plot_config['dpi']    
        dynamic_path = get_dynamic_path(config_params['output']['plot_path'], launch_datetime)
        save_plot(dynamic_path, file_format, dpi)

    try:
        df_gps['gps_gps1_latitude'] = pd.to_numeric(df_gps['gps_gps1_latitude'], errors='coerce') 
        df_gps['gps_gps1_longitude'] = pd.to_numeric(df_gps['gps_gps1_longitude'], errors='coerce')
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")

    df_gpsc = df_gps.replace({"None": None}, inplace=True)
    df_gpsc = df_gps[(df_gps['gps_gps1_latitude'].notna()) & (df_gps['gps_gps1_longitude'].notna())]
    df_gpsc.reset_index(drop=True, inplace=True)
    plot_coordinates_on_map(df_gpsc, "my_map.html")
