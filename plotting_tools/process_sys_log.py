import pathlib
import sys
import pandas as pandas
import plotly.express as px
import math
import numpy as np
import plotly.graph_objects as go
from kaleido.scopes.plotly import PlotlyScope
scope = PlotlyScope()
import os
# Plots the tick over time for all servers in one iteration

num_cores = 0
if len(sys.argv) < 2:
    print("Error! Number of CPU not given, defaulting to 2")
    num_cores = 2
else:
    num_cores = int(sys.argv[1])

template = "plotly_white"

parent = pathlib.Path(os.path.abspath(__file__)).parent.parent.absolute()
root = parent / "results"
assert root.is_dir()
output_dir = parent / "plots"
assert output_dir.is_dir()
current_server = None

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
            if curr_data_file.startswith("sys_metrics"):
                worlds.add(world)

                iteration_df = pandas.read_csv(data_file, sep="\t")
                iteration_df['server'] = current_server
                iteration_df['iteration'] = '0'
                iteration_df['world'] = world
                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min())
                iteration_df = iteration_df[(iteration_df["timestamp"] >= 0)]
                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x / 1000) # To S

                iteration_df["proc.cpu_percent"] = iteration_df["proc.cpu_percent"].transform(lambda x: x/(num_cores * 100))
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

        curr_fig.add_trace(go.Scatter(x=server_df["timestamp"],mode='markers+lines', y=server_df["proc.cpu_percent"],showlegend=True, line=line_type, name=server,line_shape="linear"))

    curr_fig.update_layout(legend=dict(y=1,font_size=16, traceorder='reversed'), width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0), font=dict(size=16), xaxis_title="CPU utilization [%]", yaxis_title="Tick time [ms]")
    curr_fig.update_layout(legend=dict(
        orientation="h",
        yanchor="top",
        y=-.15,
        xanchor="left",
        x=0
    ))

    with open(str(output_dir.joinpath(f"{world_name}_cpu_utilization.pdf")), "wb") as f:
        f.write(scope.transform(curr_fig, format="pdf"))
