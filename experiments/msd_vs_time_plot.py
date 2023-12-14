# File: msd_vs_time_plot.py

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
import re
import glob
import io
import datetime


SOURCE_PATH = r'C:\git\rouse_data\mc009'
DEST_PATH = r'C:\git\rouse_data\mc009\time-vs-msd'
DAT_FILE = "cm.dat"
TEXT_FILE_NAME = "curvature.txt"
HEADERS = 'tauMax, inner, outer, factor, res, curvature\n'
PATTERN = r'run\d+_inner(\d+)_outer(\d+)_factor(\d+)_residue(\d+)'
TAU_MAX = 100

def load_CM_positions(filename: str) -> np.ndarray:
    """Load times and positions from a file, skipping the first row (header)."""
    return np.loadtxt(filename, skiprows=1)

import numpy as np
def calculate_MSD(data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate Mean Square Displacement (tauR) for each data point in 3D.
    """

    # Generate a times array based on the length of the data
    times = np.arange(len(data))
    # Calculate displacements in x, y, and z directions
    displacements = np.diff(data, axis=0)

    # Calculate squared displacements for each dimension
    squared_displacements = displacements**2

    # Sum the squared displacements in all three dimensions to get total squared displacement
    total_squared_displacement = np.sum(squared_displacements, axis=1)

    # Calculate the Mean Squared Displacement (tauR) by cumulatively summing the total squared
    # displacements and dividing by the number of points at each step. np.arange(1, len(data))
    # generates numbers from 1 to len(data) - 1.
    MSD = np.cumsum(total_squared_displacement) / np.arange(1, len(data))

    MSD = np.sqrt(MSD)
    # Return the times array (excluding the first time point, as np.diff reduces the array length by one)
    # and the calculated tauR as a tuple
    return times[1:], MSD


def plot_msd_vs_time(times: np.ndarray, MSD: np.ndarray) -> io.BytesIO:
    """Plot tauR versus time on a log-log scale and save the figure to a BytesIO object."""
    if np.any(times <= 0) or np.any(MSD <= 0):
        print("Warning: Data contains non-positive values which cannot be log-scaled.")
        return None
    plt.figure()
    plt.scatter(times, MSD, marker='o')
    plt.xlabel('Time (s)')
    plt.ylabel('tauR')
    plt.title('tauR vs. Time (Log-Log Scale)')
    plt.grid(True)
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return img

def write_image_to_directory(img: io.BytesIO, directory: str, filename: str) -> None:
    """Write image data to a file in the specified directory_path."""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    with open(filepath, 'wb') as f:
        f.write(img.read())
    #end-of-with
#end-of-function


def clear_text_file(filepath: str) -> None:
    """Clear the contents of a text file."""
    if os.path.exists(filepath):
        with open(filepath, 'w') as file:
            file.write('')
        #end-of-with
    #end-of-if
#end-of-function


def get_directories(dir_path: str, pattern: str='run*_inner*_outer*_factor*_res*') -> list[str]:
    """This function retrieves all directories in the specified path that match a given pattern."""
    return glob.glob(os.path.join(dir_path, pattern))


def calculate_curvature(tau: np.ndarray, MSD: np.ndarray) -> np.ndarray:
    """Calculate curvature of tauR using UnivariateSpline."""
    if len(tau) < 4 or len(MSD) < 4:
        return np.array([])
    #end-of-if
    spl = UnivariateSpline(tau, MSD)
    spl_1d = spl.derivative(n=1)
    spl_2d = spl.derivative(n=2)
    curvature = np.abs(spl_2d(tau)) / (1 + spl_1d(tau)**2)**(3/2)
    return np.round(curvature, 3)
#end-of-function


def extract_values(input_string: str) -> tuple[int, int, int, int]:
    """Extract values from a formatted string."""
    try:
        match = re.search(r'run\d+_inner(\d+)_outer(\d+)_factor(\d+)_residue(\d+)', input_string)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
        else:
            raise ValueError("Input string does not match required format.")
        #end-of-if-else
    except ValueError as e:
        print(f"Error with directory_path {input_string}: {str(e)}")
    #end-of-try-except
#end-of-function


def write_curvature_to_textfile(directory: str, curvature_value: float, dest_path: str=DEST_PATH) -> None:
    """Write headers to the curvature_values.txt file if it doesn't exist or is empty, then write directory_path name, fileName, and curvature value to a text file."""
    # Create the directory_path if it doesn't exist
    os.makedirs(dest_path, exist_ok=True)
    text_file_path = os.path.join(dest_path, TEXT_FILE_NAME)
    # Write headers if the file doesn't exist or is empty
    if not os.path.exists(text_file_path) or os.path.getsize(text_file_path) == 0:
        with open(text_file_path, 'w') as f:
            f.write(HEADERS)
        #end-of-with
    #end-of-if
    # Obtain directory_path name
    directory_name = os.path.basename(directory)
    inner, outer, factor, res = extract_values(directory_name)
    # Prepare the line to be written
    line = f"{TAU_MAX}, {inner}, {outer}, {factor}, {res}, {curvature_value}\n"
    # Append the line to the text file
    with open(text_file_path, 'a') as f:
        f.write(line)
    #end-of-with
#end-of-function


def process_directories(source_path: str=SOURCE_PATH, dest_path: str=DEST_PATH, dat_file: str=DAT_FILE) -> None:
    """Process all directories in sourcePath, calculate tauR and curvature, and write results to dest_path."""
    clear_text_file(os.path.join(dest_path, TEXT_FILE_NAME))
    directories = get_directories(source_path)
    for directory in directories:
        filename = os.path.join(directory, dat_file)
        if os.path.isfile(filename):
            data = load_CM_positions(filename)
            times, MSD = calculate_MSD(data)
            times.sort()  # Ensure times are sorted
            img = plot_msd_vs_time(times, MSD)
            if img is not None:
                write_image_to_directory(img, dest_path, os.path.basename(directory) + '.png')
            curvature = calculate_curvature(times, MSD)
            avg_curvature = np.nan if curvature.size == 0 else np.mean(curvature)
            write_curvature_to_textfile(directory, avg_curvature, dest_path)
        else:
            print(f"File {filename} does not exist.")
        #end-of-if-else
    #end-of-for
#end-of-function


if __name__ == "__main__":
    process_directories()

