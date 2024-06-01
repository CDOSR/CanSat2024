import os
import datetime
import logging
import configparser
import time
import json

import folium
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
#import matplotlib.gridspec as gridspec
from matplotlib import font_manager as fm, rcParams, rc
from matplotlib.lines import Line2D
import seaborn as sns

CONFIG_FILE_NAME = 'config_base.ini'

logging.basicConfig(
    filename='rcrc24_base_app.log',  # log to a file
    filemode='w',  # overwrite the log file if exists
    level=logging.INFO,  # default log level
    format='%(asctime)s - %(levelname)s - %(message)s',  # format of log messages
)

attribute_units = {
    'temperature': '°C',
    'pressure': 'hPa',
    'speed': 'm/s',
    'humidity': '%',
    'altitude' : 'm',
    'co2' : '400 - 65000 ppm',
    'tvoc' : '0 - 65000 ppb',
    #'airquality' : '1 to 5'
    # ... add other attributes and their units as needed
}

def read_configuration(file_path: str = CONFIG_FILE_NAME) -> dict:
    """
    Reads configuration from a configuration file and returns it as a dictionary.
    
    Parameters:
        file_path (str): The path to the configuration file. Defaults to 'config.ini'.
        
    Returns:
        dict: Configuration parameters.
    """
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
        # Read and store categories and their related columns
        column_categories = {}
        for category, section_name in config['CATEGORIES'].items():
            try:
                columns = {key: value for key, value in config[section_name.upper()].items()}
            except KeyError:
                logging.error(f"Section {section_name} not found in the configuration file.")
                raise

            column_categories[category] = columns

        # MODIFY the Line Styles reading process for safety
        try:
            raw_line_styles = config.get('PLOT_CONFIG', 'LineStyles')
            line_styles = {key: val for key, val in (item.split(":") for item in raw_line_styles.split(','))}
        except (configparser.NoOptionError, ValueError):
            logging.warning("LineStyles improperly configured or not found, using defaults.")
            line_styles = {}  # or some default line styles

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
                "title" : config.get('PLOT', 'Title'),
                "xlabel" : config.get('PLOT', 'XLabel'),
                "ylabel" : config.get('PLOT', 'YLabel'),
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
    """
    Generate a dynamic file path by appending a formatted launch time to avoid overwrites.

    Parameters:
        base_path (str): The base path or template for the file path.
        launch_datetime (datetime.datetime): The launch time extracted from the config.

    Returns:
        str: The generated file path with the formatted launch time.
    """
    file_name, file_extension = os.path.splitext(base_path)
    timestamp = launch_datetime.strftime("%Y%m%d-%H%M%S")
    return f"{file_name}_{timestamp}{file_extension}"

# Setup plotting configurations
def setup_plotting():
    """
    Setup plotting configurations and return font properties.
    """
        # MODIFY for safe font loading
    try:
        fpath = os.path.join(matplotlib.get_data_path(), "fonts/ttf/Roboto-Regular.ttf")
        prop = fm.FontProperties(fname=fpath)
    except FileNotFoundError:
        logging.warning("Roboto font not found, using default font.")
        prop = fm.FontProperties()  # using default if Roboto is not available

    rcParams['font.family'] = "roboto"
    rcParams['pdf.fonttype'] = 42 
    rcParams['ps.fonttype'] = 42 

    sns.set(style="darkgrid")
    plt.rcParams["xtick.major.size"] = 4
    plt.rcParams["ytick.major.size"] = 8
    
    return prop

def basic_data_checks(df: pd.DataFrame):
    """
    Perform basic data checks.

    Parameters:
        df (pd.DataFrame): The input data frame.

    Returns:
        bool: True if checks pass, False otherwise.
    """
    # Check for NaN values
    if df.isnull().values.any():
        logging.warning("NaN values detected.")
        return False
    
    # Check for outliers in numerical columns
    for column in df.select_dtypes(include=[np.number]).columns:
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        if np.any(z_scores > 3):  # Adjust threshold as needed
            logging.warning(f"Outliers detected in column {column}.")
            return False

    logging.info("Basic data checks passed.")
    return True

def pre_processing_checks(df, melted_df, value_vars):
    """
    Perform checks on pre-processed data.

    Parameters:
        df (pd.DataFrame): The original data frame.
        melted_df (pd.DataFrame): The melted data frame.
        value_vars (list): List of melted variables.

    Returns:
        bool: True if checks pass, False otherwise.
    """
    # Check log transformation (if applicable)
    # if any(df[['bmp388Temp', 'bme280Temp', 'mcp9808Temp']] <= 0):
    #     logging.warning("Non-positive values detected; check log transformations.")
    #     return False
    
    # Check the melting process
    if len(df) * len(value_vars) != len(melted_df):
        logging.warning("Data loss or duplication detected during melting.")
        return False

    logging.info("Pre-processing checks passed.")
    return True

# Function to get time columns from the config file
def get_time_columns_from_config(file_path: str = CONFIG_FILE_NAME):
    config = configparser.ConfigParser()
    config.read(file_path)
    time_columns = [config.get('TIME_COLUMNS', key) for key in config.options('TIME_COLUMNS')]
    return time_columns

# Load data
# Load data
def load_and_prepare_data(filepath: str, time_columns, custom_dict=None, **kwargs) -> pd.DataFrame:
    try:
        # Load the JSON data
        dfall = pd.read_json(filepath, **kwargs)


        # Parse 'data' and 'esp' columns if they exist and contain JSON
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

        print(f"Custom dict: {custom_dict}")
        print(f"Time columns: {time_columns}")
        print(dfall.columns.tolist())

        # If a custom dictionary is provided, select the relevant columns
        if custom_dict:
            relevant_columns = [val for val in custom_dict.values() if val in dfall.columns]
            df = dfall[relevant_columns]
        else:
            df = dfall

        # Convert time columns to datetime format
        for column in time_columns:
            if column in df.columns:
                df = df.copy()
                df[column] = pd.to_datetime(df[column], errors='coerce')
        

        
        logging.info(f"Data from {filepath} JSON has been read successfully.")
        
        # Print the column names
        print("Column names in the DataFrame:")
        print(df.columns.tolist())
        
    except FileNotFoundError:
        logging.error(f"Data file {filepath} not found.")
        raise
    except ValueError as e:
        logging.error(f"Error loading data file {filepath}: {e}")
        raise
    
    # Additional data preparation steps can be added here as per requirement
    return df

# Data processing
def prepare_data_for_plotting(df: pd.DataFrame, atribute, launch_datetime: datetime.datetime) -> pd.DataFrame:
    print(f"Dataframe\n {df}")
    df['epoch'] = pd.to_datetime(df['epoch'])
    

    launchtime = launch_datetime.timestamp()
    launch_datetime = pd.to_datetime(launch_datetime)
    firstRuntime = df['log_counter'].iloc[0]
    launchtime = pd.to_datetime(launchtime)
    firstRuntime = pd.to_datetime(firstRuntime)

    df['log_counter'] = df['log_counter'] - firstRuntime


    # Now df['TimeOfFlight'] can be computed as:
    df['TimeOfFlight'] = launchtime + df['log_counter']
    df['TimeOfFlight'] = launchtime + pd.to_timedelta(df['log_counter']) - firstRuntime
    
    # Additional data calculations specific to plotting
    # if attribute == 'temperature':
    #     df['logbmp388Temp'] = 2**(np.log2(df['bmp388Temp']))
    #     df['logbme280Temp'] = 2**(np.log2(df['bme280Temp']))
    #     df['logmcp9808Temp'] = 2**(np.log2(df['mcp9808Temp']))
    df.index = launch_datetime + df['TimeOfFlight']
    return df

def prepare_plot_elements(df: pd.DataFrame, attribute, valuevars) -> pd.DataFrame:
    df[valuevars]=df[valuevars].replace('None', np.nan) #.astype(float) 
    dfAlt = pd.melt(df, id_vars='log_counter', value_vars=valuevars)
    
    # Additional plot preparation steps
    
    return dfAlt

def configure_plot_appearance(ax, x0, x1):
    ax.axvspan(x0, x1, color='#66DDF4', alpha=0.5)
    xlim = ax.get_xlim()
    ax.set_xlim(xlim)
    
    # ... other appearance configurations
    
    ax.set_xlabel('Time of Flight [s]', fontsize=14)
    ax.set_ylabel('Temperature [°C]', fontsize=14)
    return ax

# Plotting Temperature Graphs
def create_plot(dfAlt: pd.DataFrame):
    """
    Create the temperature plot using the provided data.
    
    Parameters:
        dfAlt (DataFrame): The melted dataframe to be plotted.
    
    Returns:
        ax: The plot's axis object for further customization.
    """
    sns.set_palette(sns.color_palette("RdPu_r", n_colors=4))
    sns.despine(top=True, offset=40, trim=True)
    ax = sns.lineplot(x='log_counter', y='value', hue='variable', data=dfAlt)
    
    return ax

def customize_plot(ax, x0: float, x1: float, figure_size: tuple,
                   title: str, xlabel: str, ylabel: str,
                   label_font_size: int, title_font_size: int,
                   line_styles: dict):
    """
    Customize the appearance of the plot.
    
    Parameters:
        ax: The plot's axis object.
        x0 (float), x1 (float): The start and end of the x-axis span.
        figure_size (tuple): The size of the figure (width, height).
        title (str): Title of the plot.
        xlabel (str), ylabel (str): Labels for the x and y axes.
        label_font_size (int): Font size of the labels.
        title_font_size (int): Font size of the title.
        line_styles (dict): Dictionary containing line style configurations.
    """
    ax.axvspan(x0, x1, color='#66DDF4', alpha=0.5)
    ax.set_xlabel(xlabel, fontsize=label_font_size)
    ax.set_ylabel(ylabel, fontsize=label_font_size)
    ax.set_title(title, fontsize=title_font_size)
    ax.figure.set_size_inches(*figure_size)

    # Apply line styles (optional, example assumes 'line' and 'dash' style types)
    if line_styles:
        for line, style in zip(ax.lines, line_styles.values()):
            if style == "line":
                line.set_linestyle("-")
            elif style == "dash":
                line.set_linestyle("--")
            # Additional styles can be added as per requirement

def display_plot():
    """
    Display the plot to the screen.
    """
    plt.show()

def save_plot(file_path: str, file_format: str, dpi: int):
    """
    Save the plot to a file.
    
    Parameters:
        file_path (str): The path where the plot will be saved.
        file_format (str): Format of the output plot (e.g., 'png', 'pdf').
        dpi (int): Dots per inch (resolution) of the output plot.
    """

    plt.savefig(file_path, format=file_format, dpi=dpi)

def clean_column(df, column_name):
    df[column_name] = df[column_name].replace('None', np.nan).astype(float)
    return df

def plot_coordinates_on_map(coordinates_df, map_file="map.html"):
    """
    Plot GPS coordinates on a map.
    
    Parameters:
        coordinates_df (pd.DataFrame): DataFrame containing latitude and longitude coordinates.
        map_file (str): Name of the HTML file to save the map.
    """
    # Assuming the dataframe has 'latitude' and 'longitude' columns
    if 'latitude' not in coordinates_df.columns or 'longitude' not in coordinates_df.columns:
        raise ValueError("Dataframe must contain 'latitude' and 'longitude' columns.")
    
    # Create a base map
    m = folium.Map(
        location=[coordinates_df['latitude'].mean(), coordinates_df['longitude'].mean()], 
        zoom_start=13
    )

    # Add points to the map
    for _, row in coordinates_df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            # popup=row['name']  # if you have a name or other info you'd like to display on click
        ).add_to(m)
    
    # Save the map as an HTML file
    m.save(map_file)
    logging.info(f"Map saved as {map_file}")

# Main script
if __name__ == "__main__":
    prop = setup_plotting()

    config_params = read_configuration('config_base.ini')

    attributes = ["temperature", "pressure", "humidity", "altitude", "uv"]

    file_name = config_params['file_name']

    # Extract category-wise column names
    column_categories = config_params['column_categories'] 
    launch_time_params = config_params['launch_time']
    launch_datetime = datetime.datetime.fromtimestamp(launch_time_params)
    time_columns = get_time_columns_from_config()
    df_gps = load_and_prepare_data(file_name, time_columns, column_categories['position'])

    for attribute in attributes:
        time_columns = get_time_columns_from_config()
        df = load_and_prepare_data(file_name, time_columns, column_categories[attribute])

        df = prepare_data_for_plotting(df, attribute, launch_datetime)
        x0, x1 = config_params['plot']['x0'], config_params['plot']['x1'] 

        if attribute in column_categories:
            value_vars = [v for k,v in column_categories[attribute].items()]  
          
        dfAlt = prepare_plot_elements(df, attribute, value_vars)


        if basic_data_checks(df) and pre_processing_checks(df, dfAlt, value_vars):
            logging.info("All checks passed, proceed to plotting.")
        else:
            logging.warning("Checks failed. Review warnings and adjust data/pre-processing.")
        
        ax = create_plot(dfAlt)
        # if attribute=='altitude':
        #     ax.invert_yaxis()

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
        
        # Pass new parameters to customize_plot
        customize_plot(ax, x0, x1, figure_size, title, xlabel, ylabel, label_font_size, title_font_size, line_styles)
        
        display_plot()
        
        # To save the plot using parameters from [PLOT_CONFIG]
        file_format = plot_config['file_format']
        dpi = plot_config['dpi']    
        dynamic_path = get_dynamic_path(config_params['output']['plot_path'], launch_datetime)
        save_plot(dynamic_path, file_format, dpi)

    try:
        df_gps['latitude'] = pd.to_numeric(df_gps['latitude'], errors='coerce') / 100
        df_gps['longitude'] = pd.to_numeric(df_gps['longitude'], errors='coerce') /100
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")

    df_gpsc = df_gps.replace({"None": None}, inplace=True)
    df_gpsc = df_gps[(df_gps['latitude'].notna()) & (df_gps['longitude'].notna())]
    df_gpsc.reset_index(drop=True, inplace=True)
    plot_coordinates_on_map(df_gpsc, "my_map.html")