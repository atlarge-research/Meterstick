import pathlib
import math

import pandas as pandas
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from kaleido.scopes.plotly import PlotlyScope
scope = PlotlyScope()
import os
import re



def parse_file(in_file):
    in_profile = False
    in_world = False
    start_re = re.compile(r'.* BEGIN PROFILE DUMP .*\n')
    end_re = re.compile(r'.* END PROFILE DUMP .*\n')
    tick_wait_re = re.compile(r'\[00\] nextTickWait.*\n')
    #tick_re = re.compile(r'\[00\] tick.*\n')
    world_re = re.compile(r'\[02\].*overworld.*\n')
    world_end_re = re.compile(r'\[02\].*\n')
    world_val_re = re.compile(r'\[04\].*\n')
    val_name_re = re.compile(r'.[a-zA-Z]*\(|.world border\(|.\#[a-zA-Z]*')

    percent_re = re.compile(r'\d*\.\d*\%\n')

    to_return = [] # Tuple list, ("name", percent)

    with open(in_file, 'r') as file_object:
        line = file_object.readline()
        while line:
            #print(line)
            if not in_profile and start_re.match(line):
                in_profile = True
            elif in_profile and end_re.match(line):
                break
            if tick_wait_re.match(line):
                #print(line)
                percent = percent_re.search(line).group(0)[:-2]
                to_return.append( ("nextTickWait", float(percent)) )

            #if tick_re.match(line):
                #print(line)
                #percent = percent_re.search(line).group(0)[:-2]
                #to_return.append( ("Tick", percent) )

            if not in_world and world_re.match(line):
                in_world = True
            elif in_world and world_end_re.match(line):
                in_world = False
            if in_world and world_val_re.match(line):
                val_name = val_name_re.search(line).group(0)
                val_name = val_name[1:-1]
                if val_name[0] != '#':
                    percent = percent_re.search(line).group(0)[:-2]
                    #print(f"{line}: gives {val_name}, {percent}")
                    if float(percent) > 0.5:
                        to_return.append( (val_name, float(percent)) )

            line = file_object.readline()

    return to_return

parent = pathlib.Path(os.path.abspath(__file__)).parent.parent.absolute()
root = parent / "results"
assert root.is_dir()
output_dir = parent / "plots"
assert output_dir.is_dir()
current_server = None
num = 1

traces = []

servers = set()
worlds = set()
server_num = 0
world_num = 0
first = True
df = pandas.DataFrame(columns = ["Name","Percent","server","iteration", "world"])
for server_dir in [x for x in root.iterdir() if x.is_dir()]:
    current_server = server_dir.parts[-1]
    servers.add(current_server)
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
            if curr_data_file.startswith("profile"):
                #print(f"STARTING SERVER {current_server}, WORLD: {world}")
                values = parse_file(data_file)
                new_df = pandas.DataFrame(values, columns = ["Name","Percent"])
                new_df['server'] = current_server
                new_df['iteration'] = '0'
                new_df['world'] = world
                df = df.append(new_df,ignore_index = True)



new_df = pandas.DataFrame(columns = ["Name","average","server", "world"])
for server, name in df.groupby(["world","server","Name"]):

    name['average'] = name['Percent'].mean(axis=0)
    name = name.drop_duplicates(subset=["Name", "server", "world"])
    new_df = new_df.append(name)
df = new_df
#print(df)

#labels = df["Name"].drop_duplicates()
for experiment_name in worlds:
    for server in servers:
        curr_group = df.loc[(df["server"] == server) & (df["world"] == experiment_name)]
        curr_group = curr_group.sort_values("Name")
        labels = curr_group["Name"].drop_duplicates()
        other  = 100 - curr_group["average"].sum()
        df = df.append({'Name' : 'Other' , 'average' : other, 'server': server, 'world' : experiment_name} , ignore_index=True)

df['rename'] = df['Name'].transform(lambda x: "Block Add/Remove" if x == 'blockEvents' else "Block Update" if x == "chunkSource" else "Entities" if x == "entities" else "Wait After" if x == "nextTickWait" else "Wait Before" if x == "tickPending" else x)

fig = px.bar(df, x='average',y='server', color='rename', facet_row = "world", orientation='h',labels={
                        "average": "Tick time [%]", "rename":"Operation:","server": ""},
                        color_discrete_sequence=["#c2bffc","#fcb2ab","#3e18f9","#fccff3","#fce0ab","#abfce2"])
fig.update_layout(font=dict(size=16), xaxis={'categoryorder':'category ascending'})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig.update_layout(legend=dict(y=1,font_size=16), width = 500, height= 600, margin = dict(l=10,r=10,b=10,t=10,pad=0))
fig.update_layout(font=dict(size=16, family="Liberation Sans"))
fig.update_layout(legend=dict(
    orientation="h",
    yanchor="top",
    y=-.11,
    xanchor="left",
    x=0
))

with open(str(output_dir.joinpath(f"tick_percents.pdf")), "wb") as f:
    f.write(scope.transform(fig, format="pdf"))
