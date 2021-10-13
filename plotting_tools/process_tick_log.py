import pathlib

import pandas as pandas
import plotly.express as px
import math
import numpy as np
import plotly.graph_objects as go
from kaleido.scopes.plotly import PlotlyScope
scope = PlotlyScope()
import os
# Plots the tick over time for all servers in one iteration

template = "plotly_white"

parent = pathlib.Path(os.path.abspath(__file__)).parent.parent.absolute()
root = parent / "results"
assert root.is_dir()
output_dir = parent / "plots"
assert output_dir.is_dir()
current_server = None

def jitter(x):
    return abs(max(50,x[1]) - max(50, x[0]))

# Populate a dataframe from all servers
df = pandas.DataFrame(columns = ["world","server","iteration","timestamp","tickTime"])
servers = set()
worlds = set()
server_num = 0
world_num = 0
first = True
for server_dir in [x for x in root.iterdir() if x.is_dir()]:
    current_server = server_dir.parts[-1]
    servers.add(current_server)
    # For only one iteration
    iteration_dir = server_dir / "0"

    curr_color = "red"
    line_type = dict(color=curr_color,width=2)
    symbol = "diamond"
    if server_num == 1:
        curr_color="blue"
        line_type = dict(color=curr_color,width=2)
        symbol = "circle"
    elif server_num == 2:
        curr_color="green"
        line_type = dict(color=curr_color,width=2)
        symbol = "square"
    server_num +=1
    world_num = 0

    for world_dir in [x for x in iteration_dir.iterdir() if x.is_dir()]:
        world = world_dir.parts[-1]
        for data_file in [x for x in world_dir.iterdir() if not x.is_dir()]:
            curr_data_file = data_file.parts[-1]
            if curr_data_file.startswith("tick_log"):
                worlds.add(world)

                iteration_df = pandas.read_csv(data_file, sep=",")
                iteration_df.rename(columns = {' tickTime':'tickTime'}, inplace = True)
                iteration_df.drop(iteration_df.columns[2],axis = 1,inplace = True)

                iteration_df['server'] = current_server
                iteration_df['iteration'] = '0'
                iteration_df['world'] = world
                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min())
                iteration_df = iteration_df[(iteration_df["timestamp"] >= 0)]
                iteration_df['tickTime'] = iteration_df['tickTime'].transform(lambda x: x / 1000000) # To MS

                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x / 1000) # To S

                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - 3) # Took a few seconds for players to join
                iteration_df = iteration_df[iteration_df["timestamp"] >= 0]

                err_df = iteration_df[(iteration_df["tickTime"] <= 0)] # Get all -1 vals
                iteration_df = iteration_df[(iteration_df["tickTime"] >= 0)] # Remove all -1 vals

                iteration_df['tickTime_adj'] = iteration_df['tickTime'].transform(lambda x: x if x > 50 else 50) # Include tickWait

                iteration_df['timestamp_adj'] = iteration_df['tickTime_adj'].cumsum()
                iteration_df['timestamp_adj'] = iteration_df['timestamp_adj'].transform(lambda x: x / 1000) # To S

                iteration_df['jitter'] = iteration_df['tickTime_adj'].rolling(window=2,min_periods=2).apply(lambda x: jitter(x), raw=True)
                iteration_df['jitter'] = iteration_df['jitter'].transform(lambda x: 0 if math.isnan(x) else x)

                df = df.append(iteration_df, ignore_index = True)

for world_name in worlds:
    curr_df = df[df['world'] == world_name]
    curr_fig = go.Figure()
    server_num = 0
    for server in servers:
        server_df = curr_df[curr_df['server'] == server]

        curr_color = "red"
        line_type = dict(color=curr_color,width=2)
        symbol = "diamond"
        if server_num == 1:
            curr_color="blue"
            line_type = dict(color=curr_color,width=2)
            symbol = "circle"
        elif server_num == 2:
            curr_color="green"
            line_type = dict(color=curr_color,width=2)
            symbol = "square"
        server_num +=1

        curr_fig.add_trace(go.Scatter(x=server_df["timestamp"],mode='markers+lines', y=server_df["tickTime"],showlegend=True, line=line_type, name=server,line_shape="linear"))

    curr_fig.add_trace(go.Scatter(x=[0,server_df["timestamp"].max()],y=[50,50], mode='lines', line=dict(color='black', dash='dash',width=2),showlegend=True,name='Overloaded Point'))
    curr_fig.update_layout(legend=dict(y=1,font_size=16, traceorder='reversed'), width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0), font=dict(size=16), xaxis_title="Time [S]", yaxis_title="Tick time [ms]")
    curr_fig.update_layout(legend=dict(
        orientation="h",
        yanchor="top",
        y=-.15,
        xanchor="left",
        x=0
    ))

    with open(str(output_dir.joinpath(f"{world_name}_tick_line.pdf")), "wb") as f:
        f.write(scope.transform(curr_fig, format="pdf"))

traces = []
server_num = 0

for server in servers:
    server_df =df[df['server'] == server]

    curr_color='red'
    curr_marker={'color':curr_color, 'symbol':'circle',"size":10}
    if server_num == 1:
        curr_color='blue'
        curr_marker={'color':curr_color, 'symbol':'square',"size":10}
    if server_num == 2:
        curr_color='green'
        curr_marker={'color':curr_color, 'symbol':'cross',"size":10}
    server_num += 1
    show_legend = True
    for world in worlds:
        world_df = server_df[server_df['world'] == world]
        jitter_score = world_df['jitter'].sum()
        performance_avg = world_df['tickTime'].mean()
        tick_sum = world_df['tickTime'].sum() # Eg runtime
        n_expected = tick_sum / 50
        normalized = jitter_score / (n_expected * 2*50)

        traces.append(go.Scatter(y=[world], x=[normalized], mode='markers',marker=curr_marker,name = server, showlegend = show_legend, yaxis ='y', xaxis = 'x2'))
        traces.append(go.Scatter(y=[world], x=[performance_avg], mode='markers',marker=curr_marker,name = server, showlegend = False, yaxis = 'y', xaxis = 'x'))
        show_legend = False


layout = go.Layout(
    yaxis=dict(
        domain = [.1, 1],
        #range=[0,2]
    ),
    xaxis=dict(
        # magnitude
        domain = [.04, .46],
        title = "Mean tick duration",
        tickformat='d'
    ),
    xaxis2=dict(
        # Jitter
        domain = [.54, .96],
        title = "Normalized jitter",
        tickformat='.2f'
    )
)

curr_fig = go.Figure(traces, layout)

curr_fig.update_layout(legend=dict(y=1,font_size=14), width = 400, height= 600, margin = dict(l=10,r=10,b=10,t=10,pad=0))
curr_fig.update_layout(font=dict(size=14, family="Liberation Sans"))

curr_fig.update_layout(legend=dict(
    title='Server:',
    orientation="h",
    yanchor="top",
    y=0,
    xanchor="left",
    x=0
))



with open(str(output_dir.joinpath("Jitter_and_tickmean.pdf")), "wb") as f:
    f.write(scope.transform(curr_fig, format="pdf"))
