# Hydroperiod-Calculator

The Hydroperiod is determined by processing a series of water masks estimated for dates within the period between the start and end dates of the hydroperiod. This computation involves applying a designated interpolation method: when assessing two dates separated by n days, the presence of water is examined. If a pixel is submerged on both dates, it is assumed to be inundated for the full n days; otherwise, it is considered inundated for n/2 days. The cumulative count of inundation days is subsequently calculated by aggregating the water masks throughout the specified period.

The input files should be binary inundation maps in 'tif' or 'tiff' format. In these maps, the pixel values should adhere to the following convention: a value of 0 represents non-inundated pixels, while a value of 1 represents inundated pixels.

execute: 'python hydroperiod_calculator.py' and enter the inputs' full directory. The outputs will be saved in the same path.
