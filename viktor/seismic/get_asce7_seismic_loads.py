import requests
import json
import os
import numpy as np

def fetch_usgs_data(latitude, longitude, code,riskCategory, siteClass):
    
    if code.startswith('asce7'):
        url = f'https://earthquake.usgs.gov/ws/designmaps/{code}.json?latitude={latitude}&longitude={longitude}&riskCategory={riskCategory}&siteClass={siteClass}&title=Example'
    elif code.startswith('asce41'):
        url = f'https://earthquake.usgs.gov/ws/designmaps/{code}.json?latitude={latitude}&longitude={longitude}&siteClass={siteClass}&title=Example'
    else:
        print('Invalid code')
        return

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        multi_period_design_spectrum = None
        multi_period_mce_earthquake = None

        if code == 'asce7-22':
            multi_period_design_spectrum = data['response']['data']['multiPeriodDesignSpectrum']
            multi_period_mce_earthquake = data['response']['data']['multiPeriodMCErSpectrum']

        two_period_design_spectrum = data['response']['data']['twoPeriodDesignSpectrum']
        two_period_mce_spectrum = data['response']['data']['twoPeriodMCErSpectrum']

        file_path = os.path.join(folder_path, 'asce7_seismic_loads.json')
        import pandas as pd

        # convert multi_period_design_spectrum to a pandas dataframe
        
        multiperiod_design_spectrum_df = pd.DataFrame(multi_period_design_spectrum, columns=['periods', 'ordinates'])
        multiperiod_design_spectrum_df.columns = ['period', 'acceleration']

        multiperiod_mce_spectrum_df = pd.DataFrame(multi_period_mce_earthquake, columns=['periods', 'ordinates'])
        multiperiod_mce_spectrum_df.columns = ['period', 'acceleration']

        two_period_design_spectrum_df = pd.DataFrame(two_period_design_spectrum, columns=['periods', 'ordinates'])
        two_period_design_spectrum_df.columns = ['period', 'acceleration']

        two_period_mce_spectrum_df = pd.DataFrame(two_period_mce_spectrum, columns=['periods', 'ordinates'])
        two_period_mce_spectrum_df.columns = ['period', 'acceleration']


        return multiperiod_design_spectrum_df, multiperiod_mce_spectrum_df, two_period_design_spectrum_df, two_period_mce_spectrum_df          
    else:
        print('Error accessing website')

def calculate_floor_mass(story_floor_area, SD, SW, LL):
    floor_mass = 0
    floor_mass = (SD + SW + LL)*story_floor_area
    return floor_mass

def get_seismic_force(story_elevations, story_floor_area, SD, SW, LL, R, latitude, longitude, code, riskCategory,siteClass, spectrum_type=None, T_optional = None):
    
    total_height = story_elevations[-1] - story_elevations[0]
    T = 0.016*(total_height**0.7)

    multiperiod_design_spectrum_df, multiperiod_mce_spectrum_df, two_period_design_spectrum_df, two_period_mce_spectrum_df = fetch_usgs_data(latitude, longitude, code, riskCategory,siteClass)
    num_stories = len(story_floor_area)

    if spectrum_type is None:
        spectrum_df = two_period_mce_spectrum_df
    elif spectrum_type == 'multi_period_design_spectrum':
        spectrum_df = multiperiod_design_spectrum_df
    elif spectrum_type == 'multi_period_mce_spectrum':
        spectrum_df = multiperiod_mce_spectrum_df
    elif spectrum_type == 'two_period_design_spectrum':
        spectrum_df = two_period_design_spectrum_df
    elif spectrum_type == 'two_period_mce_spectrum':
        spectrum_df = two_period_mce_spectrum_df

    if T_optional is not None:
        T = T_optional

    if T < 0.5:
        k=1
    elif T>2.5:
        k=2
    else:
        k=(2-1)/(2.5-0.5)*(T-0.5)+1 
    
    floor_masses = []
    for area in story_floor_area:
        floor_mass = calculate_floor_mass(area, SD, SW, LL)
        floor_masses.append(floor_mass)

    total_mass = sum(floor_masses)

    # interpolate T in spectrum_df to obtain acceleration
    acceleration = np.interp(T, spectrum_df['period'], spectrum_df['acceleration'])
    base_shear = acceleration*total_mass/R

    # Distribute the load among all the stories
    story_seismic_loads = []
    cumulative_sum = 0  # Initialize the cumulative sum

    for i in range(num_stories):
        cumulative_sum += floor_masses[i] * story_elevations[i]**k


    for i in range(num_stories):
        
        cvx = floor_masses[i] * story_elevations[i]**k / cumulative_sum
        story_load = cvx * base_shear
        story_seismic_loads.append(story_load)

    return story_seismic_loads

if __name__ == '__main__':
    folder_path = os.path.dirname(os.path.abspath(__file__))

    story_elevations = [0, 12, 24, 36, 48] #ft
    story_floor_area = [10000, 10000, 10000, 10000, 10000] #ft2
    SD = 20 # psf
    SW = 70 # psf
    LL = 100 # psf
    R = 3
    latitude = 40.7128
    longitude = -74.0060
    code = 'asce7-22'
    riskCategory = 'III'
    siteClass = 'D'
    get_seismic_force(story_elevations, story_floor_area, SD, SW, LL, R, 
                      latitude, longitude, code, riskCategory, siteClass, 
                      spectrum_type=None, T_optional = None)