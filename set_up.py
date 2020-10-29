#!/usr/bin/python3 

import os
import platform

hugepages = 0;
cpu = platform.processor()

os.system("modprobe  uio");

if("mips" in cpu ):
    hugepages = 128;
    os.system("insmod  ./mips-loongson3a-linuxapp-gcc/kmod/igb_uio.ko");
elif ("x86" in cpu ):
    hugepages = 1024;
    os.system("insmod  ./x86_64-native-linuxapp-gcc/kmod/igb_uio.ko");

os.system("echo {} > /proc/sys/vm/nr_hugepages".format(hugepages));


 
