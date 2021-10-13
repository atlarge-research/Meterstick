import os
import sys
import pathlib
import argparse
import subprocess
import threading
import time
import socket
import logging
import signal
import tempfile
from mcrcon import MCRcon

# Minecraft control client, receives control operations from control server during experiment. 

logging.basicConfig(filename='results/mc_receive.log', filemode='w',level=logging.DEBUG)

class MC_Receive:
    def __init__(self, args):
        self.mc_pid = -1
        self.jmx_pid = -1
        self.sys_pid = -1
        self.args = args
        self.iterationCounter = -1
        self.sys_sampling_freq = 0.5 # In seconds
        self.results_dir="results"
        self.server="None"
        self.world_name="None"
        self.jmx_url="net.minecraft.server:type\=Server"
        self.server_dir=""
        self.current_jmx_port=args.jmxport_start


    def log(self,message):
        logging.info("%s, %d : %s", self.server, self.iterationCounter, message)

    def setServer(self,server_name):
        self.server=server_name
        self.results_dir= "results/" + self.server
        if not os.path.isdir(self.results_dir):
            os.mkdir(self.results_dir)

    def copyWorld(self):
        subprocess.check_output(f'cp -Tr worlds/{self.world_name} {self.server_dir.name}/world',shell=True)


    # Clear previous server files, copy server to correct temp location
    def copyServer(self):
        self.server_dir = tempfile.TemporaryDirectory()
        self.log(f"Temp folder is {self.server_dir.name}")
        subprocess.check_output(f'cp -Tr servers/{self.server} {self.server_dir.name}',shell=True)

    # Start server in correct working directory
    def startServer(self):
        currentDirectory = os.getcwd()
        mc_process = subprocess.Popen(f'cd {self.server_dir.name} ; ./run.sh {currentDirectory}/{self.results_dir}/{self.iterationCounter}/{self.world_name}/mc_out.txt -{self.args.ram} {self.current_jmx_port} {self.args.cpu_affinity}', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        mc_process_out, mc_process_err = mc_process.communicate()
        self.mc_pid = int(mc_process_out.decode())
        self.log(f"MCPID is {self.mc_pid}")
        if not self.check_pid(self.mc_pid):
            # Process not running
            self.log(f"FATAL: MCPID not running!")
            return False
        else:
            return True


    # Connect JMX profiler to running server
    def connectJMX(self):
        log_file = open(f'{self.results_dir}/{self.iterationCounter}/{self.world_name}/jmx_out.txt','x')
        log_file.flush()
        jmx_process = subprocess.Popen(f'java -jar jmx_client.jar {self.jmx_url} {self.current_jmx_port} {self.results_dir}/{self.iterationCounter}/{self.world_name} &', stdout=log_file, stderr=log_file, shell=True, preexec_fn=os.setsid)
        self.jmx_pid = jmx_process.pid
        self.log(f"JMXPID is {self.jmx_pid}")
        if not self.check_pid(self.jmx_pid):
            # Process not running
            self.log(f"FATAL: JMXPID not running!")
            return False
        else:
            return True


    # Connect system metric tool to running server
    def connectSys(self):
        log_file = open(f'{self.results_dir}/{self.iterationCounter}/{self.world_name}/sys_out.txt','x')
        log_file.flush()
        sys_process = subprocess.Popen(f'python3 sys_perf.py {self.mc_pid} {self.sys_sampling_freq} {self.results_dir}/{self.iterationCounter}/{self.world_name} &', stdout=log_file, stderr=log_file, shell=True, preexec_fn=os.setsid)
        self.sys_pid = sys_process.pid
        if not self.check_pid(self.sys_pid):
            # Process not running
            self.log(f"FATAL: SYSPID not running!")
            return False
        else:
            return True
    
    # Uses RCON protocol to send control messages to server, defaults port to 25575
    def sendRCON(self, message):
        with MCRcon("127.0.0.1", "Meterstick") as mcr:
            resp = mcr.command(f"{message}")
            self.log(f"RCON response: {resp}")

        
    def stopServer(self):
        # Uses a process group to hopefully stop it from holding onto the port
        killed=False
        if self.check_pid(self.mc_pid):
            os.killpg(os.getpgid(self.mc_pid), signal.SIGTERM)
            killed=True
        self.current_jmx_port+=1
        if self.current_jmx_port > self.args.jmxport_end:
            self.current_jmx_port = self.args.jmxport_start
        return killed


    # Stops JMX, Sys and debug metrics
    def stopMetricSampling(self):
        # Stop debug profiling
        if self.args.debug_profile != 0:
            self.sendRCON("debug stop")
            subprocess.check_output(f'cp -Tr {self.server_dir.name}/debug {self.results_dir}/{self.iterationCounter}/{self.world_name}',shell=True)

        res = self.check_pid(self.jmx_pid)
        if res:
            os.killpg(os.getpgid(self.jmx_pid), signal.SIGTERM)
        return res

    # 'pings' a pid for existence
    def check_pid(self, pid):        
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    # Receives control messages from control server
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
                elif word[:8] == "set_jmx:":
                    jmx_url = word[8:]
                    self.log("Setting jmx_url to "+jmx_url)
                    self.jmx_url = jmx_url
                    connection.send(b"ok")
                elif word[:5] == "iter:":
                    iteration = int(word[5:])
                    self.log(f"Setting iteration to {iteration}")
                    self.iterationCounter = iteration

                    if os.path.isdir(f'{self.results_dir}/{self.iterationCounter}'):
                        subprocess.check_output(f'rm -rf {self.results_dir}/{self.iterationCounter}', shell=True)
                        time.sleep(1)
                    os.mkdir(f'{self.results_dir}/{self.iterationCounter}')

                    connection.send(b"ok")
                elif word[:10] == "set_world:":
                    world_name = word[10:]
                    self.log("Setting world to "+world_name)
                    self.world_name = world_name

                    if os.path.isdir(f'{self.results_dir}/{self.iterationCounter}/{self.world_name}'):
                        subprocess.check_output(f'rm -rf {self.results_dir}/{self.iterationCounter}/{self.world_name}', shell=True)
                        time.sleep(1)
                    os.mkdir(f'{self.results_dir}/{self.iterationCounter}/{self.world_name}')

                    connection.send(b"ok")
                elif word == "initialize":
                    self.log("Starting server...")

                    self.copyServer()
                    self.copyWorld()

                    if not self.startServer():
                        connection.send(b"err: server failed to start")
                    else:
                        connection.send(b"ok")
                elif word == "log_start":
                    self.log("Starting metric collection...")
                    res1 = self.connectJMX()
                    if not res1:
                        connection.send(b"err: jmx failed to start")

                    # Start debug profiling
                    if self.args.debug_profile != 0 :
                        self.sendRCON("debug start")
                    
                    res2 = self.connectSys()
                    if not res2:
                        connection.send(b"err: sys metrics failed to start")
                    if res1 and res2:
                        connection.send(b"ok")
                    
                    
                elif word == "log_stop":
                    self.log("Stopping metric collection...")
                    self.stopMetricSampling():
                    connection.send(b"ok")
                elif word == "stop_server":
                    self.log("Stopping server...")
                    if not self.stopServer():
                        connection.send(b"err: server not running")
                    else:
                        connection.send(b"ok")
                elif word == "keep_alive":
                    self.log("Keep alive received.")
                    connection.send(b"ok")
                elif word == "exit":
                    self.log("Exit received, connection ended.")
                    break
                else:
                    self.log("Badly formated message recieved")
            else:
                self.log("0 Len recv, connection ended.")
                break            



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-controlport', '-c', type=int, default=25555)
    parser.add_argument('-mcport', '-m',  type=int, default=25565)
    parser.add_argument('-debug_profile', '-d', type=int, default=0)
    parser.add_argument('-cpu_affinity', '-ca', default="0xFFFFFFFF")
    parser.add_argument('-jmxport_start', '-js',  type=int, default=25585)
    parser.add_argument('-jmxport_end', '-je',  type=int, default=25635)
    parser.add_argument('-ram')

    mc_receive = MC_Receive(parser.parse_args())
    mc_receive.listenToSocket()

