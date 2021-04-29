#@title <h3><b>←</b> Download data file from Onedrive
# !pip install plotly --upgrade

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import product, combinations
from functools import wraps
from time import process_time
from datetime import datetime, timedelta

def drop_prefix(self, prefix):
    self.columns = self.columns.str.replace('^{}'.format(prefix), '', regex=True)
    return self
pd.core.frame.DataFrame.drop_prefix = drop_prefix

def measure(func):
    @wraps(func)
    def _time_it(*args, **kwargs):
        start = int(round(process_time() * 1000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(process_time() * 1000)) - start
            print(
                f"Total execution time of {func.__name__}(): {end_ if end_ > 0 else 0} ms"
            )

    return _time_it

# %load_ext google.colab.data_table
pd.options.display.float_format = "{:,.2f}".format
# pd.options.display.max_columns = None
# pd.options.display.expand_frame_repr = False

#@title <h3><b>←</b> Setting

#@markdown ### Start/Stop Date
date_start = '2020-06-16' #@param {type:'date'}
date_stop = '2020-07-31' #@param {type:'date'}

#@markdown ### Coal Require Spec
#@markdown ##### CFB1&2
cfb12_LHV = 305 #@param {type:'number'}
cfb12_HHV_LHV = 1.065 #@param {type:'number'}
cfb12_UOF =  0.0 #@param {type:'number'}
#@markdown ##### CFB3
cfb3_LHV = 303 #@param {type:'number'}
cfb3_HHV_LHV = 1.065 #@param {type:'number'}
cfb3_UOF =  0.0 #@param {type:'number'}

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
    # 'GCV': (5600, 4900),
    'Fe2O3': (12.0, 0.0),
    'Na2O': (2.5, 0.0),
    'Slacking': (0.6, 0.0),
    'Fouling': (2.0, 0.0),
}

#@markdown ### Load Data
# input_url = 'https://glowgroup-my.sharepoint.com/:x:/g/personal/paroon_k_gpscgroup_com/EQhRaAcxEWVDssS8aI5VDk4BXE5xN0K-m7Gf8_1OrNiUsQ?rtime=6Ex3VAzt2Eg' #@param {type:"string"}
# output_dir = "coal_data.xlsx"

# split_url = input_url.rfind('?')
# converted_url = input_url[:split_url] + '?download=1'

# !wget -q -O "$output_dir" "$converted_url"

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
data_df.T


#@title <h3><b>←</b> Feasible Solution Search
def ratio_cal(data_df):
    ratio_aval = []
    for s1 in data_df.index:
        rt_dict = {}
        for s in data_df.index:
            if s == s1:
                rt = 100.0
            else:
                rt = 0.0
            rt_dict[s] = rt
        ratio_aval.append(rt_dict)
    for _rt in [90.0, 80.0, 70.0, 60.0, 50.0, 40.0, 30.0, 20.0, 10.0]:
        for s2a, s2b in combinations(data_df.index, 2):
            rt_dict = {}
            for s in data_df.index:
                if s == s2a:
                    rt = _rt
                elif s == s2b:
                    rt = 100.0 - _rt
                else:
                    rt = 0.0
                rt_dict[s] = rt
            ratio_aval.append(rt_dict)
    ratio_df = pd.DataFrame(ratio_aval)

    # calculate coal blending spec
    spec_list = ['%S', '%Ash', 'GCV', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking', 'Fouling']
    spec_list_lookup = ['Sulphur Content (%)', 'Ash Content (%)', 'Gross Calorific Value (kcal/kg)', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking Index', 'Fouling Index']
    for sp in spec_list[:-3]:
        ratio_df[sp] = sum([ratio_df[s] * data_df.loc[s, spec_list_lookup[spec_list.index(sp)]] for s in data_df.index]) / 100
    ratio_df['B/A'] = ratio_df[['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']].sum(axis=1) / ratio_df[['SiO2', 'Al2O3', 'TiO2']].sum(axis=1)
    ratio_df['Slacking'] = ratio_df['%S dry'] * ratio_df['B/A']
    ratio_df['Fouling'] = ratio_df['Na2O'] * ratio_df['B/A']

    # filter only blending spec with in boundary
    cfb12_ratio_df = ratio_df.copy()
    for sp in cfb12_limit.keys():
        cfb12_ratio_df = cfb12_ratio_df[(cfb12_ratio_df[sp] <= cfb12_limit[sp][0]) & (cfb12_ratio_df[sp] >= cfb12_limit[sp][1])]

    cfb3_ratio_df = ratio_df.copy()
    for sp in cfb3_limit.keys():
        cfb3_ratio_df = cfb3_ratio_df[(cfb3_ratio_df[sp] <= cfb3_limit[sp][0]) & (cfb3_ratio_df[sp] >= cfb3_limit[sp][1])]

    return cfb12_ratio_df.reset_index(drop=True), cfb3_ratio_df.reset_index(drop=True)

def remaining_day_cal(data_df, cfb12_ratio_df, cfb3_ratio_df, coal_aval):
    # filter zero stock supplier out
    supplier_aval = coal_aval.drop_prefix('Coal_Available_').columns[(coal_aval > 2000).any()].values

    # calculate all ratio feasible
    cfb12_ratio_filtered_df = cfb12_ratio_df[(cfb12_ratio_df[[s for s in data_df.index if s not in supplier_aval]] == 0).all(axis=1)]
    cfb3_ratio_filtered_df = cfb3_ratio_df[(cfb3_ratio_df[[s for s in data_df.index if s not in supplier_aval]] == 0).all(axis=1)]

    left = cfb12_ratio_filtered_df.add_prefix('cfb12_')
    right = cfb3_ratio_filtered_df.add_prefix('cfb3_')
    df = pd.merge(left, right, how='cross')

    df['cfb12_coal_use_total'] = (cfb12_LHV * cfb12_HHV_LHV * 3600) / (df['cfb12_GCV'].values * 4.1868) * 24 * (1 - cfb12_UOF) * 2
    df['cfb3_coal_use_total'] = (cfb3_LHV * cfb3_HHV_LHV * 3600) / (df['cfb3_GCV'].values * 4.1868) * 24 * (1 - cfb3_UOF)

    for s in data_df.index:
        df['coal_aval_' + s] = coal_aval[s].values[0]
        df['cfb12_coal_use_' + s] = (df['cfb12_coal_use_total'].values / 100) * df['cfb12_' + s].values
        df['cfb3_coal_use_' + s] = (df['cfb3_coal_use_total'].values / 100) * df['cfb3_' + s].values
        df['coal_use_' + s] = df['cfb12_coal_use_' + s].values + df['cfb3_coal_use_' + s].values
        df['day_remain_' + s] = df['coal_aval_' + s].divide(df['coal_use_' + s])

    df['day_remain'] = df[['day_remain_' + s for s in data_df.index]].min(axis=1)
    df = df[df['day_remain'] > 1.0]
    df.sort_values(by='day_remain', ascending=False, inplace=True)
    
    if len(df) > 0:
        for s in data_df.index:
            if df['coal_use_' + s].sum() == 0:
                df.drop(columns=['cfb12_' + s, 'cfb3_' + s, 'coal_aval_' + s, 'cfb12_coal_use_' + s, 'cfb3_coal_use_' + s, 'coal_use_' + s, 'day_remain_' + s], inplace=True)
                       
    return df.reset_index(drop=True)


# prepare solution df
start_dt = datetime.now()

date_rng = pd.date_range(start=date_start, end=date_stop, freq='D')
date_rng = [d.strftime('%Y-%m-%d') for d in date_rng]
df = pd.DataFrame({'Date': date_rng})
df.set_index('Date', inplace=True)

# ______Initial_______
spec_list = ['%S', '%Ash', 'GCV', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking', 'Fouling']
spec_list_lookup = ['Sulphur Content (%)', 'Ash Content (%)', 'Gross Calorific Value (kcal/kg)', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking Index', 'Fouling Index']

df[['Coal_In_' + s for s in data_df.index]] = 0.0
df['Coal_In_Total'] = 0.0
df[['Coal_Available_' + s for s in data_df.index]] = 0.0
# df['Coal_Available_DeadStock'] = round(dead_stock, 0)
df['Coal_Available_Total'] = 0.0

df[['CFB12_Ratio_' + s for s in data_df.index]] = 0.0
df['CFB12_Ratio_Total'] = 0.0
df[['CFB12_Blending_' + sp for sp in spec_list]] = 0.0
df[['CFB12_Coal_Use_' + s for s in data_df.index]] = 0.0
df['CFB12_Coal_Use_Total'] = 0.0
df[['CFB3_Ratio_' + s for s in data_df.index]] = 0.0
df['CFB3_Ratio_Total'] = 0.0
df[['CFB3_Blending_' + sp for sp in spec_list]] = 0.0
df[['CFB3_Coal_Use_' + s for s in data_df.index]] = 0.0
df['CFB3_Coal_Use_Total'] = 0.0

df[['Coal_Use_' + s for s in data_df.index]] = 0.0
df['Coal_Use_Total'] = 0.0
df[['Coal_Remain_' + s for s in data_df.index]] = 0.0
df['Coal_Remain_Total'] = 0.0