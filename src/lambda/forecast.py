# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from functools import lru_cache
import os
import time
import boto3
import botocore
import json
import requests

#region = os.getenv("AWS_REGION")
ip = "127.0.0.1"
bucket = os.getenv("BUCKET_NAME")
job_num= int(os.getenv("DOMAINS_NUM"))

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
    output = f"s3://{bucket}/outputs/{zone}/${{y}}/${{m}}/${{d}}/${{h}}"
    with open("jobs/preproc.sh", "r") as f:
        script = f.read()
    script += f"\naws s3 cp slurm-${{SLURM_JOB_ID}}.out {output}/logs/\n"
    script += f"\naws s3 cp preproc/geogrid.*.log {output}/logs/\n"
    script += f"\naws s3 cp preproc/ungrib.*.log {output}/logs/\n"
    script += f"\naws s3 cp preproc/metgrid.*.log {output}/logs/\n"
    script += f"\naws s3 cp run/real.*.log {output}/logs/\n"
    template["job"]["name"] = "pre"
    template["job"]["nodes"] = 1
    template["job"]["cpus_per_task"] = 1
    template["job"]["tasks_per_node"] = 4
    template["job"]["current_working_directory"] = f"/fsx/{zone}"
    template["script"] = script
    print(template)
    return submit(template)

def run_wrf(zone,pid):
    global bucket
    output = f"s3://{bucket}/outputs/{zone}/${{y}}/${{m}}/${{d}}/${{h}}"
    with open("jobs/run_wrf.sh", "r") as f:
        script = f.read()
    script += f"\naws s3 cp ../slurm-${{SLURM_JOB_ID}}.out {output}/logs/\n"
    script += f"\naws s3 cp wrfoutput* {output}/wrfout/\n"
    template["job"]["name"] = "wrf"
    template["job"]["nodes"] = 2 
    template["job"]["cpus_per_task"] = 4
    template["job"]["tasks_per_node"] = 24
    template["job"]["current_working_directory"] = f"/fsx/{zone}"
    template["job"]["dependency"] = f"afterok:{pid}"
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



def main(event, context):

    global ip
    global job_num
    print(event)
    ip=event['headNode']['privateIpAddress']
    print(ip)
    pids=[]
    jids=[]
    for i in range(1,job_num+1):
        n='domain_'+str(i)
        job_id=preproc(n)
        pids.append(job_id)
        jids.append(run_wrf(n,job_id))
    #fini(jids)
