#!/usr/bin/python3

import os
import subprocess
import sys
import argparse


mtu = 0
count = 0 

pkt_sys_dev = "/proc/net/pktgen/kpktgend_0"
pkt_ctl_dev = "/proc/net/pktgen/pgctrl"
pkt_usr_dev = "/proc/net/pktgen/"
eth_name = "nop";
src_mac = "nop";
dts_mac = "nop";

parse = argparse.ArgumentParser();
parse.add_argument('-m','--mtu', default=1500, help='set mtu');
parse.add_argument('-c','--count', default=1, help='Set the number of packets to send.');
parse.add_argument('-e','--eth', default="nop", help='Interface');
parse.add_argument('-s','--smac', default="nop", help='set source mac');
parse.add_argument('-d','--dmac', default="nop", help='set destination mac');


def pkt_set(dev, val):
    os.system("echo "+val+" > "+dev);
    #print("echo "+val+" > "+dev);
    if val == "start":

        print("start pktgen....");
        print("Interface:{}".format(eth_name));
        print("packt size:{}".format(mtu));
        print("packt num:{}".format(count));
        if src_mac != "nop":
            print("src mac:{}".format(src_mac));
        if dts_mac != "nop":
            print("dts mac:{}".format(dts_mac));

    ps = subprocess.run(["cat", dev], stdout=subprocess.PIPE);

    if("Result: OK" in str(ps.stdout)):
        return True;
    else:
        return False;

def cook_arg():
    global args, count, mtu, eth_name, src_mac, dts_mac;

    args = parse.parse_args();
    mtu = args.mtu;
    
    count = args.count;

    src_mac = args.smac;
    dts_mac = args.dmac;
 
    eth_name = args.eth;
    if(eth_name == "nop"):
        print("Please specify a network card to send data");
        exit(-1);
    

ps = subprocess.run("lsmod", stdout=subprocess.PIPE);

if("pktgen" in str(ps.stdout)):
    print("found pktgen mod");
else:
    os.system("modprobe pktgen")
    print("probe pktgen");


if("unbind" in sys.argv):
    os.system("echo {} > /sys/bus/pci/drivers/ixgbe/unbind".format(sys.argv[2]));
    exit(0);


if("bind" in sys.argv):
    os.system("echo {} > /sys/bus/pci/drivers/ixgbe/bind".format(sys.argv[2]));
    print("eth name is:");
    os.system("ls /sys/bus/pci/drivers/ixgbe/{}/net".format(sys.argv[2]));
    exit(0);

if("start" in sys.argv):
    pkt_set(pkt_ctl_dev,  "start");
    exit(0);

if("stop" in sys.argv):
    pkt_set(pkt_ctl_dev,  "stop");
    exit(0);

file_count = 0;

for file in os.listdir("/sys/bus/pci/drivers/ixgbe/"):
    file_count += 1;

if file_count <= 6:
    print("not found card!");
    exit(0);

cook_arg();
pkt_set(pkt_sys_dev, "rem_device_all");
pkt_set(pkt_sys_dev, "add_device " + eth_name);
pkt_set(pkt_sys_dev, "max_before_softirq 1");

pkt_set(pkt_usr_dev + eth_name, "clone_skb 1000");
pkt_set(pkt_usr_dev + eth_name, "pkt_size " + str(mtu));
if src_mac != "nop":
    pkt_set(pkt_usr_dev + eth_name, "src_mac " + src_mac);
if dts_mac != "nop":
    pkt_set(pkt_usr_dev + eth_name, "dst_mac " + dts_mac);

pkt_set(pkt_usr_dev + eth_name, "flag IPSRC_RND");
pkt_set(pkt_usr_dev + eth_name, "count "+ str(count));

pkt_set(pkt_ctl_dev,  "start");    

