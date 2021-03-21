from coal_blending_data import *

date_rng = pd.date_range(start=date_start, end=date_stop, freq='D')
date_rng = [d.strftime('%Y-%m-%d') for d in date_rng]


# ___Initialize model___
m = GEKKO(server='http://localhost:8081/')

# ______Constants_______
ratio_step = 10
n_step = 100/ratio_step

# ______Parameters______
coal_in = np.zeros([len(date_rng), len(supplier)])

# set coal_in = incoming_stock data
for d, s, n in incoming_stock:
    if d in date_rng:
        coal_in[date_rng.index(d)][supplier.index(s)] = n

# _______Variables______
coal_remain = m.Array(m.Var, (len(date_rng), len(supplier)), integer=False, lb=0, ub=None)

# Integer [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
cfb12_ratio = m.Array(m.Var, (len(date_rng), len(supplier)), integer=False, lb=0, ub=n_step)
cfb3_ratio = m.Array(m.Var, (len(date_rng), len(supplier)), integer=False, lb=0, ub=n_step)

cfb12_select = m.Array(m.Var, (len(date_rng), len(supplier)), integer=True, lb=0, ub=1)
cfb3_select = m.Array(m.Var, (len(date_rng), len(supplier)), integer=True, lb=0, ub=1)


# ____Intermediates_____
coal_remain_total = [m.Intermediate(m.sum([coal_remain[d][s] for s in range(len(supplier))]) + dead_stock) for d in range(len(date_rng))]
cfb12_select_total = [m.Intermediate(m.sum([cfb12_select[d][s] for s in range(len(supplier))])) for d in range(len(date_rng))]
cfb3_select_total = [m.Intermediate(m.sum([cfb3_select[d][s] for s in range(len(supplier))])) for d in range(len(date_rng))]

spec_list = ['%S', '%Ash', 'GCV', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking Index', 'Fouling Index']
spec_list_lookup = ['Sulphur Content (%)', 'Ash Content (%)', 'Gross Calorific Value (kcal/kg)', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking Index', 'Fouling Index']

# calculate coal blending spec
cfb12_blending = [[m.Intermediate(m.sum([cfb12_ratio[d][s] * df_coal_spec.loc[supplier[s], spec_list_lookup[sp]] for s in range(len(supplier))]) / n_step) for sp in range(len(spec_list[:-3]))] for d in range(len(date_rng))]
cfb12_blending_BA = [m.Intermediate(m.sum([cfb12_blending[d][spec_list.index(B)] for B in ['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']]) / m.sum([cfb12_blending[d][spec_list.index(A)] for A in ['SiO2', 'Al2O3', 'TiO2']])) for d in range(len(date_rng))]
cfb12_blending_Slack = [m.Intermediate(cfb12_blending[d][spec_list.index('%S dry')] * cfb12_blending_BA[d]) for d in range(len(date_rng))]
cfb12_blending_Foul = [m.Intermediate(cfb12_blending[d][spec_list.index('Na2O')] * cfb12_blending_BA[d]) for d in range(len(date_rng))]
cfb3_blending = [[m.Intermediate(m.sum([cfb3_ratio[d][s] * df_coal_spec.loc[supplier[s], spec_list_lookup[sp]] for s in range(len(supplier))]) / n_step) for sp in range(len(spec_list[:-3]))] for d in range(len(date_rng))]
cfb3_blending_BA = [m.Intermediate(m.sum([cfb3_blending[d][spec_list.index(B)] for B in ['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']]) / m.sum([cfb3_blending[d][spec_list.index(A)] for A in ['SiO2', 'Al2O3', 'TiO2']])) for d in range(len(date_rng))]
cfb3_blending_Slack = [m.Intermediate(cfb3_blending[d][spec_list.index('%S dry')] * cfb3_blending_BA[d]) for d in range(len(date_rng))]
cfb3_blending_Foul = [m.Intermediate(cfb3_blending[d][spec_list.index('Na2O')] * cfb3_blending_BA[d]) for d in range(len(date_rng))]


# ______Equations_______
# total ratio = 100%
for d in range(len(date_rng)):
    if d == 0:
        for s in range(len(supplier)):
            m.Equation(cfb12_ratio[d][s] == 0)
            m.Equation(cfb3_ratio[d][s] == 0)
    else:
        m.Equation(m.sum([cfb12_ratio[d][s] for s in range(len(supplier))]) == n_step)
        m.Equation(m.sum([cfb3_ratio[d][s] for s in range(len(supplier))]) == n_step)
        
# if ratio > 0 then select = 1, else if ratio == 0 then select = 0
for d in range(len(date_rng)):
    for s in range(len(supplier)):
        m.Equation(cfb12_ratio[d][s] <= n_step * cfb12_select[d][s])
        m.Equation(cfb12_ratio[d][s] >= cfb12_select[d][s])
        m.Equation(cfb3_ratio[d][s] <= n_step * cfb3_select[d][s])
        m.Equation(cfb3_ratio[d][s] >= cfb3_select[d][s])
        
# total number of select not exceed 2
for d in range(len(date_rng)):
    if d > 0:
        m.Equation(cfb12_select_total[d] <= 2)
        m.Equation(cfb3_select_total[d] <= 2)
        
# control blending spec
for d in range(len(date_rng)):
    if d > 0:
        for sp in cfb12_limit.keys():
            if sp in ['%S', 'Ash', 'GCV', 'Fe2O3', 'Na2O']:
                m.Equation(cfb12_blending[d][spec_list.index(sp)] <= cfb12_limit[sp][0])
                m.Equation(cfb12_blending[d][spec_list.index(sp)] >= cfb12_limit[sp][1])
            elif sp == 'Slack':
                m.Equation(cfb12_blending_Slack[d] <= cfb12_limit[sp][0])
                m.Equation(cfb12_blending_Slack[d] >= cfb12_limit[sp][1])
            elif sp == 'Foul':
                m.Equation(cfb12_blending_Foul[d] <= cfb12_limit[sp][0])
                m.Equation(cfb12_blending_Foul[d] >= cfb12_limit[sp][1])
        for sp in cfb3_limit.keys():
            if sp in ['%S', 'Ash', 'GCV', 'Fe2O3', 'Na2O']:
                m.Equation(cfb3_blending[d][spec_list.index(sp)] <= cfb3_limit[sp][0])
                m.Equation(cfb3_blending[d][spec_list.index(sp)] >= cfb3_limit[sp][1])
            elif sp == 'Slack':
                m.Equation(cfb3_blending_Slack[d] <= cfb3_limit[sp][0])
                m.Equation(cfb3_blending_Slack[d] >= cfb3_limit[sp][1])
            elif sp == 'Foul':
                m.Equation(cfb3_blending_Foul[d] <= cfb3_limit[sp][0])
                m.Equation(cfb3_blending_Foul[d] >= cfb3_limit[sp][1])


# calculate coal remain
for s, d in product(range(len(supplier)), range(len(date_rng))):
    if d == 0:
        m.Equation(coal_remain[d][s] == initial_stock[s])
    else:
        m.Equation(coal_remain[d][s] == coal_remain[d - 1][s] + coal_in[d][s])


# ______Objective_______
m.Minimize(m.sum([cfb12_ratio[d][s] * coal_adjust_price[s] for s in range(len(supplier)) for d in range(len(date_rng))] + [cfb3_ratio[d][s] * coal_adjust_price[s] for s in range(len(supplier)) for d in range(len(date_rng))]))


#_____Solve Problem_____
m.options.SOLVER = 1
m.solve(debug=1)
# m.solve(disp=False)

df = pd.DataFrame({'Date': date_rng})
df.set_index('Date', inplace=True)

df.loc[:, ['Coal_In_{}'.format(s) for s in supplier]] = coal_in
df.loc[:, ['Coal_Remain_{}'.format(s) for s in supplier]] = [[coal_remain[d][s].value[0] for s in range(len(supplier))] for d in range(len(date_rng))]
df.loc[:, ['Coal_Remain_Total']] = [coal_remain_total[d].value[0] for d in range(len(date_rng))]
df.loc[:, ['CFB12_Ratio_{}'.format(s) for s in supplier]] = [[ratio_step * cfb12_ratio[d][s].value[0] for s in range(len(supplier))] for d in range(len(date_rng))]
df.loc[:, ['CFB12_Ratio_Select']] = [cfb12_select_total[d].value[0] for d in range(len(date_rng))]
df.loc[:, ['CFB12_Blending_{}'.format(sp) for sp in spec_list[:-3]]] = [[cfb12_blending[d][sp].value[0] for sp in range(len(spec_list[:-3]))] for d in range(len(date_rng))]
df.loc[:, ['CFB12_Blending_{}'.format(sp) for sp in spec_list[-3:-2]]] = [cfb12_blending_BA[d].value[0] for d in range(len(date_rng))]
df.loc[:, ['CFB12_Blending_{}'.format(sp) for sp in spec_list[-2:-1]]] = [cfb12_blending_Slack[d].value[0] for d in range(len(date_rng))]
df.loc[:, ['CFB12_Blending_{}'.format(sp) for sp in spec_list[-1:]]] = [cfb12_blending_Foul[d].value[0] for d in range(len(date_rng))]
df.loc[:, ['CFB3_Ratio_{}'.format(s) for s in supplier]] = [[ratio_step * cfb3_ratio[d][s].value[0] for s in range(len(supplier))] for d in range(len(date_rng))]
df.loc[:, ['CFB3_Ratio_Select']] = [cfb3_select_total[d].value[0] for d in range(len(date_rng))]
df.loc[:, ['CFB3_Blending_{}'.format(sp) for sp in spec_list[:-3]]] = [[cfb3_blending[d][sp].value[0] for sp in range(len(spec_list[:-3]))] for d in range(len(date_rng))]
df.loc[:, ['CFB3_Blending_{}'.format(sp) for sp in spec_list[-3:-2]]] = [cfb3_blending_BA[d].value[0] for d in range(len(date_rng))]
df.loc[:, ['CFB3_Blending_{}'.format(sp) for sp in spec_list[-2:-1]]] = [cfb3_blending_Slack[d].value[0] for d in range(len(date_rng))]
df.loc[:, ['CFB3_Blending_{}'.format(sp) for sp in spec_list[-1:]]] = [cfb3_blending_Foul[d].value[0] for d in range(len(date_rng))]

df.columns = pd.MultiIndex.from_tuples([(col[:col.rfind('_')], col[col.rfind('_') + 1:]) for col in df.columns])

df.fillna(0, inplace=True)
df = df.loc[:, (df != 0).any(axis=0)]   #hide zero columns
print(df.head(10))