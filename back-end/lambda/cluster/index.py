# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from datetime import datetime
import datetime as dt
import os
import re
import boto3
import botocore
import json
import requests
import yaml

region = os.getenv("REGION", "us-east-2")
dynamodb = boto3.resource('dynamodb')
exec_table = dynamodb.Table(os.getenv('EXEC_DB'))

def gateway(url, method, data):

    req_call = {
        "POST": requests.post,
        "GET": requests.get,
        "PUT": requests.put,
        "PATCH": requests.patch,
        "DELETE": requests.delete,
    }.get(method)

    session = botocore.session.Session()
    request = botocore.awsrequest.AWSRequest(method=method, url=url, data=data)
    botocore.auth.SigV4Auth(session.get_credentials(), "execute-api", region).add_auth(request)
    boto_request = request.prepare()
    boto_request.headers["content-type"] = "application/json"
    response = req_call(url, data=data, headers=boto_request.headers, timeout=300)
    return response

def handler(event, context):
    baseurl = os.getenv("PCLUSTER_API_URL")
    cluster_name = os.getenv("CLUSTER_NAME", "wx-pcluster")
    path = f"{baseurl}/v3/clusters"
    global region
    ftime=event['ftime']
    id = event['id']
    receive_time=event['receive_time']
    if (event['action']=='create'):
      if (event['type']=='od'):
        with open("hpc6a.yaml", "r") as cf:
          config_data = yaml.safe_load(cf)
        config_data["Region"] = region
        config_data["HeadNode"]["Networking"]["SubnetId"] = os.getenv("PUBLIC_SUBNETID")
        config_data["HeadNode"]["Networking"]["AdditionalSecurityGroups"][0] = os.getenv("SG")
        config_data["Scheduling"]["SlurmQueues"][0]["Networking"]["SubnetIds"][0] = os.getenv("PRIVATE_SUBNETID")
        config_data["Scheduling"]["SlurmQueues"][0]["Iam"]["S3Access"][0]["BucketName"] = os.getenv("BUCKET_NAME")
        config_data["Scheduling"]["SlurmQueues"][1]["Networking"]["SubnetIds"][0] = os.getenv("PRIVATE_SUBNETID")
        config_data["Scheduling"]["SlurmQueues"][1]["Iam"]["S3Access"][0]["BucketName"] = os.getenv("BUCKET_NAME")
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Script"] = os.getenv("S3_URL_POST_INSTALL_HEADNODE")
        config_data["HeadNode"]["Iam"]["AdditionalIamPolicies"][0] = {"Policy":os.getenv("KMS_POLICY")}
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][0] = region
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][1] = event['fcst_days']    #os.getenv("FORECAST_DAYS")
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][2] = ftime
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][3] = os.getenv("JWTKEY")
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][4] = os.getenv("BUCKET_NAME")
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][5] = json.dumps(event['domains'])        #os.getenv("NUM_DOMAINS")
        url=path
        method = "POST"
        data = json.dumps({"clusterConfiguration": yaml.dump(config_data, default_flow_style=False),
          "clusterName": cluster_name,
          "rollbackOnFailure": False
        })
        res=gateway(url, method, data)
        code = res.status_code
        print(code)
        if (code >=200 and code <400):
          out=res.json()['cluster']
          out['action']='status'
          out['ftime']=ftime
          out['id']=id
          out['receive_time']=receive_time
        else:
          print(res.json())
          current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          exec_table.update_item(
            Key={
                'id': int(id),
                'receive_time': receive_time
            },
            UpdateExpression = 'SET end_time = :end_time, exec_status = :exec_status, reason = :reason, ftime = :ftime',
            ExpressionAttributeValues = {
                ':end_time':current_time,
                ':exec_status':'failed',
                ':ftime':ftime,
                ':reason':res.json()['message']
            }
          )
          out={"clusterStatus":"failed"}
          out['failed_message']=res.json()
          out['clusterName']=cluster_name
          out['id']=id
          out['receive_time']=receive_time
        return out
      elif (event['type']=='spot'):
        with open("hpc6a.yaml", "r") as cf:
          config_data = yaml.safe_load(cf)
        ftime = '2023-01-05:12:00:00Z'
        #cluster_name=f"{cluster_name}-spot"
        print(cluster_name)
        config_data["Region"] = region
        config_data["HeadNode"]["Networking"]["SubnetId"] = os.getenv("SUBNETID")
        config_data["HeadNode"]["Networking"]["AdditionalSecurityGroups"][0] = os.getenv("SG")
        config_data["Scheduling"]["SlurmQueues"][0]["Networking"]["SubnetIds"][0] = os.getenv("SUBNETID")
        config_data["Scheduling"]["SlurmQueues"][0]["Iam"]["S3Access"][0]["BucketName"] = os.getenv("BUCKET_NAME")
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Script"] = "https://raw.githubusercontent.com/nwcd-solutions/wrf-on-aws/master/pc_setup_scripts/post_install_amd.sh"
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][0] = region
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][1] = os.getenv("SNS_TOPIC")
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][2] = ftime
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][3] = os.getenv("JWTKEY")
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][4] = os.getenv("BUCKET_NAME")
        config_data["HeadNode"]["CustomActions"]["OnNodeConfigured"]["Args"][5] = '2'
        url=path
        method = "POST"
        data = json.dumps({"clusterConfiguration": yaml.dump(config_data, default_flow_style=False),
          "clusterName": cluster_name,
          "rollbackOnFailure": False
        })
        res=gateway(url, method, data)
        code = res.status_code
        print(code)
        if (code >=200 and code <400):
          out=res.json()['cluster']
          out['action']='status'
          out['ftime']=ftime
        else:
          print(res.json())
          out={"clusterStatus":"failed"}
          out['failed_message']=res.json()
          out['clusterName']=cluster_name
        return out
    elif (event['action']=='status'):
      print('query status of the cluster')
      params = {"region": event['region']}
      data = json.dumps({"clusterName": event['clusterName']})
      method = "GET"
      url = f"{path}/{event['clusterName']}?region={region}"
      res=gateway(url, method, data)
      code = res.status_code
      print(code)
      if (code >=200 and code <400):
        out=res.json()
        print(out)
        if (out['clusterStatus']=='CREATE_IN_PROGRESS'):
            out['action']='status'
            out['ftime']=ftime
            out['id']=id
            out['receive_time']=receive_time
        else:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            exec_table.update_item(
              Key={
                'id': int(id),
                'receive_time': receive_time
              },
              UpdateExpression = 'SET cluster_create_completed_time = :cluster_create_completed_time , exec_status = :exec_status, ftime = :ftime',
              ExpressionAttributeValues = {
                ':cluster_create_completed_time':current_time,
                ':ftime':ftime,
                ':exec_status': "in progress"
              }
            )            
            out['action']='destroy'
            out['ftime']=ftime
            out['id']=id
            out['receive_time']=receive_time
      else:
        out={"CheckclusterStatus":"failed"}
      return out
    elif (event['action']=='destroy'):
      print("Destroy the cluster")    
      c = boto3.client("iam")
      roles = c.list_roles()
      for role in roles["Roles"]:
        n = role["RoleName"]
        if n.startswith("wx-pcluster-Role") and not n.startswith("wx-pcluster-RoleHeadNode"):   
            policies = c.list_attached_role_policies(RoleName=n)
            for policy in policies["AttachedPolicies"]:
                c.detach_role_policy(RoleName=n, PolicyArn=policy["PolicyArn"])
      cluster_name=event['clusterName']
      region=event['region']
      job_status=event['status']
      params = {"region": region}
      data = json.dumps({"clusterName": cluster_name})
      method = "DELETE"
      url = f"{path}/{cluster_name}?region={region}"
      res=gateway(url, method, data)
      code = res.status_code
      print(code)
      if (code >=200 and code <400):
        out=res.json()
        out['action']='destroystatus'
        out['ftime']=ftime
        out['id']=id
        out['status']=job_status
        out['receive_time']=receive_time
      else:
        print(res.json())
        out={"CheckclusterStatus":"deleted failed"}
      print(out)
      return out
    elif (event['action']=='destroystatus'):
      print('query status of the cluster deleting')
      client = boto3.client('cloudformation')
      cf_arn=event['cluster']['cloudformationStackArn']
      job_status=event['status']
      print(cf_arn)
      res = client.describe_stacks( StackName=cf_arn )
      if res['Stacks'][0]['StackStatus']=="DELETE_COMPLETE":
          current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          if job_status=="in progress":
              exec_table.update_item(
                  Key={
                      'id': int(id),
                      'receive_time': receive_time
                  },
                  UpdateExpression = 'SET cluster_delete_completed_time = :cluster_delete_completed_time , exec_status = :exec_status, ftime = :ftime',
                  ExpressionAttributeValues = {
                      ':cluster_delete_completed_time':current_time,
                      ':ftime':ftime,
                      ':exec_status': "success"
                  }
              )
          else:
              exec_table.update_item(
                  Key={
                      'id': int(id),
                      'receive_time': receive_time
                  },
                  UpdateExpression = 'SET cluster_delete_completed_time = :cluster_delete_completed_time , exec_status = :exec_status, ftime = :ftime, reason=:reason',
                  ExpressionAttributeValues = {
                      ':cluster_delete_completed_time':current_time,
                      ':ftime':ftime,
                      ':reason':"wrf run timeout",
                      ':exec_status': "failed"
                  }
              )
      out={}
      out['action']='destroystatus'
      out['ftime']=ftime
      out['id']=id
      out['receive_time']=receive_time
      out['status']=job_status
      out['cluster']={
        "cloudformationStackArn":cf_arn,
        "clusterStatus":res['Stacks'][0]['StackStatus']
      }
      return out
