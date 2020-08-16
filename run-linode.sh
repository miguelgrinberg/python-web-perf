#!/bin/bash
echo Creating Linode...
public_key=$(cat ~/.ssh/id_rsa.pub)
root_pw=$(openssl rand -base64 32)
linode_id=$(linode-cli linodes create --label perf --root_pass $root_pw --authorized_keys "$public_key" --json | jq -r ".[0].id")
while true
do
    sleep 1
    linode_view=$(linode-cli linodes view $linode_id --json)
    status=$(echo $linode_view | jq -r ".[0].status")
    if [[ "$status" == "running" ]]; then
        break
    fi
done
linode_ip=$(echo $linode_view | jq -r ".[0].ipv4[0]")
echo "Done, IP address: $linode_ip"

echo Creating user account...
ssh -o "StrictHostKeyChecking no" root@$linode_ip "adduser --gecos '' --disabled-password ubuntu; usermod -aG sudo ubuntu; mkdir /home/ubuntu/.ssh; cp /root/.ssh/authorized_keys /home/ubuntu/.ssh/; chown ubuntu:ubuntu -R /home/ubuntu/.ssh; chmod 500 /home/ubuntu/.ssh; chmod 400 /home/ubuntu/.ssh/authorized_keys; echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"

echo Setup server...
ssh ubuntu@$linode_ip "wget https://raw.githubusercontent.com/miguelgrinberg/python-web-perf/master/setup.sh; bash setup.sh"

echo Run benchmark...
ssh ubumtu@$linode_ip "cd python-web-perf; venv/bin/python run-benchmark.py"

echo Delete Linode...
linode-cli linodes delete $linode_ip
