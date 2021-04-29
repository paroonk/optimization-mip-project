from datetime import datetime

from numpy import False_
from coal_feasible_search_base import *

# set coal_in = incoming_stock data
for d in incoming_stock.keys():
    if d in date_rng:
        df.loc[d, 'Coal_In_' + incoming_stock[d][0]] = incoming_stock[d][1]

# calculate coal available for day 0
d = 0
df.loc[date_rng[d], ['Coal_Available_' + s for s in data_df.index]] = [data_df.loc[s, 'Initial Stock (ton)'] for s in data_df.index]
df.loc[date_rng[d], ['Coal_Remain_' + s for s in data_df.index]] = [df.loc[date_rng[d], 'Coal_Available_{}'.format(s)] - df.loc[date_rng[d], 'Coal_Use_{}'.format(s)] for s in data_df.index]

# calculate all available ratio
cfb12_ratio_df, cfb3_ratio_df = ratio_cal(data_df)

# ______Search_______
try:
    d = 1
    plan = {}
    solvable = True
    last_dt = datetime.now() - timedelta(days=1)
    solution_df = pd.DataFrame()

    while d < len(date_rng) and solvable == True:
        # calculate plan
        while True:
            if d not in plan:
                df.loc[date_rng[d], ['Coal_Available_' + s for s in data_df.index]] = [df.loc[date_rng[d - 1], 'Coal_Remain_' + s] + df.loc[date_rng[d - 1], 'Coal_In_' + s] for s in data_df.index]
                coal_aval = df.loc[date_rng[d:d + 1], ['Coal_Available_{}'.format(s) for s in data_df.index]]
                plan[d] = remaining_day_cal(data_df, cfb12_ratio_df, cfb3_ratio_df, coal_aval)
                
                if d == 1:
                    plan[d].to_excel('plan.xlsx')

            if len(plan[d]) > 0:
                break
            else:
                if d != 1:
                    plan.pop(d)
                    df.loc[date_rng[d:]] = 0
                    d = max(list(plan.keys()))
                    
                    supplier_aval = [s for s in data_df.index if 'coal_use_' + s in plan[d].iloc[0].index]
                    # improve 1
                    if len(supplier_aval) <= 2:
                        # if have less than 2 choices of supplier and best branch not feasible, skip this group of branches and go back to root of this branch and continue
                        plan[d] = []
                    else:
                        # continue next branch
                        plan[d] = plan[d].iloc[1:]
                        
                        # improve 2
                        # re-filter to check number of suppliers left
                        if len(plan[d]) > 1:
                            for s in supplier_aval:
                                if plan[d]['coal_use_' + s].sum() == 0:
                                    plan[d].drop(columns=['cfb12_' + s, 'cfb3_' + s, 'coal_aval_' + s, 'cfb12_coal_use_' + s, 'cfb3_coal_use_' + s, 'coal_use_' + s, 'day_remain_' + s], inplace=True)
                else:
                    solvable = False
                    break              
            
        if solvable:
            current_plan = plan[d].iloc[0]

            # calculate coal usage for selected plan
            supplier_aval = [s for s in data_df.index if 'coal_use_' + s in current_plan.index]

            day_remain = int(current_plan['day_remain'])
            
            # print status
            list_plan = [len(df) for i, df in plan.items()]
            print(
                '{:.0f}'.format(d),
                ' ', '{:.2f}'.format(d + current_plan['day_remain']),
                ' ', list_plan,
                  )
            
            solution = pd.DataFrame([[d, d + current_plan['day_remain'], list_plan, supplier_aval, current_plan[['cfb12_' + s for s in supplier_aval]].values, current_plan[['cfb3_' + s for s in supplier_aval]].values]],
                                    columns=['start_d', 'end_d', 'plan', 'supplier_aval', 'cfb12_ratio', 'cfb3_ratio'])
            solution_df = solution_df.append(solution, ignore_index=True)
            # if datetime.now() - last_dt >= timedelta(seconds=1):
            #     last_dt = datetime.now()
            #     print(date_rng[d], [len(df) for i, df in plan.items()])
            
            df.loc[date_rng[d:d + day_remain], ['CFB12_Ratio_' + s for s in supplier_aval]] = current_plan[['cfb12_' + s for s in supplier_aval]].values
            df.loc[date_rng[d:d + day_remain], ['CFB3_Ratio_' + s for s in supplier_aval]] = current_plan[['cfb3_' + s for s in supplier_aval]].values
            df.loc[date_rng[d:d + day_remain], ['CFB12_Blending_' + sp for sp in spec_list]] = current_plan[['cfb12_' + sp for sp in spec_list]].values
            df.loc[date_rng[d:d + day_remain], ['CFB3_Blending_' + sp for sp in spec_list]] = current_plan[['cfb3_' + sp for sp in spec_list]].values
            df.loc[date_rng[d:d + day_remain], ['CFB12_Coal_Use_' + s for s in supplier_aval]] = current_plan[['cfb12_coal_use_' + s for s in supplier_aval]].values
            df.loc[date_rng[d:d + day_remain], ['CFB3_Coal_Use_' + s for s in supplier_aval]] = current_plan[['cfb3_coal_use_' + s for s in supplier_aval]].values
            df.loc[date_rng[d:d + day_remain], ['Coal_Use_' + s for s in supplier_aval]] = current_plan[['coal_use_' + s for s in supplier_aval]].values
            for i in range(min([day_remain, len(date_rng) - d])):
                df.loc[date_rng[d + i], ['Coal_Available_' + s for s in data_df.index]] = [df.loc[date_rng[d + i - 1], 'Coal_Remain_' + s] + df.loc[date_rng[d + i - 1], 'Coal_In_' + s] for s in data_df.index]
                df.loc[date_rng[d + i], ['Coal_Remain_' + s for s in data_df.index]] = [df.loc[date_rng[d + i], 'Coal_Available_{}'.format(s)] - df.loc[date_rng[d + i], 'Coal_Use_{}'.format(s)] for s in data_df.index]

            d += day_remain

# Results
finally:
    pd.set_option('display.max_rows', None)
    print(solution_df)
    pd.set_option('display.max_rows', 10)
    
    if solvable:
        df['Coal_In_Total'] = df[['Coal_In_{}'.format(s) for s in data_df.index]].sum(axis=1)
        # df['Coal_Available_Total'] = df[['Coal_Available_{}'.format(s) for s in data_df.index] + ['Coal_Available_DeadStock']].sum(axis=1)
        df['Coal_Available_Total'] = df[['Coal_Available_{}'.format(s) for s in data_df.index]].sum(axis=1)
        df['CFB12_Ratio_Total'] = df[['CFB12_Ratio_{}'.format(s) for s in data_df.index]].sum(axis=1)
        df['CFB3_Ratio_Total'] = df[['CFB3_Ratio_{}'.format(s) for s in data_df.index]].sum(axis=1)
        df['CFB12_Coal_Use_Total'] = df[['CFB12_Coal_Use_{}'.format(s) for s in data_df.index]].sum(axis=1)
        df['CFB3_Coal_Use_Total'] = df[['CFB3_Coal_Use_{}'.format(s) for s in data_df.index]].sum(axis=1)
        df['Coal_Use_Total'] = df[['Coal_Use_{}'.format(s) for s in data_df.index]].sum(axis=1)
        df['Coal_Remain_Total'] = df[['Coal_Remain_{}'.format(s) for s in data_df.index]].sum(axis=1)

        # df.columns = pd.MultiIndex.from_tuples([(col[:col.rfind('_')], col[col.rfind('_') + 1:]) for col in df.columns])
        # l_print = 5
        # print(df[['Coal_In', 'Coal_Available', 'Coal_Use', 'Coal_Remain']].head(l_print))
        # print(df[['Coal_In', 'Coal_Available', 'Coal_Use', 'Coal_Remain']].tail(l_print))
        # print(df[['CFB12_Ratio', 'CFB12_Blending', 'CFB12_Coal_Use']].head(l_print))
        # print(df[['CFB12_Ratio', 'CFB12_Blending', 'CFB12_Coal_Use']].tail(l_print))
        # print(df[['CFB3_Ratio', 'CFB3_Blending', 'CFB3_Coal_Use']].head(l_print))
        # print(df[['CFB3_Ratio', 'CFB3_Blending', 'CFB3_Coal_Use']].tail(l_print))
    else:
        print('No feasible solution')
    
    exec_time = (datetime.now() - start_dt)
    print('Execution time = {} sec'.format(exec_time.total_seconds()))
