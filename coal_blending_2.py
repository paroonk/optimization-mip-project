from mip import model
from coal_blending_data import *
from math import log

date_rng = pd.date_range(start=date_start, end=date_stop, freq='D')
date_rng = [d.strftime('%Y-%m-%d') for d in date_rng]


# ___Initialize model___
m = Model()

# ______Constants_______
ratio_step = 10
n_step = 100/ratio_step


# _______Variables______
coal_in = [[m.add_var(name='Coal_In_{}_{}'.format(supplier[s], date_rng[d]), var_type='I', lb=0) for s in range(len(supplier))] for d in range(len(date_rng))]
coal_remain = [[m.add_var(name='Coal_Remain_{}_{}'.format(supplier[s], date_rng[d]), var_type='I', lb=0) for s in range(len(supplier))] for d in range(len(date_rng))]
coal_remain_total = [m.add_var(name='Coal_Remain_Total_{}'.format(date_rng[d]), var_type='I', lb=0) for d in range(len(date_rng))]

# Integer [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
cfb12_ratio = [[m.add_var(name='CFB12_Ratio_{}_{}'.format(supplier[s], date_rng[d]), var_type='I', lb=0, ub=n_step) for s in range(len(supplier))] for d in range(len(date_rng))]
cfb3_ratio = [[m.add_var(name='CFB3_Ratio_{}_{}'.format(supplier[s], date_rng[d]), var_type='I', lb=0, ub=n_step) for s in range(len(supplier))] for d in range(len(date_rng))]

cfb12_select = [[m.add_var(name='CFB12_Select_{}_{}'.format(supplier[s], date_rng[d]), var_type='B') for s in range(len(supplier))] for d in range(len(date_rng))]
cfb3_select = [[m.add_var(name='CFB3_Select_{}_{}'.format(supplier[s], date_rng[d]), var_type='B') for s in range(len(supplier))] for d in range(len(date_rng))]

# ______Equations_______
# set coal_in = incoming_stock data
for d in incoming_stock.keys():
    if d in date_rng:
        m += coal_in[date_rng.index(d)][supplier.index(incoming_stock[d][0])] >= incoming_stock[d][1]
        
# # total ratio = 100%
for d in range(len(date_rng)):
    if d == 0:
        for s in range(len(supplier)):
            m += cfb12_ratio[d][s] == 0
            m += cfb3_ratio[d][s] == 0
    else:
        m += xsum(cfb12_ratio[d][s] for s in range(len(supplier))) == n_step
        m += xsum(cfb3_ratio[d][s] for s in range(len(supplier))) == n_step
        
# if ratio > 0 then select = 1, else if ratio == 0 then select = 0
for d in range(len(date_rng)):
    for s in range(len(supplier)):
        m += cfb12_ratio[d][s] <= n_step * cfb12_select[d][s]
        m += cfb12_ratio[d][s] >= cfb12_select[d][s]
        m += cfb3_ratio[d][s] <= n_step * cfb3_select[d][s]
        m += cfb3_ratio[d][s] >= cfb3_select[d][s]

        
# total number of select not exceed 2
cfb12_select_total = [xsum(cfb12_select[d][s] for s in range(len(supplier))) for d in range(len(date_rng))]
cfb3_select_total = [xsum(cfb3_select[d][s] for s in range(len(supplier))) for d in range(len(date_rng))]
for d in range(len(date_rng)):
    if d > 0:
        m += cfb12_select_total[d] <= 2
        m += cfb3_select_total[d] <= 2
        
# # control blending spec
spec_list = ['%S', '%Ash', 'GCV', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking', 'Fouling']
spec_list_lookup = ['Sulphur Content (%)', 'Ash Content (%)', 'Gross Calorific Value (kcal/kg)', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking Index', 'Fouling Index']

# calculate coal blending spec
cfb12_blending = [[xsum(cfb12_ratio[d][s] * df_coal_spec.loc[supplier[s], spec_list_lookup[sp]] for s in range(len(supplier))) / n_step for d in range(len(date_rng))] for sp in range(len(spec_list[:-3]))]
cfb3_blending = [[xsum(cfb3_ratio[d][s] * df_coal_spec.loc[supplier[s], spec_list_lookup[sp]] for s in range(len(supplier))) / n_step for d in range(len(date_rng))] for sp in range(len(spec_list[:-3]))]

for d in range(len(date_rng)):
    if d > 0:
        for sp in cfb12_limit.keys():
            if sp in ['%S', 'Ash', 'GCV', 'Fe2O3', 'Na2O']:
                m += cfb12_blending[spec_list.index(sp)][d] <= cfb12_limit[sp][0]
                m += cfb12_blending[spec_list.index(sp)][d] >= cfb12_limit[sp][1]
            # elif sp == 'Slack':
            #     m += cfb12_y_Slack[d] <= cfb12_limit[sp][0] * cfb12_A[d]
                # m += cfb12_blending[spec_list.index(sp)][d] >= cfb12_limit[sp][1]
#             elif sp == 'Foul':
#                 m.Equation(cfb12_blending_Foul[d] <= cfb12_limit[sp][0])
#                 m.Equation(cfb12_blending_Foul[d] >= cfb12_limit[sp][1])
        for sp in cfb3_limit.keys():
            if sp in ['%S', 'Ash', 'GCV', 'Fe2O3', 'Na2O']:
                m += cfb3_blending[spec_list.index(sp)][d] <= cfb3_limit[sp][0]
                m += cfb3_blending[spec_list.index(sp)][d] >= cfb3_limit[sp][1]
#             elif sp == 'Slack':
#                 m.Equation(cfb3_blending_Slack[d] <= cfb3_limit[sp][0])
#                 m.Equation(cfb3_blending_Slack[d] >= cfb3_limit[sp][1])
#             elif sp == 'Foul':
#                 m.Equation(cfb3_blending_Foul[d] <= cfb3_limit[sp][0])
#                 m.Equation(cfb3_blending_Foul[d] >= cfb3_limit[sp][1])


# calculate coal remain
for s, d in product(range(len(supplier)), range(len(date_rng))):
    if d == 0:
        m += coal_remain[d][s] == initial_stock[s]
    else:
        m += coal_remain[d][s] == coal_remain[d - 1][s] + coal_in[d][s]

for d in range(len(date_rng)):
    m += coal_remain_total[d] == xsum(coal_remain[d][s] for s in range(len(supplier))) + round(dead_stock, 0)


# # ______Objective_______
cfb12_total_price = xsum(cfb12_ratio[d][s] * coal_adjust_price[s] for s in range(len(supplier)) for d in range(len(date_rng)))
cfb3_total_price = xsum(cfb3_ratio[d][s] * coal_adjust_price[s] for s in range(len(supplier)) for d in range(len(date_rng)))

m.objective = minimize(cfb12_total_price + cfb3_total_price)


# #_____Solve Problem_____
status = m.optimize()

df = pd.DataFrame({'Date': date_rng})
df.set_index('Date', inplace=True)

# df.loc[:, ['Coal_In_{}'.format(s) for s in supplier]] = [[coal_in[d][s].x for s in range(len(supplier))] for d in range(len(date_rng))]
df.loc[:, ['Coal_Remain_{}'.format(s) for s in supplier]] = [[coal_remain[d][s].x for s in range(len(supplier))] for d in range(len(date_rng))]
df.loc[:, ['Coal_Remain_Total']] = [coal_remain_total[d].x for d in range(len(date_rng))]

df.loc[:, ['CFB12_Ratio_{}'.format(s) for s in supplier]] = [[ratio_step * cfb12_ratio[d][s].x for s in range(len(supplier))] for d in range(len(date_rng))]
df.loc[:, ['CFB12_Ratio_Select']] = [cfb12_select_total[d].x for d in range(len(date_rng))]
df.loc[:, ['CFB12_Blending_{}'.format(sp) for sp in spec_list[:-3]]] = [[cfb12_blending[sp][d].x for sp in range(len(spec_list[:-3]))] for d in range(len(date_rng))]
cfb12_blending_B = [sum([cfb12_blending[spec_list.index(B)][d].x for B in ['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']]) for d in range(len(date_rng))]
cfb12_blending_A = [sum([cfb12_blending[spec_list.index(A)][d].x for A in ['SiO2', 'Al2O3', 'TiO2']]) for d in range(len(date_rng))]
df.loc[:, ['CFB12_Blending_B/A']] = [b / a for (b, a) in zip(cfb12_blending_B, cfb12_blending_A)]
df.loc[:, ['CFB12_Blending_Slacking']] = df['CFB12_Blending_%S dry'] * df['CFB12_Blending_B/A']
df.loc[:, ['CFB12_Blending_Fouling']] = df['CFB12_Blending_Na2O'] * df['CFB12_Blending_B/A']

df.loc[:, ['CFB3_Ratio_{}'.format(s) for s in supplier]] = [[ratio_step * cfb3_ratio[d][s].x for s in range(len(supplier))] for d in range(len(date_rng))]
df.loc[:, ['CFB3_Ratio_Select']] = [cfb3_select_total[d].x for d in range(len(date_rng))]
df.loc[:, ['CFB3_Blending_{}'.format(sp) for sp in spec_list[:-3]]] = [[cfb3_blending[sp][d].x for sp in range(len(spec_list[:-3]))] for d in range(len(date_rng))]
cfb3_blending_B = [sum([cfb3_blending[spec_list.index(B)][d].x for B in ['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']]) for d in range(len(date_rng))]
cfb3_blending_A = [sum([cfb3_blending[spec_list.index(A)][d].x for A in ['SiO2', 'Al2O3', 'TiO2']]) for d in range(len(date_rng))]
df.loc[:, ['CFB3_Blending_B/A']] = [b / a for (b, a) in zip(cfb3_blending_B, cfb3_blending_A)]
df.loc[:, ['CFB3_Blending_Slacking']] = df['CFB3_Blending_%S dry'] * df['CFB3_Blending_B/A']
df.loc[:, ['CFB3_Blending_Fouling']] = df['CFB3_Blending_Na2O'] * df['CFB3_Blending_B/A']

df.columns = pd.MultiIndex.from_tuples([(col[:col.rfind('_')], col[col.rfind('_') + 1:]) for col in df.columns])

df.fillna(0, inplace=True)
# df = df.loc[:, (df != 0).any(axis=0)]   #hide zero columns
print(df)