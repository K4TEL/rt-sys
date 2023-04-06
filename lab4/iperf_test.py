#!/usr/bin/env python
# coding: utf-8

import pytest
from parser import *
from conftest import *

parser_headers = ['Interval', 'Transfer', 'Bitrate', 'Retr', 'Cwnd']

class TestSuite():
    def test_ssh_client(self, ssh_client):
        ssh = ssh_client
        assert ssh.get_transport().is_active()
        
    def test_server(self, ssh_client, server):
        response = server
        assert response[0] in ["", None]
        
    def test_ssh_servers(self, ssh_client, ssh_prompt):
        response = ssh_prompt
        assert response[-1] not in ["", None]
        
        # forming dict of ports and IPs of running iperf instances
        iperf_instance_dict = {s.split(':')[-1]: s.split(':')[0] for s in response[-1]}

        for port, ip in iperf_instance_dict.items():
            if len(ip) == 0: # not strict ip binding
                # check local ip addresses for available iperf client connection on the current port
                iperf_instance_dict[port] = [ip for ip in host_list if 
                                             subprocess.getstatusoutput(f'iperf3 -c {ip} -p {port} -n 1')[0] == 0]
            assert len(iperf_instance_dict[port]) == len(host_list)
        
    def test_iperf_client_connection(self, ssh_client, server, client_check):
        result, code = client_check
        assert code == 0
        
    def test_iperf_client_traffic(self, ssh_client, server, client):
        result, error, client_time = client
        
        assert error in ["", None]

        # standard parser headers in the output
        result_table = parser(result, client_time, parser_headers)
        condition_matches = result_table.loc[(result_table.Transfer > 2) & (result_table.Bitrate > 20), :]
        print(f"Percentage of matching conditions Transfer > 2 & Bitrate > 20:\t" 
            f"{100 * len(condition_matches.index)/len(result_table.index)}%")
        assert len(condition_matches.index) == len(result_table.index)

