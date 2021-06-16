import pathlib

import pandas as pandas
import plotly.express as px
import plotly.graph_objects as go
from kaleido.scopes.plotly import PlotlyScope
scope = PlotlyScope()
import os


template = "plotly_white"

root = pathlib.Path(os.path.abspath(__file__)).parent.absolute()
assert root.is_dir()
output_dir = root
current_server = None

server_num = 0


# Only take data from the player who was standing still
only_still=True

df = pandas.DataFrame(columns = ["server","iteration","yardstick_id","player","timestamp","name","message"])

locations=["DAS5_Internal","AWS_Internal", "DAS5_Behaviour","AWS_Behaviour","AWS_Network"]

for location in locations:
    curr_root = root.joinpath(location)
    if os.path.isdir(curr_root):
        for server_dir in os.listdir(curr_root):
            server_path = curr_root.joinpath(server_dir)

            if os.path.isdir(server_path):
                current_server = server_dir
                # For only one iteration
                iteration_dir = server_path.joinpath("0")
                total = 0

                for data_file in os.listdir(iteration_dir):
                    if not os.path.isdir(data_file) and data_file.find("yardstick") != -1:
                        # Each file is a player
                        data_path = root.joinpath(iteration_dir).joinpath(data_file)
                        data_file_split = data_file.split('_')
                        curr_yardstick_id = data_file_split[0]
                        curr_player = data_file_split[1]
                        iteration_df = pandas.read_csv(data_path, sep=",")
                        if only_still and curr_player != 'still':
                            continue

                        #iteration_df = iteration_df[iteration_df['outgoing'] == False] # Only want incoming
                        #iteration_df.rename(columns = {'name':'message'}, inplace = True) # Rename name to message

                        #iteration_df.drop(['length','outgoing'], axis = 1, inplace = True) # Don't need length or outgoing fields
                        iteration_df['server'] = f"{current_server} {location}"
                        iteration_df['iteration'] = '0'
                        iteration_df['yardstick_id'] = curr_yardstick_id
                        iteration_df['player'] = curr_player
                        
                        iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min()) # elapsed time
                        iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x / 1000) # To Seconds

                        if not only_still:
                            iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - (10000 - 1000 * int(curr_player))) # Cut joining players duration
                        iteration_df = iteration_df[iteration_df["timestamp"] >= 0]

                        
                        #iteration_df = iteration_df[iteration_df['message'] == "ClientChatPacket"] # Only care about two types of message
                        iteration_df = iteration_df.query('name == "ClientChatPacket" or name == "ServerChatPacket"')
                        #iteration_df = iteration_df.query('length == 5 or length == 303 or length == 54')

                        #print(iteration_df)

                        df = df.append(iteration_df, ignore_index = True)


"""        curr_color = "red"
        line_type = dict(color=curr_color,width=2)
        symbol = "diamond"
        offset = 10
        if server_num == 1:
            curr_color="blue"
            line_type = dict(color=curr_color,width=2)
            symbol = "circle"
            offset = 5
        elif server_num == 2:
            curr_color="green"
            line_type = dict(color=curr_color,width=2)
            symbol = "square"
            offset = 0
        server_num +=1

        fig.add_trace(go.Scatter(y=df['percent_sum'], x=df['diff'], line=line_type, name=current_server))
print(df)
        

fig.update_layout(yaxis_title="round trip time [ms]",width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0), xaxis_title='time [s]', font=dict(size=16))

with open(str(output_dir.joinpath(f"messages_rtt.pdf")), "wb") as f:
    f.write(scope.transform(fig, format="pdf"))"""

df['rtt'] = -10
df['message'] = df['message'].transform(lambda x: x[-5:] if len(x) > 0 else x)


fig = go.Figure()
fig_violin= go.Figure()
server_num = 0
servers = ["PaperMC", "Forge", "Vanilla"]
for server in servers:
    for location in locations:
        server_loc = f"{server} {location}"
        curr_df = df[df['server'] == server_loc]

        curr_df['timestamp'] = curr_df['timestamp'].transform(lambda x: x - 26) # Remove joining time
        curr_df = curr_df[curr_df["timestamp"] >=0]

        total_messages = len(curr_df[curr_df['name'] == "ClientChatPacket"])
        fraction_amount = 1 / total_messages
        
        for i,row in curr_df.iterrows():
            if row['name'] == "ClientChatPacket":
                resp = curr_df.query(f'message == "{row["message"]}" and name == "ServerChatPacket"')
                if len(resp) > 0:
                    rtt = resp['timestamp'].values[0] - row['timestamp']
                    curr_df.loc[i, ['rtt']] = rtt
                else:
                    print("Packet without response!")
        
        curr_df = curr_df[curr_df['name'] == "ClientChatPacket"]
        curr_df = curr_df.sort_values('rtt')
        curr_df = curr_df[curr_df['rtt'] != -10]
        curr_df["fraction"] = fraction_amount
        curr_df['rolling_sum'] = curr_df['fraction'].cumsum()
        
        curr_color = "red"
        curr_line_color="darkred"
        line_type = dict(color=curr_color,width=2)
        symbol = "diamond"
        offset = 10
        if server_num in range(5,10):
            curr_color="blue"
            curr_line_color="darkblue"
            line_type = dict(color=curr_color,width=2)
            symbol = "circle"
            offset = 5
        elif server_num in range(10,15):
            curr_color="green"
            curr_line_color="darkgreen"
            line_type = dict(color=curr_color,width=2)
            symbol = "square"
            offset = 0
        server_num +=1
        
        print(curr_df)

        fig.add_trace(go.Scatter(y=curr_df['rolling_sum'], x=curr_df['rtt'], line=line_type, name=server_loc))
        outlier_df = curr_df[curr_df['rtt'] > 0.5]
        num_outlier = len(outlier_df)
        #curr_df = curr_df[curr_df['rtt'] <= 0.5]
        fig_violin.add_trace(go.Violin(x=curr_df['server'],
                                y=curr_df['rtt'],
                                name=server_loc,
                                box_visible=True,
                                line_color=curr_line_color,
                                fillcolor=curr_color,
                                spanmode='hard',
                                points='outliers',
                                meanline_visible=True))
        """fig_violin.add_annotation(
                        x=server_loc,
                        y=0.5,
                        ay=0.44,
                        ayref='y',
                        axref='pixel',
                        ax=40,
                        arrowhead=1,
                        arrowwidth=2,
                        arrowside='end',
                        xshift=10,
                        text=f"Outliers: {num_outlier}",
                        showarrow=True
                        )"""


fig.update_layout(yaxis_title="percent of messages (CDF)", width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0), xaxis_title='round trip time [s]', font=dict(size=16))
fig.update_traces(mode='lines+markers')

with open(str(output_dir.joinpath(f"messages_rtt_cdf.pdf")), "wb") as f:
    f.write(scope.transform(fig, format="pdf"))


fig_violin.update_layout(yaxis_title="round trip time [s]", yaxis=dict(
        range = [0,.5]
    ),width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0), font=dict(size=16))

fig_violin.update_traces(showlegend=False)


with open(str(output_dir.joinpath("rtt_violin.pdf")), "wb") as f:
    f.write(scope.transform(fig_violin, format="pdf"))


