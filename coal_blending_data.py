import numpy as np
import pandas as pd
from gekko import GEKKO
from itertools import product 

pd.options.display.float_format = "{:,.2f}".format
pd.options.display.max_columns = None
pd.options.display.expand_frame_repr = False

# Fill in coal specification
supplier = ['Banpu', 'Logplus', 'Mac', 'Tiger', 'AVRA', 'Spot2', 'Spot3', 'Spot4', 'Spot5']

# Coal specification
total_moisture = [28.66, 17.81, 22.51, 20.82, 24.74] + [23.00]*4
inherent_moisture = [11.40, 12.70, 12.91, 12.81, 15.31] + [10.00]*4

ad_basis = [True]*5 + [False]*4
ash_content = [4.96, 5.98, 6.80, 4.27, 4.83] + [6.00]*4
volatile_matter = [42.98, 40.42, 40.78, 41.43, 39.92] + [36.00]*4
fixed_carbon = [40.65, 40.90, 39.51, 41.49, 39.94] + [37.00]*4
sulphur_content = [0.41, 0.49, 0.45, 0.16, 0.32] + [0.50]*4
gross_calorific_value = [5918, 6167.25, 5794, 5962, 5634] + [5400, 5300, 5600, 5500]

# Ash Analysis
SiO2 = [45.42, 35.80, 42.80, 28.36, 47.30] + [40.82]*4
Al2O3 = [14.18, 20.63, 17.32, 17.38, 17.60] + [13.57]*4
Fe2O3 = [14.58, 10.14, 11.41, 9.79, 11.20] + [11.22]*4
CaO = [7.43, 16.31, 9.23, 19.68, 9.00] + [16.09]*4
MgO = [5.65, 3.88, 3.31, 5.32, 4.97] + [2.53]*4
Na2O = [0.99, 1.81, 1.39, 8.70, 0.68] + [2.24]*4
K2O = [1.24, 1.32, 1.24, 1.03, 1.10] + [0.76]*4
TiO2 = [0.56, 0.79, 0.71, 0.70, 0.92] + [0.55]*4
Mn3O4 = [0.24, 0.08, 0.14, 0.04, 0.08] + [0.06]*4
SO3 = [7.49, 8.46, 11.92, 6.70, 0.61] + [11.05]*4
P2O5 = [0.16, 0.25, 0.43, 0.51, 0.45] + [0.16]*4

df_coal_spec = pd.DataFrame({
    'Supplier': supplier,
    'Total Moisture (%)': total_moisture,
    'Inherent Moisture (%)': inherent_moisture,
})
df_coal_spec.set_index('Supplier', inplace=True)

AR_conversion_ratio = (100 - df_coal_spec['Total Moisture (%)']) / (100 - df_coal_spec['Inherent Moisture (%)'])
for i in range(len(df_coal_spec)):
    ratio = AR_conversion_ratio[i] if ad_basis[i] else 1
    df_coal_spec.loc[df_coal_spec.index[i], ['Ash Content (%)']] = ash_content[i] * ratio
    df_coal_spec.loc[df_coal_spec.index[i], ['Volatile Matter (%)']] = volatile_matter[i] * ratio
    df_coal_spec.loc[df_coal_spec.index[i], ['Fixed Carbon (%)']] = fixed_carbon[i] * ratio
    df_coal_spec.loc[df_coal_spec.index[i], ['Sulphur Content (%)']] = sulphur_content[i] * ratio
    df_coal_spec.loc[df_coal_spec.index[i], ['Gross Calorific Value (kcal/kg)']] = gross_calorific_value[i] * ratio

df_coal_spec['SiO2'] = SiO2
df_coal_spec['Al2O3'] = Al2O3
df_coal_spec['Fe2O3'] = Fe2O3
df_coal_spec['CaO'] = CaO
df_coal_spec['MgO'] = MgO
df_coal_spec['Na2O'] = Na2O
df_coal_spec['K2O'] = K2O
df_coal_spec['TiO2'] = TiO2
df_coal_spec['Mn3O4'] = Mn3O4
df_coal_spec['SO3'] = SO3
df_coal_spec['P2O5'] = P2O5

df_coal_spec['%S dry'] = df_coal_spec['Sulphur Content (%)'] * 100/(100 - df_coal_spec['Total Moisture (%)'])
df_coal_spec['B/A'] = df_coal_spec[['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']].sum(axis=1) / df_coal_spec[['SiO2', 'Al2O3', 'TiO2']].sum(axis=1)
df_coal_spec['Slacking Index'] = df_coal_spec['%S dry'] * df_coal_spec['B/A']
df_coal_spec['Fouling Index'] = df_coal_spec['Na2O'] * df_coal_spec['B/A']

date_start = '2020-06-16'
date_stop = '2020-08-31'

# ['Banpu', 'Logplus', 'Mac', 'Tiger', 'AVRA', 'Spot2', 'Spot3', 'Spot4', 'Spot5']
initial_stock = [30811, 36262, 0, 7000, 33158, 0, 0, 0, 0]
dead_stock = 10159.7833420158 + 42402

# Case Oct
incoming_stock = [
    ['2020-06-17', 'Tiger', 20000],
    ['2020-06-18', 'Tiger', 20000],
    ['2020-06-19', 'Tiger', 15000],
    ['2020-07-03', 'Banpu', 54000],
    ['2020-07-27', 'Logplus', 53000],
    ['2020-08-10', 'Tiger', 53000],
    ['2020-08-27', 'Mac', 53000],
    ['2020-09-11', 'Logplus', 53000],
    ['2020-09-24', 'Banpu', 52000],
    ['2020-10-07', 'Logplus', 53000],
    ['2020-10-23', 'Banpu', 52000],
    ['2020-11-09', 'Tiger', 53000],
    ['2020-11-22', 'Banpu', 52000],
    ['2020-12-08', 'Spot2', 52000],
    ['2020-12-24', 'Spot3', 52000],
    ['2021-01-09', 'Banpu', 52000],
    ['2021-01-24', 'Logplus', 52000],
]

coal_adjust_price = [3267, 1499, 2373, 2179, 2500, 2600, 2700, 2800, 2900]

# print(df_coal_spec.T)