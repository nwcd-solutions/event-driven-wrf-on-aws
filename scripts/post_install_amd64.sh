#!/bin/bash 
. /etc/parallelcluster/cfnconfig

#shared_folder=$(echo $cfn_ebs_shared_dirs | cut -d ',' -f 1 )
#shared_folder=/fsx

# Set ulimits according to WRF needs
cat >>/tmp/limits.conf << EOF
# core file size (blocks, -c) 0
*           hard    core           0
*           soft    core           0
# data seg size (kbytes, -d) unlimited
*           hard    data           unlimited
*           soft    data           unlimited
# scheduling priority (-e) 0
*           hard    priority       0
*           soft    priority       0
# file size (blocks, -f) unlimited
*           hard    fsize          unlimited
*           soft    fsize          unlimited
# pending signals (-i) 256273
*           hard    sigpending     1015390
*           soft    sigpending     1015390
# max locked memory (kbytes, -l) unlimited
*           hard    memlock        unlimited
*           soft    memlock        unlimited
# open files (-n) 1024
*           hard    nofile         65536
*           soft    nofile         65536
# POSIX message queues (bytes, -q) 819200
*           hard    msgqueue       819200
*           soft    msgqueue       819200
# real-time priority (-r) 0
*           hard    rtprio         0
*           soft    rtprio         0
# stack size (kbytes, -s) unlimited
*           hard    stack          unlimited
*           soft    stack          unlimited
# cpu time (seconds, -t) unlimited
*           hard    cpu            unlimited
*           soft    cpu            unlimited
# max user processes (-u) 1024
*           soft    nproc          16384
*           hard    nproc          16384
# file locks (-x) unlimited
*           hard    locks          unlimited
*           soft    locks          unlimited
EOF

sudo bash -c 'cat /tmp/limits.conf > /etc/security/limits.conf'

function download_wrf_install_package {
echo "Download wrf pre-compiled installation package"

chmod 777 ${shared_folder}
cd ${shared_folder}
wget https://aws-hpc-builder.s3.amazonaws.com/project/apps/aws_pcluster_3.4_alinux2_wrf_amd64.tar.xz
tar xpf aws_pcluster_3.4_alinux2_wrf_amd64.tar.xz
}

echo "NODE TYPE: ${cfn_node_type}"

case ${cfn_node_type} in
        HeadNode)
                echo "I am the HeadNode node"
                download_wrf_install_package
                cd ${shared_folder}
                #wget https://raw.githubusercontent.com/
                #bash pcluster_install_spack.sh
                wget https://raw.githubusercontent.com/config_slurm.sh
                bash config_slurm.sh
                
        ;;
        ComputeFleet)
                echo "I am a Compute node"
        ;;
        esac
        
exit 0
