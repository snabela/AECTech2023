import requests
import json
import os
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import csv

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
        
        seismic_data = {
            'sds': data['response']['data']['sds'],
            'sd1': data['response']['data']['sd1'],
            'ss': data['response']['data']['ss'],
            's1': data['response']['data']['s1'],
            'short_period': data['response']['data']['ts'],
            'long_period': data['response']['data']['tl']
        }

        # Write data to CSV file

        # with open('seismic_data.csv', mode='w', newline='') as file:
        #     writer = csv.writer(file)
        #     writer.writerow(['seismic_parameter', 'value'])
        #     writer.writerow(['sds', sds])
        #     writer.writerow(['sd1', sd1])
        #     writer.writerow(['ss', ss])
        #     writer.writerow(['s1', s1])
        #     writer.writerow(['short_period', short_period])
        #     writer.writerow(['long_period', long_period])

        multi_period_design_spectrum = None
        multi_period_mce_earthquake = None

        if code == 'asce7-22':
            multi_period_design_spectrum = data['response']['data']['multiPeriodDesignSpectrum']
            multi_period_mce_earthquake = data['response']['data']['multiPeriodMCErSpectrum']

        two_period_design_spectrum = data['response']['data']['twoPeriodDesignSpectrum']
        two_period_mce_spectrum = data['response']['data']['twoPeriodMCErSpectrum']


        # convert multi_period_design_spectrum to a pandas dataframe
        
        multiperiod_design_spectrum_df = pd.DataFrame(multi_period_design_spectrum, columns=['periods', 'ordinates'])
        multiperiod_design_spectrum_df.columns = ['period', 'acceleration']

        multiperiod_mce_spectrum_df = pd.DataFrame(multi_period_mce_earthquake, columns=['periods', 'ordinates'])
        multiperiod_mce_spectrum_df.columns = ['period', 'acceleration']

        two_period_design_spectrum_df = pd.DataFrame(two_period_design_spectrum, columns=['periods', 'ordinates'])
        two_period_design_spectrum_df.columns = ['period', 'acceleration']

        two_period_mce_spectrum_df = pd.DataFrame(two_period_mce_spectrum, columns=['periods', 'ordinates'])
        two_period_mce_spectrum_df.columns = ['period', 'acceleration']


        return multiperiod_design_spectrum_df, multiperiod_mce_spectrum_df, two_period_design_spectrum_df, two_period_mce_spectrum_df, seismic_data
    else:
        print('Error accessing website')

def calculate_floor_mass(story_floor_area, SD, LL):
    floor_mass = 0
    floor_mass = (SD + LL)*story_floor_area
    return floor_mass

def get_seismic_force(story_data, SD, LL, R, latitude, longitude, code, riskCategory,siteClass, spectrum_type=None, T_optional = None):
    '''
    Parameters for get_seismic_force function:
    story_data: Tuple of story elevations in ft from top floor to bottom floor. do not include ground floor elevation
                and of story floor areas in ft2
    SD: design dead load in psf assumed the same for each floor
    self weight load in psf assumed the same for each floor
    LL: design live load in psf assumed the same for each floor
    R: seismic response coefficient
    latitude: latitude of the site
    longitude: longitude of the site
    code: code to be used for seismic design
    riskCategory: risk category of the building
    siteClass: site class of the building
    spectrum_type: type of spectrum to be used for seismic design
    T_optional: optional parameter to specify the period of the structure i.e. from ETABS or SAP2000

    Output of get_seismic_force function:
    story_seismic_loads: list of seismic loads for each story in kips
    seimsic_shear_story_plot: list of shear story values for plotting
    seismic_shear_elevation_plot: list of shear elevation values for plotting
    seismic_data: dictionary of seismic parameters from USGS (sds, sd1, ss, s1, short_period, long_period)
    '''
    story_elevations = []
    story_floor_area = []

    for story in story_data:
        story_elevations.append(story[0])
        story_floor_area.append(story[1])

    total_height = story_elevations[0] - story_elevations[-1]
    T = 0.016*(total_height**0.7)

    multiperiod_design_spectrum_df, multiperiod_mce_spectrum_df, two_period_design_spectrum_df, two_period_mce_spectrum_df, seismic_data = fetch_usgs_data(latitude, longitude, code, riskCategory,siteClass)

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
        floor_mass = calculate_floor_mass(area, SD, LL)
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

    current_shear_story = 0
    shear_story = []
    for i in range(num_stories):
        
        cvx = floor_masses[i] * story_elevations[i]**k / cumulative_sum
        story_load = cvx * base_shear
        story_seismic_loads.append(story_load)
        current_shear_story+=story_load
        shear_story.append(current_shear_story)
    
    # Initialize lists to store shear story and elevation data
    seimsic_shear_story_plot = []
    seismic_shear_elevation_plot = []
    story_elevations.append(0)
    for i in range(len(shear_story)):
        seimsic_shear_story_plot.append(shear_story[i])
        seismic_shear_elevation_plot.append(story_elevations[i])
  
        if i < (len(story_elevations) - 1):
            seimsic_shear_story_plot.append(shear_story[i] )
            seismic_shear_elevation_plot.append(story_elevations[i+1])


    # Plot the data
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=seimsic_shear_story_plot, y=seismic_shear_elevation_plot, mode='lines+markers'))
    # fig.update_layout(title='Shear Story vs Elevation', xaxis_title='Shear Story (kips)', yaxis_title='Elevation (ft)', xaxis=dict(range=[0, max(shear_story)]), yaxis=dict(range=[0, max(story_elevations)]))
    # fig.show()
    
    story_seismic_loads_dict = {}
    for i in range(len(story_seismic_loads)):
        story_seismic_loads_dict[f"Story {i+1}"] = story_seismic_loads[i]
    
    return story_seismic_loads_dict, seimsic_shear_story_plot, seismic_shear_elevation_plot, seismic_data

if __name__ == '__main__':
    story_elevations = [48, 36, 24, 12] #ft
    story_floor_area = [10000, 10000, 10000, 10000] #ft2

    story_data = [[story_elevations[i], story_floor_area[i]] for i in range(len(story_elevations))]
    SD = 20 # psf
    LL = 100 # psf
    R = 3
    latitude = 40.7128
    longitude = -74.0060
    code = 'asce7-22'
    riskCategory = 'III'
    siteClass = 'D'
    get_seismic_force(story_data, SD, LL, R, 
                      latitude, longitude, code, riskCategory, siteClass, 
                      spectrum_type=None, T_optional = None)