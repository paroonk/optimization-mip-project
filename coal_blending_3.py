from sys import executable
from coal_blending_data_3 import *

# %load_ext google.colab.data_table
pd.options.display.float_format = "{:,.2f}".format
pd.options.display.max_columns = None
pd.options.display.expand_frame_repr = False

date_start = '2020-06-16'
date_stop = '2020-06-27'

date_rng = pd.date_range(start=date_start, end=date_stop, freq='D')
date_rng = [d.strftime('%Y-%m-%d') for d in date_rng]


# ___Initialize model___
m = ConcreteModel()


# ______Constants_______
ratio_step = 10
n_step = 100/ratio_step


# _______Variables______
m.coal_in = Var(date_rng, data_df.index, domain=NonNegativeReals)
m.coal_use = Var(date_rng, data_df.index, domain=NonNegativeReals)
m.coal_remain = Var(date_rng, data_df.index, domain=NonNegativeReals)

m.cfb12_ratio = Var(date_rng, data_df.index, domain=NonNegativeIntegers, bounds=(0, n_step))
m.cfb3_ratio = Var(date_rng, data_df.index, domain=NonNegativeIntegers, bounds=(0, n_step))

m.cfb12_select = Var(date_rng, data_df.index, domain=Binary)
m.cfb3_select = Var(date_rng, data_df.index, domain=Binary)

m.cfb12_coal_use = Var(date_rng, domain=NonNegativeReals)
m.cfb3_coal_use = Var(date_rng, domain=NonNegativeReals)

# ______Equations_______
m.cons = ConstraintList()
        
# total ratio = 100%
for d in date_rng:
    if d == date_rng[0]:
        for s in data_df.index:
            m.cons.add(m.cfb12_ratio[d, s] == 0)
            m.cons.add(m.cfb3_ratio[d, s] == 0)
    else:
        m.cons.add(sum(m.cfb12_ratio[d, s] for s in data_df.index) == n_step)
        m.cons.add(sum(m.cfb3_ratio[d, s] for s in data_df.index) == n_step)
        
# if ratio > 0 then select = 1, else if ratio == 0 then select = 0
for d, s in product(date_rng, data_df.index):
    m.cons.add(m.cfb12_ratio[d, s] <= n_step * m.cfb12_select[d, s])
    m.cons.add(m.cfb12_ratio[d, s] >= m.cfb12_select[d, s])
    m.cons.add(m.cfb3_ratio[d, s] <= n_step * m.cfb3_select[d, s])
    m.cons.add(m.cfb3_ratio[d, s] >= m.cfb3_select[d, s])

# total number of select not exceed 2
cfb12_select_total = {d: sum(m.cfb12_select[d, s] for s in data_df.index) for d in date_rng}
cfb3_select_total = {d: sum(m.cfb3_select[d, s] for s in data_df.index) for d in date_rng}
for d in date_rng:
    if d != date_rng[0]:
        m.cons.add(cfb12_select_total[d] <= 2)
        m.cons.add(cfb3_select_total[d] <= 2)
        
# calculate coal blending spec (without B/A, Slacking, Fouling constraints, because of nonlinear function of B/A)
spec_list = ['%S', '%Ash', 'GCV', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking', 'Fouling']
spec_list_lookup = ['Sulphur Content (%)', 'Ash Content (%)', 'Gross Calorific Value (kcal/kg)', 'SiO2', 'Al2O3', 'Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O', 'TiO2', '%S dry', 'B/A', 'Slacking Index', 'Fouling Index']

cfb12_blending = {sp: {d: sum(m.cfb12_ratio[d, s] * data_df.loc[s, spec_list_lookup[spec_list.index(sp)]] for s in data_df.index) / n_step for d in date_rng} for sp in spec_list[:-3]}
cfb12_blending['B/A'] = {d: sum(cfb12_blending[sp][d] for sp in ['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']) / sum(cfb12_blending[sp][d] for sp in ['SiO2', 'Al2O3', 'TiO2']) for d in date_rng}
cfb12_blending['Slacking'] = {d: cfb12_blending['%S dry'][d] * cfb12_blending['B/A'][d] for d in date_rng}
cfb12_blending['Fouling'] = {d: cfb12_blending['Na2O'][d] * cfb12_blending['B/A'][d] for d in date_rng}

cfb3_blending = {sp: {d: sum(m.cfb3_ratio[d, s] * data_df.loc[s, spec_list_lookup[spec_list.index(sp)]] for s in data_df.index) / n_step for d in date_rng} for sp in spec_list[:-3]}
cfb3_blending['B/A'] = {d: sum(cfb3_blending[sp][d] for sp in ['Fe2O3', 'CaO', 'MgO', 'Na2O', 'K2O']) / sum(cfb3_blending[sp][d] for sp in ['SiO2', 'Al2O3', 'TiO2']) for d in date_rng}
cfb3_blending['Slacking'] = {d: cfb3_blending['%S dry'][d] * cfb3_blending['B/A'][d] for d in date_rng}
cfb3_blending['Fouling'] = {d: cfb3_blending['Na2O'][d] * cfb3_blending['B/A'][d] for d in date_rng}

# control blending spec in bounds
for d in date_rng:
    if d != date_rng[0]:
        for sp in cfb12_limit.keys():
            m.cons.add((cfb12_limit[sp][1], cfb12_blending[sp][d], cfb12_limit[sp][0]))
        for sp in cfb3_limit.keys():
            m.cons.add((cfb3_limit[sp][1], cfb3_blending[sp][d], cfb3_limit[sp][0]))

# set coal_in = incoming_stock data
for d, s in product(date_rng, data_df.index):
    if d in incoming_stock.keys():
        if s == incoming_stock[d][0]:
            m.cons.add(m.coal_in[d, s] == incoming_stock[d][1])
        else:
            m.cons.add(m.coal_in[d, s] == 0)
    else:
        m.cons.add(m.coal_in[d, s] == 0)

# calculate cfb coal use
for d in date_rng:
    if d == date_rng[0]:
        m.cons.add(m.cfb12_coal_use[d] == 0)
        m.cons.add(m.cfb3_coal_use[d] == 0)
    else:
        m.cons.add(m.cfb12_coal_use[d] == (cfb12_LHV*cfb12_HHV_LHV * 3600) / (cfb12_blending['GCV'][d] * 4.1868) * 24 * 2 * (1 - cfb12_UOF))
        m.cons.add(m.cfb3_coal_use[d] == (cfb3_LHV*cfb3_HHV_LHV * 3600) / (cfb3_blending['GCV'][d] * 4.1868) * 24 * (1 - cfb3_UOF))

# calculate coal use
for d, s in product(date_rng, data_df.index):
    if d == date_rng[0]:
        m.cons.add(m.coal_use[d, s] == 0)
    else:
        m.cons.add(m.coal_use[d, s] == (m.cfb12_ratio[d, s] * m.cfb12_coal_use[d] + m.cfb3_ratio[d, s] * m.cfb3_coal_use[d]) / n_step)

# calculate coal remain
for d, s in product(date_rng, data_df.index):
    if d == date_rng[0]:
        m.cons.add(m.coal_remain[d, s] == data_df.loc[s, 'Initial Stock (ton)'])
    else:
        m.cons.add(m.coal_remain[d, s] == m.coal_remain[date_rng[date_rng.index(d) - 1], s] + m.coal_in[d, s] - m.coal_use[d, s])


# ______Objective_______
cfb12_total_price = sum(m.cfb12_ratio[d, s] * data_df.loc[s, 'Coal Adjust Price'] for s in data_df.index for d in date_rng)
cfb3_total_price = sum(m.cfb3_ratio[d, s] * data_df.loc[s, 'Coal Adjust Price'] for s in data_df.index for d in date_rng)

m.obj = Objective(expr=cfb12_total_price + cfb3_total_price, sense=minimize)


#_____Solve Problem_____
# solver = SolverFactory('glpk', executable='/usr/bin/glpsol')
# solver = SolverFactory('cbc', executable='/usr/bin/cbc')
# solver = SolverFactory('ipopt', executable='/content/ipopt')
# solver = SolverFactory('bonmin', executable='/content/bonmin')
# solver = SolverFactory('couenne', executable='/content/couenne')
solver = SolverFactory('apopt.py')

results = solver.solve(m, tee=True)