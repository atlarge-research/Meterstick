from io import DEFAULT_BUFFER_SIZE
import os
import sys
import pathlib
import argparse
import subprocess
import threading
import time
import socket
import logging

# Controller server, contains experiment loop. Sends control messages to YS and MC control clients.

args = None
MC_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
YS_sockets = []
logging.basicConfig(format='%(asctime)s :: %(message)s',level=logging.DEBUG)

def experimentLoop():
    current_server = 0
    for server_name in args.servers:
        logging.info("Starting Experiment with %s",server_name)
        sendMC("set_server:"+server_name, True)
        sendYS("set_server:"+server_name, True)
        sendMC("set_jmx:"+args.jmx_urls[current_server], True)
        iterationCounter = 0
        
        if args.iteration_start != 0:
            # Used during experiment recovery, -1 because incremented during setup
            iterationCounter = args.iteration_start
            sendMC(f"iter:{args.iteration_start - 1}", True)
            sendYS(f"iter:{args.iteration_start - 1}", True)
            args.iteration_start = 0

        while iterationCounter < args.iterations:
            # Send initialization to all nodes, wait for server to start up
            logging.info("  Starting iteration %s",iterationCounter)
            logging.info("      Initializing MC")
            sendMC("initialize", True)
            time.sleep(35) # wait for server to start

            logging.info("      Starting YS")
            sendYS("connect", True) 

            logging.info("      Starting logging")
            sendMC("log_start", True)

            # Hack-y fix for Azure killing TCP connections that don't send data for extended amounts of time
            if args.duration >= 200:
                duration_left = args.duration + 5
                while duration_left > 0:
                    sleep_amount = 120 if duration_left >= 120 else duration_left
                    time.sleep(sleep_amount)
                    logging.info("      Sending keep alives")
                    sendMC("keep_alive", True)
                    sendYS("keep_alive", True)
                    duration_left -= 120
            else:
                time.sleep(args.duration + 5) # Wait for ys to finish

            logging.info("      Stopping logging")
            sendMC("log_stop", True)
            
            if args.workload:
                logging.info("      Converting Yardstick metrics")
                sendYS("convert", True)

            logging.info("      Stopping MC")
            sendMC("stop_server", True)

            iterationCounter += 1
            time.sleep(5) # wait for port to (hopefully) be free again
        current_server+=1
    logging.info("Experiment finished.")

# Connects to the MC node
def connectMC():
    MC_socket.settimeout(30)
    logging.info("Connecting MC socket to %s", args.server_node_ip)
    MC_socket.connect((args.server_node_ip, args.controlport))
    
# Connects to all YS nodes
def connectYS():
    for ip in args.yardstick_ips:
        logging.info("Connecting YS socket to %s", ip)
        ys_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ys_sock.settimeout(30) # Log timeout for yardstick metric processing
        ys_sock.connect((ip, args.controlport))
        YS_sockets.append(ys_sock)

# Disconnects from all nodes
def exitAll():
    sendMC("exit", False)
    sendYS("exit", False)

# Send message to the node running MC. Returns true if ack requested and received
def sendMC(to_send, req_ack):
    try:
        MC_socket.sendall(to_send.encode())
        if req_ack:
            return handleAck(MC_socket)
        else:
            return True
    except socket.error as e:
        logging.info(e)
        MC_socket.close()

    
# Send message to all nodes running YS. Returns true if ack requested and received from all yardstick nodes
def sendYS(to_send, req_ack):
    response = []
    for ys_sock in YS_sockets:
        try:
            ys_sock.sendall(to_send.encode())
            if req_ack:
                response.append(handleAck(ys_sock))
            else:
                return True
        except socket.error as e:
            logging.info(e)
            ys_sock.close()
    if False in response:
        return False

# Returns true if ack received and false otherwise
def handleAck(listen_sock):
    try:
        response = listen_sock.recv(32)
        res = response.decode()
        if res == "":
            logging.info("Ack requested but connection has been closed")
            return False 
        if res[:5] == b"err: ":
            logging.info("Ack returned error: %s", res[5:])
            return False
        if res != "ok":
            logging.info("Incorrect/missing ack: %s", res)
            return False
        return True
    except socket.timeout:
        logging.info("No ack received though it was requested.")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('server_node_ip')
    parser.add_argument('-yardstick_ips', '-y', nargs='+', required=True)
    parser.add_argument('-servers', '-s', nargs='+', required=True)
    parser.add_argument('-jmx_urls', '-ju', nargs='+', required=True)
    parser.add_argument('-workload', '-w', default=True)
    parser.add_argument('-controlport', '-c',  type=int, default=25555)
    parser.add_argument('-mcport', '-m',  type=int, default=25565)
    parser.add_argument('-iterations', '-i', type=int,  default=10)
    parser.add_argument('-iteration_start', '-is', type=int,  default=0)
    parser.add_argument('-duration', '-d', type=int,  default=60)


    args = parser.parse_args()

# Initialize connection to the control clients
connectMC()
connectYS()

# Begin experiment loop
experimentLoop()

exitAll()