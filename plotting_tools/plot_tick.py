import pathlib

import pandas as pandas
import plotly.express as px
import math
import plotly.graph_objects as go
from kaleido.scopes.plotly import PlotlyScope
scope = PlotlyScope()
import os
# Plots the tick over time for all servers in one iteration

template = "plotly_white"

root = pathlib.Path(os.path.abspath(__file__)).parent.absolute()
assert root.is_dir()
output_dir = root
current_server = None

def custom_round(x, base=50):
    return int(base * math.ceil(float(x)/base))


# Populate a dataframe from all servers
df = pandas.DataFrame(columns = ["server","iteration","timestamp","cpu"])
fig_line = go.Figure()
servers = []
server_num = 0

for server_dir in os.listdir('../results'):
    if os.path.isdir(server_dir):
        current_server = server_dir
        servers.append(current_server)
        # For only one iteration
        iteration_dir = server_dir + "/0"

        for data_file in os.listdir(iteration_dir):
            if not os.path.isdir(data_file) and data_file.startswith("tick_log"):
                data_path = root.joinpath(iteration_dir).joinpath(data_file)

                iteration_df = pandas.read_csv(data_path, sep=",")
                iteration_df.rename(columns = {' tickTime':'tickTime'}, inplace = True)
                iteration_df.drop(iteration_df.columns[2],axis = 1,inplace = True)
                
                iteration_df['server'] = current_server
                iteration_df['iteration'] = '0'
                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min())
                iteration_df = iteration_df[(iteration_df["timestamp"] >= 0)]
                iteration_df['tickTime'] = iteration_df['tickTime'].transform(lambda x: x / 1000000) # To MS
                
                # Adjust for samples with long ticks
                curr_start = 0
                curr_end = 50
                max_index = len(iteration_df)
                while curr_end <= max_index:
                        curr_df = iteration_df.iloc[curr_start:curr_end]
                        num_skipped = curr_df[curr_df['tickTime'] < 0]['tickTime'].count()
                        last_real = curr_end - num_skipped - 1
                        num_real = last_real - curr_start + 1
                        new_tick_dur = 2500/num_real
                        start_time = iteration_df.iloc[curr_start]['timestamp']
                        #print(f"Starts at {start_time}, {num_skipped} are skipped, intervals of {new_tick_dur}")
                        for i,row in curr_df.iterrows():
                           if i > last_real:
                               #iteration_df = iteration_df.drop([i])
                               pass
                           else:
                               iteration_df.loc[[i], ['timestamp']] = start_time + ((i-curr_start) * new_tick_dur)
                        curr_start = curr_end
                        curr_end = curr_start + 50
                        
                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x / 1000) # To S
                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - 28)
                iteration_df = iteration_df[(iteration_df["timestamp"] >= 0)]
                err_df = iteration_df[(iteration_df["tickTime"] <= 0)] # Get all -1 vals
                iteration_df = iteration_df[(iteration_df["tickTime"] >= 0)] # Remove all -1 vals
                iteration_df = iteration_df[(iteration_df["timestamp"] <= 300)]
                

                # Adjust timestamp for long ticks 
                #iteration_df["tickTime_adj"] = iteration_df['tickTime'].transform(lambda x: 50 if x < 50 else x)
                #iteration_df['timestamp_adj'] = iteration_df["tickTime_adj"].cumsum()
                #iteration_df['timestamp_adj'] = iteration_df['timestamp_adj'].transform(lambda x: x - x.min())
                #iteration_df['timestamp_adj'] = iteration_df['timestamp_adj'].transform(lambda x: x/1000) # to S
                
                #iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min())
                #iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x / 1000) # To S
                #iteration_df['timestamp_adj'] = iteration_df['timestamp_adj'].transform(lambda x: x - 28) # Took a few seconds for players to join
                #iteration_df = iteration_df[iteration_df["timestamp_adj"] >= 0]
                #iteration_df = iteration_df[iteration_df["timestamp"] <= 275] # Don't count player logging out
                
                iteration_df['rolling'] = iteration_df['tickTime'].rolling(50).mean() # Mean of ~2.5 sec
                
                outlier_df=iteration_df[(iteration_df["tickTime"] >= iteration_df['rolling'] + 50)]
                iteration_df = iteration_df[(iteration_df["tickTime"] < iteration_df['rolling'] + 500)] # Remove really big outliers, for violin plot

                print(iteration_df)

                #iteration_df['std'] = iteration_df['tickTime'].rolling(50).std() # std of the same period
                #iteration_df['err'] = iteration_df['std'].transform(lambda x: x / math.sqrt(50)) # calculate error of the average
                #iteration_df['err_low'] = iteration_df['rolling'] - iteration_df['err'] 
                #iteration_df['err_high'] = iteration_df['rolling'] - iteration_df['err'] 

                df = df.append(iteration_df, ignore_index = True)

                curr_color = "red"
                line_type = dict(color=curr_color,width=2)
                symbol = "diamond"
                offset = 20
                if server_num == 1:
                    curr_color="blue"
                    line_type = dict(color=curr_color,width=2)
                    symbol = "circle"
                    offset = 10
                elif server_num == 2:
                    curr_color="green"
                    line_type = dict(color=curr_color,width=2)
                    symbol = "square"
                    offset = 0
                server_num +=1
                fig_line.add_trace(go.Scatter(x=iteration_df["timestamp"],y=iteration_df["rolling"], line=line_type, name=current_server, line_shape="spline"))

                
                for i, row in outlier_df.iterrows():
                    if row['tickTime'] <= 500:
                        fig_line.add_trace(go.Scatter(x=[ row["timestamp"] ],y=[row['tickTime']],mode="markers",marker=dict(color=curr_color, symbol=symbol,size=8),showlegend=False))
                    else:
                        fig_line.add_trace(go.Scatter(x=[ row["timestamp"] ],y=[200 + offset],mode="markers+text",marker=dict(color=curr_color, symbol=symbol,size=8),text=int(row['tickTime']),textposition="middle left",showlegend=False))
                

                #fig_line.add_trace(go.Scatter(x=iteration_df["timestamp"],y=iteration_df["tickTime"], line=line_type, opacity=0.5,name=current_server))
                #fig_line.add_trace(go.Scatter(x=iteration_df["timestamp"],y=iteration_df["rolling"], line=line_type, name=current_server)) # average


#fig.update_traces(mode='lines+markers')

#fig.update_yaxes(tick0=0, dtick=100)
fig_line.add_trace(go.Scatter(x=[0,300],y=[50,50], mode='lines', line=dict(color='black', dash='dash',width=2),name='Overloaded Point'))
#fig_line.update_traces(mode='lines')

fig_line.update_layout(legend=dict(y=1,font_size=16), width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0),xaxis_title="time [s]", yaxis_title="tick time, rolling average [ms]", font=dict(size=16))


with open(str(output_dir.joinpath("tick_line.pdf")), "wb") as f:
    f.write(scope.transform(fig_line, format="pdf"))

fig_violin= go.Figure()
server_num = 0

for server in servers:
    curr_color = "red"
    curr_line_color="darkred"
    if server_num == 1:
        curr_color = "blue"
        curr_line_color="darkblue"
    elif server_num == 2:
        curr_color = "green"
        curr_line_color="darkgreen"
    elif server_num > 2:
        # For more than 3 servers, let default colors take over
        fig_violin.add_trace(go.Violin(x=df['server'][df['server'] == server],
                            y=df['tickTime'][df['server'] == server],
                            name=server,
                            box_visible=True,
                            meanline_visible=True))
        continue

    server_num += 1

    fig_violin.add_trace(go.Violin(x=df['server'][df['server'] == server],
                            y=df['tickTime'][df['server'] == server],
                            name=server,
                            box_visible=True,
                            line_color=curr_line_color,
                            fillcolor=curr_color,
                            points='outliers',
                            meanline_visible=True))
fig_violin.update_traces(showlegend=False)
fig_violin.update_layout(yaxis_title="tick time [ms]",width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0), font=dict(size=16))


with open(str(output_dir.joinpath("tick_violin.pdf")), "wb") as f:
    f.write(scope.transform(fig_violin, format="pdf"))
                


