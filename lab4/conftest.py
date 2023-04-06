#!/usr/bin/env python
# coding: utf-8

import subprocess
import paramiko
import pytest
from iperf_test import *

ssh_user = "kl"
ssh_pass = "1337"
ssh_port = 22
iperf_port = "5201"

local_ips_prompt = "ip addr show | grep -oP 'inet6? [^ /]+' | awk '{print $2}' | sort | uniq | grep -v '^fe80::'"

# list of local host names 
host_list = subprocess.getoutput(local_ips_prompt).split("\n")
host = host_list[2]

port_servers_prompt = "netstat -tnlp | grep " + iperf_port + " | awk '{print $4}'"
iperf_servers_prompt = "netstat -tnlp | grep iperf3 | awk '{print $4}'"
# prompts to check server instance on the SSH client 
ssh_prompts = [port_servers_prompt, iperf_servers_prompt]

# fast client coonection check flags
client_check_flags = ['-n', '1']
# iperf client base
client_start = ['iperf3', '-c', host, '-p', iperf_port]

# iperf server deamon start
server_start = "iperf3 -s -D"

# iperf servers stop
server_stop = f"echo {ssh_pass} | sudo -S killall iperf3"

# fast client connection check
check_prompt = ' '.join(client_start + client_check_flags)

# iperf client-server traffic measure prompts
traffic_prompts = []
for t in range(10, 60, 10):
    traffic_prompts.append(client_start + ["-t", str(t)])

# open SSH client connection
@pytest.fixture(scope="module", params=host_list)
def ssh_client(request):
    ssh_host = request.param or host
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, 
               port=ssh_port, 
               username=ssh_user, 
               password=ssh_pass)
    
    yield ssh
    ssh.close()

#check if the server is available for all local host client connections
@pytest.fixture(scope="module", params=ssh_prompts)
def ssh_prompt(ssh_client, server, request):
    prompt = request.param
    
    err = server[0]
    if err:
        return [err, None]
    
    stdin, stdout, stderr = ssh_client.exec_command(prompt)
    
    error = stderr.readlines()
    error = None if len(error) == 0 else [line.rstrip() for line in error]

    output = stdout.readlines()
    output = None if len(output) == 0 else [line.rstrip() for line in output]
    
    return [ error, output ]

# start iperf server on host SSH client
@pytest.fixture(scope="module")
def server(ssh_client):
    # start the server
    stdin, stdout, stderr = ssh_client.exec_command(server_start)
    
    error = stderr.readlines()
    error = None if len(error) == 0 else [line.rstrip() for line in error]

    output = stdout.readlines()
    output = None if len(output) == 0 else [line.rstrip() for line in output]
    
    yield [ error, output ]

    # stop the server
    stdin, stdout, stderr = ssh_client.exec_command(server_stop)
    

# connect iperf client to the server running on SSH host
@pytest.fixture(scope="module")
def client_check(server):
    err = server[0]
    if err:
        return None, err

    check_code, check_output = subprocess.getstatusoutput(check_prompt)
    return check_output, check_code

# test traffic of the iperf client to the server running on SSH host
@pytest.fixture(scope="module", params=traffic_prompts)
def client(server, request):    
    err = server[0]
    if err:
        return None, err

    client_prompt = request.param
    process = subprocess.Popen(client_prompt, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               encoding='utf-8')
    stdout, stderr = process.communicate()        
    return stdout, stderr, int(client_prompt[-1])
