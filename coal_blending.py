from coal_blending_data import *

date_rng = pd.date_range(start=date_start, end=date_stop, freq='D')
date_rng = [d.strftime('%Y-%m-%d') for d in date_rng]


# ___Initialize model___
m = GEKKO()


# ______Constants_______
ratio_step = 10
n_step = 100/ratio_step

# ______Parameters______
coal_price = m.Array(m.Param, len(supplier))
coal_in = np.zeros([len(date_rng), len(supplier)])
coal_remain = np.zeros([len(date_rng), len(supplier)])
coal_remain_total = np.zeros(len(date_rng))
# coal_remain = [[m.Var(0) for d in date_rng] for s in supplier]
# coal_remain_total = [m.Var(0) for d in date_rng]

# set coal_in = incoming_stock data
for d, s, n in incoming_stock:
    if d in date_rng:
        coal_in[date_rng.index(d)][supplier.index(s)] = n

# _______Variables______
# Integer [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
cfb12_ratio = m.Array(m.Var, (len(supplier), len(date_rng)), integer=True, lb=0, ub=n_step)
cfb3_ratio = m.Array(m.Var, (len(supplier), len(date_rng)), integer=True, lb=0, ub=n_step)

# cfb12_select = [[m.Var(integer=True, lb=0, ub=1) for d in date_rng] for s in supplier]
# cfb3_select = [[m.Var(integer=True, lb=0, ub=1) for d in date_rng] for s in supplier]

# spec_list = ['%S', '%Ash', 'GCV', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking Index', 'Fouling Index']
# spec_list_lookup = ['Sulphur Content (%)', 'Ash Content (%)', 'Gross Calorific Value (kcal/kg)', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking Index', 'Fouling Index']
# cfb12_blending = [[m.Var() for d in date_rng] for sp in spec_list]
# cfb3_blending = [[m.Var() for d in date_rng] for sp in spec_list]


# ____Intermediates_____  
# coal_remain = [[m.Intermediate(0) for d in date_rng] for s in supplier]
# coal_remain_total = [m.Intermediate(0) for d in date_rng]

# ______Equations_______                                                

# total ratio = 100%, and selection not exceed 2
# for d in range(len(date_rng)):
#     if d == 0:
#         for s in range(len(supplier)):
#             m.Equation(cfb12_ratio[s][d] == 0)
#             m.Equation(cfb3_ratio[s][d] == 0)
#     else:
#         m.Equation(m.sum([cfb12_ratio[s][d] for s in range(len(supplier))]) == n_step)
#         m.Equation(m.sum([cfb3_ratio[s][d] for s in range(len(supplier))]) == n_step)

#         m.Equation(m.sum([m.if2(cfb12_ratio[s][d], 0, 1) for s in range(len(supplier))]) <= 2)
#         m.Equation(m.sum([m.if2(cfb3_ratio[s][d], 0, 1) for s in range(len(supplier))]) <= 2)

# if ratio > 0 then select = 1, else if ratio == 0 then select = 0
# for d in range(len(date_rng)):
#     for s in range(len(supplier)):
        # m.Equation(cfb12_ratio[s][d] <= n_step * cfb12_select[s][d])
        # m.Equation(cfb12_ratio[s][d] >= cfb12_select[s][d])
        # m.Equation(cfb3_ratio[s][d] <= n_step * cfb3_select[s][d])
        # m.Equation(cfb3_ratio[s][d] >= cfb3_select[s][d])

# total number of select not exceed 2
# for d in range(len(date_rng)):
#     if d > 0:
#         m.Equation(m.sum([cfb12_select[s][d] for s in range(len(supplier))]) <= 2)
#         m.Equation(m.sum([cfb3_select[s][d] for s in range(len(supplier))]) <= 2)

# # calculate coal blending spec
# for sp, d in product(range(len(spec_list)), range(len(date_rng))):
#     pass


    # if sp == spec_list.index('B/A'):
    #     model += xsum(cfb12_blending[spec_list.index(B)][d] for B in ['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']) >= xsum(cfb12_blending[spec_list.index(A)][d] for A in ['SiO2', 'Al2O3', 'TiO2'])
    #     model += cfb3_blending[sp][d] == xsum(cfb3_blending[spec_list.index(B)][d] for B in ['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']) / xsum(cfb3_blending[spec_list.index(A)][d] for A in ['SiO2', 'Al2O3', 'TiO2'])
    # elif sp == spec_list.index('Slacking Index'):
    #     model += cfb12_blending[sp][d] == cfb12_blending[spec_list.index('%S dry')][d] * cfb12_blending[spec_list.index('B/A')][d]
    #     model += cfb3_blending[sp][d] == cfb3_blending[spec_list.index('%S dry')][d] * cfb3_blending[spec_list.index('B/A')][d]
    # elif sp == spec_list.index('Fouling Index'):
    #     model += cfb12_blending[sp][d] == cfb12_blending[spec_list.index('Na2O')][d] * cfb12_blending[spec_list.index('B/A')][d]
    #     model += cfb3_blending[sp][d] == cfb3_blending[spec_list.index('Na2O')][d] * cfb3_blending[spec_list.index('B/A')][d]
    # else:
    #     model += cfb12_blending[sp][d] == xsum(cfb12_ratio[s][d] * df_coal_spec.loc[supplier[s], spec_list_lookup[sp]] for s in range(len(supplier))) / n_step
    #     model += cfb3_blending[sp][d] == xsum(cfb3_ratio[s][d] * df_coal_spec.loc[supplier[s], spec_list_lookup[sp]] for s in range(len(supplier))) / n_step

# calculate coal remain
# for s, d in product(range(len(supplier)), range(len(date_rng))):
#     if d == 0:
#         coal_remain[s][d].value = initial_stock[s]
#     else:
#         coal_remain[s][d].value = coal_remain[s][d - 1] + coal_in[s][d]

# calculate coal remain total
# for d in range(len(date_rng)):
#     coal_remain_total[d].value = m.sum([coal_remain[s][d] for s in range(len(supplier))]) + dead_stock


# ______Objective_______
m.Minimize(m.sum([cfb12_ratio[s][d] * coal_price[s] for s in range(len(supplier)) for d in range(len(date_rng))] + [cfb3_ratio[s][d] * coal_price[s] for s in range(len(supplier)) for d in range(len(date_rng))]))

    
#_____Solve Problem_____
m.options.SOLVER = 1
m.solve()
# m.solve(disp=False)

df = pd.DataFrame({'Date': date_rng})
df.loc[:, ['Coal_In_{}'.format(s) for s in supplier]] = coal_in
# df.loc[:, ['Coal_Remain_{}'.format(s) for s in supplier]] = [[coal_remain[s][d].value for s in range(len(supplier))] for d in range(len(date_rng))]
# df.loc[:, ['Coal_Remain_Total']] = [coal_remain_total[d].value for d in range(len(date_rng))]

df.loc[:, ['CFB12_Ratio_{}'.format(s) for s in supplier]] = [[ratio_step * cfb12_ratio[s][d].value[0] for s in range(len(supplier))] for d in range(len(date_rng))]
# df.loc[:, ['CFB12_Select_{}'.format(s) for s in supplier]] = [[cfb12_select[s][d].value[0] for s in range(len(supplier))] for d in range(len(date_rng))]
# df.loc[:, ['CFB12_Blending_{}'.format(s) for s in spec_list]] = [[cfb12_blending[s][d].value[0] for s in range(len(spec_list))] for d in range(len(date_rng))]
df.loc[:, ['CFB3_Ratio_{}'.format(s) for s in supplier]] = [[ratio_step * cfb3_ratio[s][d].value[0] for s in range(len(supplier))] for d in range(len(date_rng))]
# df.loc[:, ['CFB3_Select_{}'.format(s) for s in supplier]] = [[cfb3_select[s][d].value[0] for s in range(len(supplier))] for d in range(len(date_rng))]
# df.loc[:, ['CFB3_Blending_{}'.format(s) for s in spec_list]] = [[cfb3_blending[s][d].value[0] for s in range(len(spec_list))] for d in range(len(date_rng))]

df.set_index('Date', inplace=True)
df.columns = pd.MultiIndex.from_tuples([(col[:col.rfind('_')], col[col.rfind('_') + 1:]) for col in df.columns])

# df = df.loc[:, (df != 0).any(axis=0)]   #hide zero columns
print(df.head(10))