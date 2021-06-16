import pathlib

import pandas as pandas
import plotly.express as px
import math
import plotly.graph_objects as go
from kaleido.scopes.plotly import PlotlyScope
scope = PlotlyScope()
import os
# Plots the tick over time for each server with many iterations

template = "plotly_white"

root = pathlib.Path(os.path.abspath(__file__)).parent.absolute()
assert root.is_dir()
output_dir = root
current_server = None

# Populate a dataframe from all servers
df = pandas.DataFrame(columns = ["host","server","iteration","timestamp","tickTime"])

servers = ["PaperMC", "Forge", "Vanilla"]


traces = []

hosts =  ['DAS5', 'AWS', 'Azure']
show_legend = True
host_num = 0
for host in hosts:
    curr_root = root.joinpath(f"results_{host}_50iter")

    curr_yaxis = 'y'
    if host_num == 1:
        curr_yaxis = 'y2'
    if host_num == 2:
        curr_yaxis = 'y3'

    server_num = 0

    for server_dir in os.listdir(curr_root):
        server_path = curr_root.joinpath(server_dir)
        if os.path.isdir(server_path):
            current_server = server_dir
            
            for iteration_dir in os.listdir(server_path):
                iteration_path = server_path.joinpath(iteration_dir)
                
                for data_file in os.listdir(iteration_path):
                    if not os.path.isdir(data_file) and data_file.startswith("tick_log"):
                        data_path = iteration_path.joinpath(data_file) 
                        
                        iteration_df = pandas.read_csv(data_path, sep=",")
                    
                        iteration_df.rename(columns = {' tickTime':'tickTime'}, inplace = True)
                        iteration_df.drop(iteration_df.columns[2],axis = 1,inplace = True)

                        iteration_df['server'] = current_server
                        iteration_df['host'] = host
                        iteration_df['iteration'] = '0'
                        iteration_df['tickTime'] = iteration_df['tickTime'].transform(lambda x: x / 1000000) # To MS
                        iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min())
                        iteration_df = iteration_df[(iteration_df["timestamp"] >= 0)]

                        # Adjust for samples with long ticks
                        curr_start = 0
                        curr_end = 50
                        max_index = len(iteration_df)
                        while curr_end <= max_index:
                            curr_df = iteration_df.iloc[curr_start:curr_end]
                            num_skipped = curr_df[curr_df['tickTime'] < 0]['tickTime'].count()
                            if num_skipped == 0:
                                curr_start = curr_end
                                curr_end = curr_start + 50
                                continue
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
                        #iteration_df = iteration_df[iteration_df["timestamp"] <= 56] # Don't count player logging out
                        #iteration_df.insert(0, 's_ID', range(0, 0 + len(iteration_df)))
                        
                        
                        err_df = iteration_df[(iteration_df["tickTime"] <= 0)] # Get all -1 vals
                        iteration_df = iteration_df[(iteration_df["tickTime"] >= 0)] # Remove all -1 vals
                        iteration_df = iteration_df[(iteration_df["tickTime"] < 500)] # Remove the save tick

                        iteration_df['rolling'] = iteration_df['tickTime'].rolling(50).mean() # Mean of ~2.5 sec

                        symbol = "diamond"
                        curr_color = "red"
                        line_type = dict(color=curr_color,width=2)
                        join_time = 28
                        curr_xaxis = 'x'
                        if server_num == 1:
                            symbol = "circle"
                            curr_color='blue'
                            line_type = dict(color=curr_color,width=2)
                            join_time = 26
                            curr_xaxis = 'x2'
                        elif server_num == 2:
                            symbol = "square"
                            curr_color='green'
                            line_type = dict(color=curr_color,width=2)
                            join_time = 26
                            curr_xaxis = 'x3'

                        iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - join_time) # Took a few seconds for players to join
                        iteration_df = iteration_df[iteration_df["timestamp"] >= 0]
                        #iteration_df = iteration_df[iteration_df["timestamp"] <= 52]
                        
                        #outlier_df=iteration_df[(iteration_df["tickTime"] >= iteration_df['rolling'] + 50)]

                        traces.append(go.Scatter(x=iteration_df["timestamp"],y=iteration_df["rolling"], mode='lines', line=line_type, xaxis=curr_xaxis, yaxis=curr_yaxis,name=current_server, opacity = 0.1, showlegend=False, line_shape="spline"))
                        traces.append(go.Scatter(x=[0,52],y=[50,50], mode='lines', showlegend=show_legend,yaxis=curr_yaxis, xaxis=curr_xaxis, line=dict(color='black', dash='dash',width=2),name='Overloaded Point'))
                        show_legend = False
                        
                        #for i, row in outlier_df.iterrows():
                        #    if row['tickTime'] <= 500:
                        #        traces.append(go.Scatter(x=[ row["timestamp"] ],y=[row['tickTime']],mode="markers",yaxis=curr_axis,marker=dict(color=curr_color, symbol=symbol,size=8),showlegend=False))
                            #else:
                                #fig_line.add_trace(go.Scatter(x=[ row["timestamp"] ],y=[100 + offset],mode="markers+text",marker=dict(color=curr_color, symbol=symbol,size=8),text=int(row['tickTime']),textposition="middle left",showlegend=False))
            server_num +=1

    host_num+=1


                        
layout = go.Layout(
    xaxis=dict(
        domain = [.0, .31],
        range = [0, 52]
    ),
    xaxis2=dict(
        domain = [.33, .63],
        range = [0, 52],
        title = "time [s]"
    ),
    xaxis3=dict(
        domain = [.65, .95],
        range = [0, 52]
    ),
    yaxis=dict(
        domain = [.0, .31],
        range = [0,149],
        dtick =50,
        #tick0 =10,
        #title = "PaperMC"
    ),
    yaxis2=dict(
        domain = [.33, .63],
        range = [0,149],
        dtick = 50,
        #tick0=10,
        title = "tick time, sliding window average [ms]"
    ),
    yaxis3=dict(
        domain = [.65, .95],
        range = [0,149],
        dtick =50,
        #tick0=10,
        #title = "Vanilla"
    )
)

fig = go.Figure(traces, layout)
fig.add_annotation(xref='paper',
                    x=.98,
                    y=.1,
                    yref="paper",
                    text="DAS5",
                    textangle=90,
                    yshift=-1,
                    showarrow=False)
fig.add_annotation(xref='paper',
                    x=.98,
                    y=.5,
                    yref="paper",
                    text="AWS",
                    yshift=0,
                    textangle=90,
                    showarrow=False)
fig.add_annotation(xref='paper',
                    x=.98,
                    y=.85,
                    yref="paper",
                    text="Azure",
                    yshift=8,
                    textangle=90,
                    showarrow=False)
fig.add_annotation(xref='paper',
                    x=.09,
                    y=1,
                    yref="paper",
                    text="PaperMC",
                    yshift=10,
                    showarrow=False)
fig.add_annotation(xref='paper',
                    x=.49,
                    y=1,
                    yref="paper",
                    text="Forge",
                    yshift=10,
                    showarrow=False)
fig.add_annotation(xref='paper',
                    x=.87,
                    y=1,
                    yref="paper",
                    text="Vanilla",
                    yshift=10,
                    showarrow=False)


fig.update_layout(font=dict(size=16),width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0), 
legend=dict(
    orientation="h",
    yanchor="top",
    y=-.08,
    xanchor="left",
    x=0
))


with open(str(output_dir.joinpath("multi_50iter_tick_line.pdf")), "wb") as f:
    f.write(scope.transform(fig, format="pdf"))
                


