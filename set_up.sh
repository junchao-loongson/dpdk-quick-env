#!/bin/bash   

echo 1024 > /proc/sys/vm/nr_hugepages
modprobe  uio
insmod  ./x86_64-native-linuxapp-gcc/kmod/igb_uio.ko 
