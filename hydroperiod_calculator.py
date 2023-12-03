import os
from osgeo import gdal
from datetime import datetime
import numpy as np
from PIL import Image
import seaborn as sns

class HydroperiodCalculator:
    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.tif_files = {}
        self.random_band = None

    def read_tif_files_gdal(self):
        '''
        The read_tif_files_gdal function reads GeoTIFF files from a specified directory, 
        validates date formats, and stores the corresponding data arrays in a dictionary. 
        The function utilizes the GDAL library for file handling and NumPy for array manipulation. 
        Any files with invalid date formats are ignored, and errors during file reading are reported. 
        The last opened GDAL dataset is returned (though, it's advisable to handle the returned 
        dataset with caution as it may be None in case of errors).
        '''

        self.directory_path = self.directory_path.replace("\\", "/")
        files = os.listdir(self.directory_path)

        for file in files:
            if file.lower().endswith(('.tif', '.tiff')):
                date_str = file.split('.')[0]
                try:
                    datetime.strptime(date_str, '%Y_%m_%d')
                except ValueError:
                    print(f"Ignored file {file} due to invalid date format.")
                    continue
                try:
                    tif_path = os.path.join(self.directory_path, file)
                    dataset = gdal.Open(tif_path)
                    tif_array = dataset.ReadAsArray().astype(np.float64)
                    self.tif_files[date_str] = tif_array
                except Exception as e:
                    print(f"Error reading file {file}: {e}")

        return dataset

    def check_array_shapes(self):
        '''
        Checks if the arrays stored in self.tif_files have consistent shapes.
        Raises a ValueError if arrays have different shapes, providing details on the shapes.
        '''
        shapes = [arr.shape for arr in self.tif_files.values()]

        if len(set(shapes)) != 1:
            print("Error: Arrays have different shapes.")
            print("Shapes:", shapes)
            raise ValueError("Inconsistent array shapes. Stopping the process.")
        
        return None

    def extract_days_between_and_arrays(self):
        '''
        Extracts the sorted dates from self.tif_files keys and computes days between each consecutive pair. 
        Returns a tuple containing a list of days between dates and a list of arrays stored in self.tif_files.
        '''
        dates = sorted([datetime.strptime(date, '%Y_%m_%d') for date in self.tif_files.keys()])
        days_between = [0]

        for i in range(len(dates) - 1):
            days_between.append((dates[i+1] - dates[i]).days)

        arrays = [value for value in self.tif_files.values()]

        return days_between, arrays

    def hydroperiod_calculation(self, days_between, arrays):
        '''
        Calculates hydroperiods based on arrays and days between consecutive dates.
        Args:
        - days_between (list): List of days between consecutive dates.
        - arrays (list): List of arrays representing inundation states for each date.
        Returns:
        - final_hydroperiod (numpy.ndarray): Hydroperiod array calculated by summing inundation durations.
        '''
        x, y = arrays[0].shape
        all_hydroperiods = []

        for i in range(len(arrays) - 1):
            hydroperiod_between_two_dates = np.full((x, y), -1)
            sum_of_arrays = arrays[i] + arrays[i + 1]
            hydroperiod_between_two_dates[np.where(sum_of_arrays == 0)] = 0
            hydroperiod_between_two_dates[np.where(sum_of_arrays == 1)] = int(days_between[i + 1] / 2)
            hydroperiod_between_two_dates[np.where(sum_of_arrays == 2)] = days_between[i + 1]
            all_hydroperiods.append(hydroperiod_between_two_dates)

        final_hydroperiod = np.full((x, y), 0)

        for hydroperiod in all_hydroperiods:
            final_hydroperiod += hydroperiod

        final_hydroperiod[final_hydroperiod < 0] = -1

        return final_hydroperiod

    def save_geotiff(self, final_hydroperiod, random_band, directory_path):
        '''
        Saves the final hydroperiod array as a GeoTIFF file.
        Args:
        - final_hydroperiod (numpy.ndarray): Hydroperiod array to be saved.
        - random_band (gdal.Dataset): Random GDAL band for geotransformation and projection information.
        - directory_path (str): Directory path for saving the GeoTIFF file.
        '''
        x, y = final_hydroperiod.shape

        driver = gdal.GetDriverByName('GTiff')
        dataset = driver.Create(directory_path + "/output/hydroperiod_map.tif", y, x, 1, gdal.GDT_Float64)
        dataset.GetRasterBand(1).WriteArray(final_hydroperiod)
        dataset.GetRasterBand(1).SetNoDataValue(-1)

        if random_band is not None:
            geotrans = random_band.GetGeoTransform()
            proj = random_band.GetProjection()
            dataset.SetGeoTransform(geotrans)
            dataset.SetProjection(proj)

        dataset = None


    def create_RGB(self, final_hydroperiod, directory_path):
        '''
        Creates an RGB visualization of the hydroperiod array and saves it as a PNG image.
        Args:
        - final_hydroperiod (numpy.ndarray): Hydroperiod array to be visualized.
        - directory_path (str): Directory path for saving the RGB visualization PNG image.
        '''
        final_hydroperiod += 1

        normalized_data = (final_hydroperiod - np.min(final_hydroperiod)) / (np.max(final_hydroperiod) - np.min(final_hydroperiod))
        cmap = sns.color_palette("crest", as_cmap=True)
        rgba_data = (cmap(normalized_data) * 255).astype(np.uint8)

        rgba_data[normalized_data == 0] = [255, 255, 255, 255]

        image = Image.fromarray(rgba_data, 'RGBA')
        image.save(directory_path + '/output/hydroperiod_visualization.png')


if __name__ == "__main__":
    print("The input files should be binary inundation maps in 'tif' or 'tiff' format. In these maps, the pixel values should adhere to the following convention: a value of 0 represents non-inundated pixels, while a value of 1 represents inundated pixels")
    directory_path = input("Enter the inputs' full path here:")
    
    hydro_calc = HydroperiodCalculator(directory_path)
    hydro_calc.read_tif_files_gdal()
    hydro_calc.check_array_shapes()
    
    days_between, arrays = hydro_calc.extract_days_between_and_arrays()
    final_hydroperiod = hydro_calc.hydroperiod_calculation(days_between, arrays)
    
    try:
        os.mkdir(directory_path + '/output')
    except FileExistsError:
        print("Output folder already exists")
    
    hydro_calc.save_geotiff(final_hydroperiod, hydro_calc.random_band, directory_path)
    hydro_calc.create_RGB(final_hydroperiod, directory_path)