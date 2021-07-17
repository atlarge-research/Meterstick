import os
import sys
import pathlib
import argparse
import subprocess
import threading
import time
import socket
import logging

# Yardstick control server, receives control operations from controller server during experiment. 

logging.basicConfig(filename='results/ys_receive.log', filemode='w',level=logging.DEBUG)

class YS_Receive:
    def __init__(self, args):
        self.args = args
        self.iterationCounter = -1
        self.ys_pid = -1
        self.results_dir="results"
        self.server="None"
        self.world_name="None"
        self.id=args.yardstick_id

    def log(self, message):
        logging.info("%s, %d : %s", self.server, self.iterationCounter, message)

    # Sets the server name, makes a results folder
    def setServer(self,server_name):
        self.server=server_name
        self.results_dir= "results/" + self.server
        if os.path.isdir(self.results_dir):
            subprocess.check_output(f'rm -rf {self.results_dir}', shell=True)
        time.sleep(1)
        os.mkdir(self.results_dir)

    # Add configuration to yardstick.toml
    def initializeYardstick(self): 
        subprocess.check_output(f'cp base_yardstick.toml yardstick.toml', shell=True)
        file1 = open("yardstick.toml", "a")  # append mode
        file1.write(f"\nduration = {self.args.duration}\nbots = {self.args.num_players}\nboxDiameter={self.args.bounding_box}\n[game]\nhost = \"{self.args.server_ip}\"\nport = {self.args.mcport}\n")
        if self.args.workload:
            file1.write("[logging]\ndump-workload = true\n")
        file1.write(f"[experiment]\nid={self.args.behaviour}\n")
        file1.close()

    # Start player emulat subprocess
    def startYardstick(self):
        log_file = open(f'{self.results_dir}/{self.iterationCounter}/{self.world_name}/ys_out.txt','x')
        log_file.flush()
        ys_process= subprocess.Popen('java -jar yardstick.jar &',stdout=log_file, stderr=log_file, shell=True)
        self.ys_pid = ys_process.pid

    # Convert log file to CSV using Yardstick tool, can take a while
    # TODO: have yardstick directly write CSV?
    def convertMetrics(self):
        curr_player = 0
        for player_bin in os.listdir('./workload'):
            if player_bin.__contains__("still"):
                subprocess.check_output(f'java -jar yardstick.jar --csvdump --input workload/{player_bin} --output {self.results_dir}/{self.iterationCounter}/{self.world_name}/{self.id}_still_yardstick.csv', shell=True)
            else:
                subprocess.check_output(f'java -jar yardstick.jar --csvdump --input workload/{player_bin} --output {self.results_dir}/{self.iterationCounter}/{self.world_name}/{self.id}_{curr_player}_yardstick.csv', shell=True)
            curr_player += 1
            os.remove(f'./workload/{player_bin}')

    # Receive control message from control server
    def listenToSocket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((socket.gethostname(),self.args.controlport))
        server_socket.listen(5)
        logging.info("Listening for connections...")
        connection, address = server_socket.accept()
        while True:
            buf = connection.recv(64)
            if len(buf) > 0:
                word = buf.decode()
                if word[:11] == "set_server:":
                    server_name = word[11:]
                    self.log("Setting current server to "+server_name)
                    self.setServer(server_name)
                    self.iterationCounter = -1
                    connection.send(b"ok")
                elif word[:5] == "iter:":
                    iteration = int(word[5:])
                    self.log(f"Setting iteration to {iteration}")
                    self.iterationCounter = iteration

                    os.mkdir(f'./{self.results_dir}/{self.iterationCounter}')

                    connection.send(b"ok")
                elif word[:10] == "set_world:":
                    world_name = word[10:]
                    self.log(f"Setting world to {world_name}")
                    self.world_name = world_name
                    
                    os.mkdir(f'./{self.results_dir}/{self.iterationCounter}/{self.world_name}')

                    connection.send(b"ok")
                elif word == "connect":
                    self.log("Starting Yardstick...")
                    self.startYardstick()
                    connection.send(b"ok")
                elif word == "convert":
                    self.log("Converting metrics to csv...")
                    self.convertMetrics()
                    connection.send(b"ok")
                elif word == "keep_alive":
                    self.log("Keep alive received.")
                    connection.send(b"ok")
                elif word == "exit":
                    self.log("Connection ended.")
                    break
            else:
                self.log("Connection ended.")
                break



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('server_ip')
    parser.add_argument('num_players', type=int)
    parser.add_argument('-behaviour', '-b', type=int, default=4)
    parser.add_argument('-bounding_box', '-box', type=int, default=32)
    parser.add_argument('-yardstick_id', '-id', type=int, default=0)
    parser.add_argument('-workload', '-w', default=True)
    parser.add_argument('-duration', '-d', type=int, default=60)
    parser.add_argument('-controlport', '-c', type=int, default=25555)
    parser.add_argument('-mcport', '-m', type=int, default=25565)
   
    ys_receive = YS_Receive(parser.parse_args())
    ys_receive.initializeYardstick()
    ys_receive.listenToSocket()
