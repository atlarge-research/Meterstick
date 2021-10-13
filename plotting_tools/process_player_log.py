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
only_still = True
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
            if curr_data_file.find("yardstick") != -1:
                worlds.add(world)
                data_file_split = curr_data_file.split('_')
                curr_yardstick_id = data_file_split[0]
                curr_player = data_file_split[1]
                iteration_df = pandas.read_csv(data_file, sep=",")
                if only_still and curr_player != 'still':
                    continue

                iteration_df['server'] = current_server
                iteration_df['world'] = world
                iteration_df['iteration'] = '0'
                iteration_df['yardstick_id'] = curr_yardstick_id
                iteration_df['player'] = curr_player

                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min()) # elapsed time

                if not only_still:
                    iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - (10000 - 1000 * int(curr_player))) # Cut joining players duration
                iteration_df = iteration_df[iteration_df["timestamp"] >= 0]


                iteration_df = iteration_df.query('name == "ClientChatPacket" or name == "ServerChatPacket"')


                df = df.append(iteration_df, ignore_index = True)

df['rtt'] = -10
df = df.astype({'message':np.str})
df['message'] = df['message'].transform(lambda x: x[-5:] if len(x) > 0 else x)


fig = go.Figure()
fig_net_violin = go.Figure()

server_num = 0
traces = []
to_add = []
First=True
for world in worlds:
    exp_df = df[df["world"] == world]

    for server in servers:
        curr_df = exp_df[exp_df["server"] == server]

        curr_df = curr_df[curr_df["timestamp"] >=0]


        total_messages = len(curr_df[curr_df['name'] == "ClientChatPacket"])
        fraction_amount = 1 / total_messages

        for i,row in curr_df.iterrows():
            if row['name'] == "ClientChatPacket":
                resp = curr_df.query(f'message == "{row["message"]}" and name == "ServerChatPacket"')
                if len(resp) > 0:
                    rtt = resp['timestamp'].values[0] - row['timestamp']
                    curr_df.loc[i, ['rtt']] = rtt
                #else:
                    #print("Packet without response!")

        curr_df = curr_df[curr_df['name'] == "ClientChatPacket"]
        curr_df = curr_df.sort_values('rtt')
        curr_df = curr_df[curr_df['rtt'] != -10]
        curr_df["fraction"] = fraction_amount
        curr_df['rolling_sum'] = curr_df['fraction'].cumsum()


        curr_color = "red"
        curr_line_color="darkred"
        line_type = dict(color=curr_color,width=2)
        symbol = "diamond"
        if server_num == 1:
            curr_color="lightblue"
            curr_line_color="blue"
            line_type = dict(color=curr_color,width=2)
            symbol = "circle"
        elif server_num == 2:
            curr_color="lightgreen"
            curr_line_color="green"
            line_type = dict(color=curr_color,width=2)
            symbol = "square"
        server_num+=1

        fig.add_trace(go.Scatter(y=curr_df['rolling_sum'], x=curr_df['rtt'], line=line_type, name=f"{world} {server}"))
        curr_df['server'] = f"{world} {server}"
        if First:
            to_add.append(go.Box(x=[0], y=["n"],line=dict(color=curr_line_color),fillcolor=curr_color,xaxis='x2',name= server, showlegend =True))
        traces.append(
            go.Violin(x=curr_df['rtt'],
                    y=curr_df['server'],
                    name=server,
                    box_visible=True,
                    line_color='rgba(255,255,255,0)',
                    fillcolor='rgba(255,255,255,0)',
                    marker_color=curr_line_color,
                    box = dict(
                        line=dict(color=curr_line_color),
                        fillcolor=curr_color,
                        width = .75
                    ),
                    #meanline = dict(color="#f704ef"),
                    spanmode='hard',
                    points='outliers',
                    width=.9,
                    meanline_visible=True,
                    showlegend=False)
        )
        traces.append(
            go.Violin(x=curr_df['rtt'],
                    y=curr_df['server'],
                    name=server,
                    box_visible=True,
                    line_color='rgba(255,255,255,0)',
                    fillcolor='rgba(255,255,255,0)',
                    marker_color=curr_line_color,
                    box = dict(
                        line=dict(color=curr_line_color),
                        fillcolor=curr_color,
                        width = .75
                    ),
                    #meanline = dict(color="#f704ef"),
                    spanmode='hard',
                    points='outliers',
                    width=.9,
                    meanline_visible=True,
                    xaxis="x2",
                    showlegend=False)
        )
        traces.append(
            go.Scatter(x=[curr_df['rtt'].mean()],
                    y=curr_df['server'],
                    marker=dict(symbol='diamond',color='#ed28c9', size= 8),
                    xaxis="x",
                    showlegend=False)
        )
        traces.append(
            go.Scatter(x=[curr_df['rtt'].mean()],
                    y=curr_df['server'],
                    marker=dict(symbol='diamond',color='#ed28c9', size= 8),
                    mode="markers",
                    xaxis="x2",
                    showlegend=False)
        )
    First=False
    server_num = 0
for t in to_add:
    traces.append(t)
traces.append(
    go.Scatter(x=[0],
            y=["n"],
            marker=dict(symbol='diamond',color='#ed28c9', size = 8),
            mode="markers",
            name="Mean",
            xaxis="x2",
            showlegend=True)
)
traces.append(go.Scatter(x=[60,60], y=["n","m"], mode='lines',line=dict(color='orange',width=3),name= 'Noticable', showlegend =True))
traces.append(go.Scatter(x=[118,118], y=["n","m"], mode='lines',line=dict(color='red',width=3),name= 'Unplayable', showlegend =True))


order_array = ['n']
for world in worlds:
    for server in servers:
        order_array.append(f"{world} {server}")
order_array.append('m')

layout = go.Layout(
    yaxis=dict(
        domain = [.1, .98],
        categoryorder='array',
        categoryarray=order_array,
        dtick=1,
        range=[.5,len(order_array)-1.5],
        showticklabels=True,
    ),
    xaxis=dict(
        domain = [.05, .66],
        title="Game response time [ms]",
        range = [0,220]
    ),
    xaxis2=dict(
        domain = [.7, 1],
        range = [221,1500]
    )
)



fig_violin = go.Figure(traces, layout)

fig_violin.update_traces(orientation='h')

fig_violin.update_layout(width = 600, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0))
fig_violin.update_layout(font=dict(size=16, family="Liberation Sans"))

fig_violin.update_layout(legend=dict(
    title='',
    orientation="h",
    yanchor="top",
    #y=-.02,
    xanchor="left",
    #x=0
))

fig_violin.add_annotation(
                    x=0,
                    ax=90,
                    ay=0,
                    y=len(order_array)-2.2,
                    #yref="paper",
                    text="<i>Lower is better</i>",
                    yshift=22,
                    font=dict(size=16),
                    arrowhead=1,
                    arrowsize=2,
                    textangle=0)

with open(str(output_dir.joinpath("game_response_time.pdf")), "wb") as f:
    f.write(scope.transform(fig_violin, format="pdf"))
