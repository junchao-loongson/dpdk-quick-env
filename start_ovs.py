#!/bin/python3

import os
import argparse
import sys
import subprocess

#mail: zhaojunchao@loongson.cn

arg_f = False;

hugepagenum = "";
db_socket = "db.sock";

dir_bin = "./bin/";
dir_sbin = "./sbin/";
dir_work = os.getcwd() + "/";
dir_etc = "./etc/openvswitch/"
dir_var_run = "./var/run/openvswitch/"
dir_var_log = "./var/log/openvswitch/"
dir_share = "./share/openvswitch/"

ret_sdk = os.getenv('RTE_SDK')
ret_target = os.getenv('RTE_TARGET');

parse = argparse.ArgumentParser();
parse.add_argument('-pages',default="128",type=str);
parse.add_argument('-addbr',type=str);
parse.add_argument('-addport',type=str, nargs=3);


print("work dir:" + dir_work);

def print_error(pstr):
    print("\033[27;31;31m\t{}\033[0m".format(pstr)) 

def init_hugepage(num):

    os.system("echo {} > /proc/sys/vm/nr_hugepages".format(num));
    
    ps = subprocess.run(["cat", "/proc/sys/vm/nr_hugepages "], stdout=subprocess.PIPE);
    if(num in str(ps.stdout)):
        print("set hugepage_nr {} success".format(num));
    else:
        print_error("set hugepage_nr error! nr is {}".format(str(ps.stdout)));
        exit(-1);
    #TODO: for x86
    os.system("mount -t hugetlbfs -o pagesize=32768k none /dev/hugepages")

def init_kmod():
  
    if(ret_sdk is None):
        print_error("please set RET_SDK and RTE_RARGET");
        exit(-1);

    os.system("modprobe uio");
    os.system("modprobe openvswitch");
    os.system("insmod " + ret_sdk + "/" + ret_target + "/kmod/igb_uio.ko");
    
    ps = subprocess.run(["lsmod"], stdout=subprocess.PIPE);
    
    if("igb_uio" in str(ps.stdout)):
        print("igb_uio mod ok");
    else:
        print_error("ismod igb_uio error");
        exit(-1);
    if("openvswitch" in str(ps.stdout)):
        print("OVS mod ok");
    else:
        print("ismod OVS error");
        exit(-1);


def init_env():

    if(ret_sdk is None):
        print("please set RET_SDK and RTE_RARGET");
        exit(-1);
    if(not os.path.isfile("./bin/ovs-vsctl")):
        print_error("not in OVS install dir");
        exit(-1);

    if (not os.path.isdir(dir_etc)):
        print("creat " + dir_etc);
        os.system("mkdir -p  " + dir_etc);

    if (not os.path.isdir(dir_var_run)):
        print("creat " + dir_var_run);
        os.system("mkdir -p " + dir_var_run);

    if (not os.path.isdir(dir_var_log)):
        print("creat " + dir_var_log);
        os.system("mkdir -p " + dir_var_log);


def add_br(name):
    os.system(dir_bin + "ovs-vsctl add-br {} -- set bridge {} datapath_type=netdev".format(name, name));
    os.system(dir_bin + "ovs-vsctl show");

def add_port(br, name, idx):
    os.system(dir_bin + "ovs-vsctl add-port {} {} -- set Interface {} type=dpdkvhostuserclient options:vhost-server-path=/usr/local/var/run/sock{} mtu_request=9000".format(br,name,name, idx));
    os.system(dir_bin + "ovs-vsctl show");

def clr_env():
    os.system("killall ovsdb-server ovs-vswitchd");
    os.system("rm ./etc/openvswitch/conf.db");
    os.system("rm -f ./var/run/openvswitch/vhost-user*");

def show_info():
    print("#hugepagenum : ------------------------------");
    os.system("cat /proc/sys/vm/nr_hugepages");
    
    print("# mod ---------------------------------------");
    os.system("lsmod | grep uio");
    os.system("lsmod | grep openvswitch");

    print("# ovs ---------------------------------------");
    ps = subprocess.run(["ps", "-ef"], stdout=subprocess.PIPE);
    if("ovs-vswitchd" in str(ps.stdout)):
        print("ovs-vswitchd is running!");
        ps1 = subprocess.run([dir_bin + "ovs-vsctl", "get", "Open_vSwitch", ".", "dpdk_initialized"], stdout=subprocess.PIPE);
        if("true" in str(ps1.stdout)):
            print("Open_vSwitch . dpdk_initialized");
            os.system(dir_bin + "ovs-vsctl show");
        else:
            print_error("Open_vSwitch . dpdk_initialize ERROR!");
    else:
        print_error("ovs-vswitchd is not running!");

def cook_arg():

   global hugepagenum
   args = parse.parse_args();
   print(args);
   hugepagenum = args.pages;
   if(not args.addbr is None):
       print(args.addbr);
       add_br(args.addbr);
       exit(0);
   if(not args.addport is None):
       if(len(args.addport) != 3):
           print("arg error!");
           print("br_name port_name port_id");
           exit(-1);
       add_port(args.addport[0], args.addport[1], args.addport[2]);
       exit(0);

if("page" in sys.argv):
    init_hugepage(sys.argv[sys.argv.index("page")+1]);
    arg_f = True;
if("mod" in sys.argv):
    init_kmod(); 
    arg_f = True;

if("log" in sys.argv):
    os.system("cat var/log/openvswitch/ovs-vswitchd.log");
    arg_f = True;

if("clr" in sys.argv):
    clr_env();
    arg_f = True;

if("show" in sys.argv):
    show_info();
    arg_f = True;

if(arg_f):
    exit(0);

cook_arg();
init_env();
init_hugepage(hugepagenum);
init_kmod(); 
clr_env();

os.system(dir_bin + "ovsdb-tool create " + dir_etc + "conf.db " + dir_share + "vswitch.ovsschema");
os.system(dir_sbin + "ovsdb-server --remote=punix:" + db_socket + " --remote=db:Open_vSwitch,Open_vSwitch,manager_options --pidfile --detach");
os.system(dir_bin + "ovs-vsctl --no-wait set Open_vSwitch . other_config:per-port-memory=true");
os.system(dir_bin + "ovs-vsctl --no-wait init");
os.system(dir_bin + "ovs-vsctl --no-wait set Open_vSwitch . other_config:dpdk-lcore-mask=0x2");
os.system(dir_bin + "ovs-vsctl --no-wait set Open_vSwitch . other_config:dpdk-socket-mem=2048");
os.system(dir_bin + "ovs-vsctl --no-wait set Open_vSwitch . other_config:dpdk-init=true");
os.system(dir_sbin + "ovs-vswitchd unix:"+ dir_work +"var/run/openvswitch/db.sock  --pidfile --detach --log-file=" + dir_var_log +"ovs-vswitchd.log");

ps = subprocess.run([dir_bin + "ovs-vsctl", "get", "Open_vSwitch", ".", "dpdk_initialized"], stdout=subprocess.PIPE);

if("true" in str(ps.stdout)):
    print("ovs-vswitchd start!");
else :
    print_error("ovs-vswitchd start ERROR!");



