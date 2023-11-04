import requests
import json
import os

def fetch_usgs_data(latitude, longitude, code,riskCategory, siteClass, folder_path):
    
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


if __name__ == '__main__':
    folder_path = os.path.dirname(os.path.abspath(__file__))
    code = 'asce7-22'
    riskCategory = 'III'
    siteClass = 'D'
    fetch_usgs_data(40.7128, -74.0060, code, riskCategory,siteClass, folder_path)