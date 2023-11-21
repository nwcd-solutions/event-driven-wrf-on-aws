import json
import boto3
import os
import re

def main(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.getenv('DYNAMODB'))
    response = table.scan()
    items = response['Items']
    domains_num = 0
    fcst_days = 0
    auto_mode = False
    key_str=r"gfs.t(?P=h)z.pgrb2.0p50.f096"
    print(items)
    for item in items:
        if item['para_name'] == 'domain':
            domains_num = len(item['value'])
            print("domains:")
            print(domains_num)
        if item['para_name'] == 'auto_mode':
            auto_mode = item['value']
            print("mode")
            print(auto_mode)
        if item['para_name'] =='fcst_days':
            fcst_days = item['value']
            print("fcst days:")
            print(fcst_days)
        if item['para_name'] == 'key_str':
            key_str == item['value']
            print(key_str)
    if domains_num==0 or auto_mode==False or fcst_days==0:
        print("stop working")
        return

    msg = json.loads(event["Records"][0]["Sns"]["Message"])
    key = msg["Records"][0]["s3"]["object"]["key"]
    prefix_str=r"""
                gfs.                      # GFS prefix
                (?P<y>\d{4})              # Year
                (?P<m>\d{2})              # Month
                (?P<d>\d{2})              # Day
                /(?P<h>\d{2})             # Hour
                /atmos/
                """
    
    p = re.compile(r"{}$".format(prefix_str+key_str),re.VERBOSE)
    m = p.match(key)
    if not m:
        return
    print(event)
    print(msg)
    print(key)
    ftime = f"{m.group('y')}-{m.group('m')}-{m.group('d')}T{m.group('h')}:00:00Z"

    sfn = boto3.client('stepfunctions')
    sfn.start_execution(
        stateMachineArn=os.getenv("SM_ARN"),
        input = "{\"action\" : \"create\",\"type\" : \"od\",\"ftime\":\"" + ftime + "\",\"fcst_days\":\""+fcst_days+"\"}"
    )

def destroy(event, context):
    print(event)
    clustername=os.getenv('CLUSTER_NAME')
    region=os.getenv('REGION')
    sfn = boto3.client('stepfunctions')
    sfn.start_execution(
        stateMachineArn=os.getenv("SM_ARN"),
        input = "{\"action\" : \"destroy\",\"clusterName\":\""+clustername+ "\",\"region\":\""+region+"\",\"ftime\":\" \"}"
    )
