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
    curr_root = root.joinpath(f"results_{host}_baseline")

    curr_axis = 'y'
    num_cores = 16
    if host_num == 1:
        curr_axis = 'y2'
        num_cores = 2
    if host_num == 2:
        curr_axis = 'y3'
        num_cores = 2

    server_num = 0

    for server_dir in os.listdir(curr_root):
        server_path = curr_root.joinpath(server_dir)
        if os.path.isdir(server_path):
            current_server = server_dir
            
            iteration_path = server_path.joinpath('0')
                
            for data_file in os.listdir(iteration_path):
                if not os.path.isdir(data_file) and data_file.startswith("sys_metrics"):
                    data_path = iteration_path.joinpath(data_file) 
                    
                    iteration_df = pandas.read_csv(data_path, sep="\t")
                

                    iteration_df['server'] = current_server
                    iteration_df['host'] = host
                    iteration_df['iteration'] = '0'
                    iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min())
                    iteration_df = iteration_df[(iteration_df["timestamp"] >= 0)]

   
                    iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x / 1000) # To S
                    #iteration_df = iteration_df[iteration_df["timestamp"] <= 56] # Don't count player logging out
                    #iteration_df.insert(0, 's_ID', range(0, 0 + len(iteration_df)))
                    
                    

                    iteration_df["proc.cpu_percent"] = iteration_df["proc.cpu_percent"].transform(lambda x: x/(num_cores * 100))

                    iteration_df['rolling'] = iteration_df["proc.cpu_percent"].rolling(5).mean() # Mean of ~2.5 sec

                    symbol = "diamond"
                    curr_color = "red"
                    line_type = dict(color=curr_color,width=2)
                    join_time = 28
                    if server_num == 1:
                        symbol = "circle"
                        curr_color='blue'
                        line_type = dict(color=curr_color,width=2)
                        join_time = 26
                    elif server_num == 2:
                        symbol = "square"
                        curr_color='green'
                        line_type = dict(color=curr_color,width=2)
                        join_time = 26
                    server_num +=1

                    iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - join_time) # Took a few seconds for players to join
                    iteration_df = iteration_df[iteration_df["timestamp"] >= 0]
                 

                    traces.append(go.Scatter(x=iteration_df["timestamp"],y=iteration_df["rolling"], line=line_type, yaxis=curr_axis,name=current_server, showlegend=show_legend, line_shape="spline"))

    show_legend = False
    host_num+=1


                        
layout = go.Layout(
    xaxis=dict(
        range = [0,300],
        dtick =50
    ),
    yaxis=dict(
        domain = [.0, .28],
        range = [0,1],
        dtick =.25,
        #tick0 =10,
        #title = "PaperMC"
    ),
    yaxis2=dict(
        domain = [.33, .62],
        range = [0,1],
        dtick = .25,
        #tick0=10,
        title = "CPU utilization, sliding window average [%]"
    ),
    yaxis3=dict(
        domain = [.67, .96],
        range = [0,1],
        dtick =.25,
        #tick0=10,
        #title = "Vanilla"
    )
)

fig = go.Figure(traces, layout)
fig.add_annotation(xref='paper',
                    x=.5,
                    y=.28,
                    yref="paper",
                    text="DAS5 (16 vCPU)",
                    yshift=-1,
                    showarrow=False)
fig.add_annotation(xref='paper',
                    x=.5,
                    y=.65,
                    yref="paper",
                    text="AWS (2 vCPU)",
                    yshift=0,
                    showarrow=False)
fig.add_annotation(xref='paper',
                    x=.5,
                    y=1,
                    yref="paper",
                    text="Azure (2 vCPU)",
                    yshift=8,
                    showarrow=False)


fig.update_layout(font=dict(size=16),width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0),xaxis_title="time [s]")


with open(str(output_dir.joinpath("multi_baseline_cpu_line.pdf")), "wb") as f:
    f.write(scope.transform(fig, format="pdf"))
                


