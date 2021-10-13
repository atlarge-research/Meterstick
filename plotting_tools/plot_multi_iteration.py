import pathlib
import sys
import pandas as pandas
import plotly.express as px
import math
import plotly.graph_objects as go
from kaleido.scopes.plotly import PlotlyScope
import numpy as np
scope = PlotlyScope()
import os
# Plots the tick over time for each server with many iterations
num_players = 0
if len(sys.argv) < 2:
    print("Error! Number of players not given, defaulting to 1")
    num_players = 1
else:
    num_players = int(sys.argv[1])

template = "plotly_white"


parent = pathlib.Path(os.path.abspath(__file__)).parent.parent.absolute()
root = parent / "results"
assert root.is_dir()
output_dir = parent / "plots"
assert output_dir.is_dir()
current_server = None

# Populate a dataframe from all servers
df = pandas.DataFrame(columns = ["world","server","iteration","timestamp","tickTime"])

servers = ["PaperMC", "Forge", "Minecraft"]

def jitter(x):
    return abs(max(50,x[1]) - max(50, x[0]))

traces = []

show_legend = True

servers = set()
worlds = set()
server_num = 0
world_num = 0
first = True
for server_dir in [x for x in root.iterdir() if x.is_dir()]:
    current_server = server_dir.parts[-1]
    servers.add(current_server)
    iteration=0

    for iteration_dir in [x for x in server_dir.iterdir() if x.is_dir()]:
        iteration = iteration_dir.parts[-1]
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
                    iteration_df['iteration'] = iteration
                    iteration_df['world'] = world
                    iteration_df['tickTime'] = iteration_df['tickTime'].transform(lambda x: x / 1000000) # To MS
                    iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min())
                    iteration_df = iteration_df[(iteration_df["timestamp"] >= 0)]


                    iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x / 1000) # To S


                    err_df = iteration_df[(iteration_df["tickTime"] <= 0)] # Get all -1 vals
                    iteration_df = iteration_df[(iteration_df["tickTime"] >= 0)] # Remove all -1 vals

                    symbol = "diamond"
                    curr_color = "red"
                    line_type = dict(color=curr_color,width=2)
                    join_time = num_players + 2
                    curr_xaxis = 'x'
                    if server_num == 1:
                        symbol = "circle"
                        curr_color='blue'
                        line_type = dict(color=curr_color,width=2)
                        curr_xaxis = 'x2'
                    elif server_num == 2:
                        symbol = "square"
                        curr_color='green'
                        line_type = dict(color=curr_color,width=2)
                        curr_xaxis = 'x3'


                    #iteration_df = iteration_df[iteration_df["timestamp"] <= 52]
                    iteration_df['tickTime_adj'] = iteration_df['tickTime'].transform(lambda x: x if x > 50 else 50) # Include tickWait

                    iteration_df['jitter'] = iteration_df['tickTime_adj'].rolling(window=2,min_periods=2).apply(lambda x: jitter(x), raw=True)
                    iteration_df['jitter'] = iteration_df['jitter'].transform(lambda x: 0 if math.isnan(x) else x)

                    iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - join_time) # Took a few seconds for players to join
                    iteration_df = iteration_df[iteration_df["timestamp"] >= 0]

                    df = df.append(iteration_df, ignore_index = True)
    server_num +=1

stabilities=pandas.DataFrame(columns = ["world","server","iteration","jitter","normalized_jitter","performance_avg"])

df = df.astype({'iteration':np.int})

for world in worlds:
    world_df = df[df['world'] == world]
    for server in servers:
        server_df = world_df[world_df['server'] == server]

        for iteration_num in range(0,int(server_df['iteration'].max())):
            iter_df = server_df[server_df['iteration'] == iteration_num]
            jitter_score = iter_df['jitter'].sum()
            tick_sum = iter_df['tickTime_adj'].sum()

            ticks_expected = tick_sum // 50
            normalized_jitter = jitter_score / (ticks_expected * 2*50)

            performance_avg = iter_df['tickTime'].mean()

            stabilities.loc[len(stabilities.index)] = [world, server, iteration_num, jitter_score, normalized_jitter, performance_avg]

fig = px.box(stabilities, y='world', x="normalized_jitter",color='server',
labels={"server":"Server:","normalized_jitter":"Normalized Jitter"}
)

fig.update_layout(legend=dict(y=1,font_size=15), width = 400, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0))
fig.update_layout(font=dict(size=15, family="Liberation Sans"))

fig.update_layout(legend=dict(
    orientation="h",
    yanchor="top",
    y=-.18,
    xanchor="left",
    x=0
))
fig.update_layout(
    xaxis=dict(domain=[0,1], tickformat='.2f', title_standoff=0),
    yaxis=dict(domain=[.1,1],title_standoff=0,title_font_size=1)
)

with open(str(output_dir.joinpath(f"multi-iteration_jitter_ditribution.pdf")), "wb") as f:
    f.write(scope.transform(fig, format="pdf"))


fig = px.box(stabilities, y='world', x="performance_avg",color='server',
labels={"server":"Server:","performance_avg":"Mean tick time"}
)

fig.update_layout(legend=dict(y=1,font_size=15), width = 400, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0))
fig.update_layout(font=dict(size=15, family="Liberation Sans"))

fig.update_layout(legend=dict(
    orientation="h",
    yanchor="top",
    y=-.18,
    xanchor="left",
    x=0
))
fig.update_layout(
    xaxis=dict(domain=[0,1], title_standoff=0),
    yaxis=dict(domain=[.1,1],title_standoff=0,title_font_size=1)
)

with open(str(output_dir.joinpath(f"multi-iteration_tick_mean_ditribution.pdf")), "wb") as f:
    f.write(scope.transform(fig, format="pdf"))
