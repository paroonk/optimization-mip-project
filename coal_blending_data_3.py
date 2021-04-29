import numpy as np
import pandas as pd
from pyomo.environ import *
from itertools import product

pd.options.display.float_format = "{:,.2f}".format
pd.options.display.max_columns = None
pd.options.display.expand_frame_repr = False

data_df = pd.read_excel('coal_data.xlsx')

# Convert AD to AR
data_df.loc[data_df['AD Basis'] == True, 'AR Ratio'] = (100 - data_df['Total Moisture (%)']) / (100 - data_df['Inherent Moisture (%)'])
data_df.loc[data_df['AD Basis'] == False, 'AR Ratio'] = 1
AR_ratio = pd.DataFrame([(100 - data_df['Total Moisture (%)'][i]) / (100 - data_df['Inherent Moisture (%)'][i]) if data_df['AD Basis'][i] else 1] for i in data_df.index)
data_df['Ash Content (%)'] = data_df['Ash Content (%)'] * data_df['AR Ratio']
data_df['Volatile Matter (%)'] = data_df['Volatile Matter (%)'] * data_df['AR Ratio']
data_df['Fixed Carbon (%)'] = data_df['Fixed Carbon (%)'] * data_df['AR Ratio']
data_df['Sulphur Content (%)'] = data_df['Sulphur Content (%)'] * data_df['AR Ratio']
data_df['Gross Calorific Value (kcal/kg)'] = data_df['Gross Calorific Value (kcal/kg)'] * data_df['AR Ratio']
data_df.drop(['AD Basis', 'AR Ratio'], axis=1, inplace=True)

# Calculate %S dry, B/A, Slacking, Fouling index
data_df['%S dry'] = data_df['Sulphur Content (%)'] * 100/(100 - data_df['Total Moisture (%)'])
data_df['B/A'] = data_df[['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']].sum(axis=1) / data_df[['SiO2', 'Al2O3', 'TiO2']].sum(axis=1)
data_df['Slacking Index'] = data_df['%S dry'] * data_df['B/A']
data_df['Fouling Index'] = data_df['Na2O'] * data_df['B/A']

data_df = data_df[data_df['Supplier'] != 'Dummy']
data_df.set_index('Supplier', inplace=True)
# print(data_df.T)

cfb12_LHV = 305
cfb12_HHV_LHV = 1.065
cfb12_UOF =  0.0
cfb3_LHV = 303
cfb3_HHV_LHV = 1.065
cfb3_UOF =  0.0

dead_stock = 52561.78

# Case Oct
incoming_stock = {
    '2020-06-17': ('Tiger', 20000),
    '2020-06-18': ('Tiger', 20000),
    '2020-06-19': ('Tiger', 15000),
    '2020-07-03': ('Banpu', 54000),
    '2020-07-27': ('Logplus', 53000),
    '2020-08-10': ('Tiger', 53000),
    '2020-08-27': ('Mac', 53000),
    '2020-09-11': ('Logplus', 53000),
    '2020-09-24': ('Banpu', 52000),
    '2020-10-07': ('Logplus', 53000),
    '2020-10-23': ('Banpu', 52000),
    '2020-11-09': ('Tiger', 53000),
    '2020-11-22': ('Banpu', 52000),
    '2020-12-08': ('Spot2', 52000),
    '2020-12-24': ('Spot3', 52000),
    '2021-01-09': ('Banpu', 52000),
    '2021-01-24': ('Logplus', 52000),
}

cfb12_limit = {
    '%S': (0.6 , 0.1),
    '%Ash': (7.5, 4.0),
    'GCV': (5600, 5000),
    'Fe2O3': (12.0, 0.0),
    'Na2O': (2.5, 0.0),
    'Slacking': (0.6, 0.0),
    'Fouling': (2.0, 0.0),
}

cfb3_limit = {
    '%S': (0.6, 0.1),
    '%Ash': (7.5, 4.0),
    'GCV': (5200, 4900),
    'Fe2O3': (12.0, 0.0),
    'Na2O': (2.5, 0.0),
    'Slacking': (0.6, 0.0),
    'Fouling': (2.0, 0.0),
}