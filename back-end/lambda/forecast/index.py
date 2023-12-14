# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from functools import lru_cache
import os
import time
import boto3
import botocore
import json
import requests
import math

ssm = boto3.client('ssm')
#region = os.getenv("AWS_REGION")
ip = "127.0.0.1"
bucket = os.getenv("BUCKET_NAME")
#job_num= int(os.getenv("DOMAINS_NUM"))
ftime = "2023-01-01:12:00:00Z"
template = {
    "job": {
        "name":"",
        "nodes":1,
        "cpus_per_task": 4,
        "tasks_per_node": 24,
        "current_working_directory":"/fsx",
        "environment":{
            "PATH":"/bin:/usr/bin/:/usr/local/bin/",
            "LD_LIBRARY_PATH":"/lib/:/lib64/:/usr/local/lib"
        },
        "requeue": "false"
    },
    "script": ""
}

@lru_cache
def token():
    session = boto3.session.Session()
    sm = session.client('secretsmanager')
    secret = sm.get_secret_value(SecretId="JWTKey")
    return secret['SecretString']

@lru_cache
def headers():
    return {
            "X-SLURM-USER-NAME": "ec2-user",
            "X-SLURM-USER-TOKEN": token(),
            "content-type": "application/json",
            }

def submit(data):
    global ip
    url = f"http://{ip}:8080/slurm/v0.0.37/job/submit"
    resp = requests.post(url, data=json.dumps(data), headers=headers())
    print(resp)
    jid = resp.json()["job_id"]
    print(resp.json())
    print(resp.status_code)
    return jid

def status(jobid):
    global ip
    url = f"http://{ip}:8080/slurm/v0.0.37/job/{jobid}"
    resp = requests.get(url, headers=headers())
    print(resp)
    return resp.json()

def fini(ids):
    global bucket
    global ftime
    y=ftime[0:4]
    m=ftime[5:7]
    d=ftime[8:10]
    h=ftime[11:13]
    output = f"s3://{bucket}/outputs/{y}/{m}/{d}/{h}"    
    with open("jobs/fini.sh", "r") as f:
        script = f.read()
    script += f"\naws s3 cp forecast.done {output}/forecast.done"
    script += f"\naws s3 cp slurm-${{SLURM_JOB_ID}}.out {output}/logs/slurm-${{SLURM_JOB_ID}}.out\n"
    template["job"]["nodes"] = 1
    template["job"]["name"] = "fini"
    template["job"]["tasks_per_node"] = 1
    template["job"]["current_working_directory"] = "/fsx"
    template["job"]["dependency"] = f"afterok:{':'.join([str(x) for x in ids])}"
    template["script"] = script
    print(template)
    return submit(template)

    
def preproc(zone):
    global bucket
    global ftime
    y=ftime[0:4]
    m=ftime[5:7]
    d=ftime[8:10]
    h=ftime[11:13]
    output = f"s3://{bucket}/outputs/{y}/{m}/{d}/{h}/{zone}"
    with open("jobs/pre.sh", "r") as f:
        script = f.read()
    script += f"\naws s3 cp slurm-${{SLURM_JOB_ID}}.out {output}/logs/\n"
    script += f"\naws s3 cp preproc/geogrid.*.log {output}/logs/\n"
    script += f"\naws s3 cp preproc/ungrib.*.log {output}/logs/\n"
    script += f"\naws s3 cp preproc/metgrid.*.log {output}/logs/\n"
    script += f"\naws s3 cp run/real.*.log {output}/logs/\n"
    template["job"]["name"] = "pre_" + zone
    template["job"]["nodes"] = 1
    template["job"]["cpus_per_task"] = 4
    template["job"]["tasks_per_node"] = 1
    template['job']['partition']='wps'
    template["job"]["current_working_directory"] = f"/fsx/{zone}"
    template["script"] = script
    print(template)
    return submit(template)

def run_wrf(zone,pid,nodes):
    global bucket
    global ftime
    y=ftime[0:4]
    m=ftime[5:7]
    d=ftime[8:10]
    h=ftime[11:13]
    output = f"s3://{bucket}/outputs/{y}/{m}/{d}/{h}/{zone}"
    nodes =  int(nodes) 
    with open("jobs/run.sh", "r") as f:
        script = f.read()
    script += f"\naws s3 cp ../slurm-${{SLURM_JOB_ID}}.out {output}/logs/\n"
    script += f"\naws s3 cp . {output}/wrfout/ --recursive --exclude \"*\" --include \"wrfout_*\"\n"
    template["job"]["name"] = "wrf_" + zone
    template["job"]["nodes"] = nodes 
    template["job"]["cpus_per_task"] = 4
    template["job"]["tasks_per_node"] = 24
    template["job"]["current_working_directory"] = f"/fsx/{zone}"
    template["job"]["dependency"] = f"afterok:{pid}"
    template['job']['partition']='general'
    template["script"] = script
    print(template)
    return submit(template)
    

def post(pid):
    with open("jobs/post.sh", "r") as f:
        script = f.read()
    script += f"\naws s3 cp --no-progress ${{grib}} {output}/${{grib}}"
    script += f"\naws s3 cp slurm-${{SLURM_JOB_ID}}.out {output}/logs/slurm-${{SLURM_JOB_ID}}.out\n"
    template["job"]["nodes"] = 1
    jids = []
    for i in range(0, 7):
        template["job"]["name"] = f"post-{i:03}"
        template["job"]["dependency"] = f"afterok:{pid}"
        template["job"]["current_working_directory"] = f"/fsx/run/post/{i:02}"
        template["script"] = script
        print(template)
        jids.append(submit(template))
    return jids



def handler(event, context):

    global ip
    global ftime
    
    print(event)
    ip=event['headNode']['privateIpAddress']
    ftime=event['ftime']
    receive_time=event['receive_time']
    id=event['id']
    region=event['region']
    cluster_name=event['cloudformationStackArn']
    job_num = 0
    print(ip)
    pids=[]
    jids=[]
    job_num=0
    dynamodb = boto3.resource('dynamodb')
    para_table = dynamodb.Table(os.getenv('PARA_DB'))
    response = para_table.scan()
    items = response['Items']
    job_num = len(items)
    print(items)
    print("domains:")
    print(job_num)
    for item in items:
        n=item['name']
        pids.append(preproc(n))
    i=1
    for item in items:
        n=item['name']
        nodes=str(math.cell(int(item['cores'])/64))
        jids.append(run_wrf(n,pids[i-1],nodes))
        i=i+1
    fini(jids)

    ssm.put_parameter(
        Name=os.getenv('FTIME'),
        Value= ftime,
        Type='String',
        Overwrite=True
    )
    ssm.put_parameter(
        Name=os.getenv('EXEC_ID'),
        Value= id,
        Type='String',
        Overwrite=True
    )
    ssm.put_parameter(
        Name=os.getenv('EXEC_RECEIVE_TIME'),
        Value= receive_time,
        Type='String',
        Overwrite=True
    )
    timeout_value=ssm.get_parameter(
        Name=os.getenv('JOB_TIMEOUT'),
    )
    out={
        "ftime":ftime,
        "id":id,
        "region":region,
        'receive_time':receive_time,
        "clustername":cluster_name,
        "job_timeout":timeout_value['Parameter']['Value']
    }
    return out
