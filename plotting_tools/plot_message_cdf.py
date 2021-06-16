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



servers = []
server_num = 0


# Only take data from the player who was standing still
only_still=True

fig_cdf = go.Figure()

for server_dir in os.listdir('../results'):
    if os.path.isdir(server_dir):
        current_server = server_dir
        servers.append(current_server)
        # For only one iteration
        iteration_dir = server_dir + "/0"
        df = pandas.DataFrame(columns = ["server","iteration","yardstick_id","player","timestamp","message"])
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

                iteration_df = iteration_df[iteration_df['outgoing'] == False] # Only want incoming
                iteration_df.rename(columns = {'name':'message'}, inplace = True) # Rename name to message
                
                iteration_df = iteration_df[iteration_df['message'] == measured_message] # Only care about one type of message

                iteration_df.drop(['length','outgoing'], axis = 1, inplace = True) # Don't need length or outgoing fields
                iteration_df['server'] = current_server
                iteration_df['iteration'] = '0'
                iteration_df['yardstick_id'] = curr_yardstick_id
                iteration_df['player'] = curr_player
                
                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - x.min()) # elapsed time
                iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x / 1000) # To Seconds

                if not only_still:
                    iteration_df['timestamp'] = iteration_df['timestamp'].transform(lambda x: x - (10000 - 1000 * int(curr_player))) # Cut joining players duration
                iteration_df = iteration_df[iteration_df["timestamp"] >= 0]
                iteration_df = iteration_df[iteration_df["timestamp"] <= 275000] # Don't count player logging out

                iteration_df['diff'] = iteration_df['timestamp'].diff()
                #iteration_df['count'] = 0
                iteration_df['percent'] = 0
                #iteration_df = iteration_df[iteration_df['diff'] > 10]
                #iteration_df['count'] = iteration_df.index + 1 # Count of how many of specific message
                #iteration_df.insert(0, 'count', range(1, 1 + len(iteration_df)))

                # Count total messages
                total = iteration_df['message'].size
                for diff_val in iteration_df['diff'].drop_duplicates():
                    diff_df = iteration_df[iteration_df['diff'] == diff_val]
                    # Find percent attributed to one diff
                    #iteration_df.loc[diff_df.index, ['count']] = diff_df['message'].size 
                    iteration_df.loc[diff_df.index, ['percent']] = diff_df['message'].size / total

                iteration_df = iteration_df.sort_values('diff')
                iteration_df = iteration_df.drop_duplicates('diff')
                iteration_df = iteration_df[iteration_df['diff'] < 13]

                iteration_df['percent_sum'] = iteration_df['percent'].cumsum()

                df = df.append(iteration_df, ignore_index = True)


        curr_color = "red"
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

        fig_cdf.add_trace(go.Scatter(y=df['percent_sum'], x=df['diff'], line=line_type, name=current_server))
        """df = df.sort_values(by=['player'])
        fig_violin = px.violin(df, y='diff', x='player', color='player', box=False, points="outliers")
        fig_violin.update_traces(showlegend=False)
        fig_violin.update_layout(yaxis_title="Inter-arrival message time", xaxis_title='Player ID', font=dict(size=16))

        with open(str(output_dir.joinpath(f"{current_server}_message_violin.pdf")), "wb") as f:
            f.write(scope.transform(fig_violin, format="pdf"))

        
        fig = px.scatter(df, y="diff", x='timestamp', color='player')

        with open(str(output_dir.joinpath(f"{current_server}_message_scatter.pdf")), "wb") as f:
            f.write(scope.transform(fig, format="pdf"))
        """
        

fig_cdf.update_layout(yaxis_title="CDF of MultiBlockChange",width = 800, height= 400, margin = dict(l=10,r=10,b=10,t=10,pad=0), xaxis_title='interpacket arrival time [s]', font=dict(size=16))
fig_cdf.update_traces(mode='lines+markers')

with open(str(output_dir.joinpath(f"messages_cdf.pdf")), "wb") as f:
    f.write(scope.transform(fig_cdf, format="pdf"))
