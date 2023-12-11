import json
import boto3
import os
import re
from datetime import datetime

ssm = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    if (event["Records"]=="test"):
        key=r"gfs.20231122/00/atmos/gfs.t00z.pgrb2.0p50.f096"
    else:
        msg = json.loads(event["Records"][0]["Sns"]["Message"])
        key = msg["Records"][0]["s3"]["object"]["key"]
    key_str=r"gfs.t(?P=h)z.pgrb2.0p50.f096"
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
    print(key)
    ftime = f"{m.group('y')}-{m.group('m')}-{m.group('d')}T{m.group('h')}:00:00Z"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_timestamp = str(int(datetime.now().timestamp()))

    exec_table = dynamodb.Table(os.getenv('EXEC_DB'))
    exec_table.put_item(Item={'ftime': ftime, 'receive_time': current_time,'id':current_timestamp})
    para_table = dynamodb.Table(os.getenv('PARA_DB'))
    response = para_table.scan()
    items = response['Items']
    domains_num = 0
    fcst_days = "0"
    auto_mode = "False"
    
    domains_num=len(items)
    response = ssm.get_parameter(Name=os.getenv('AUTO_MODE'))
    auto_mode = response['Parameter']['Value']    
    response = ssm.get_parameter(Name=os.getenv('FCST_DAYS'))
    fcst_days = response['Parameter']['Value']    
    if domains_num==0 or auto_mode=="False" or fcst_days=="0":
        print("stop working")
        exec_table.update_item(
            Key={
                'ftime':ftime,
                'id': current_timestamp
            },
            UpdateExpression = 'SET end_time = :end_time, exec_status = :exec_status, reason = :reason',
            ExpressionAttributeValues = {
                ':end_time':current_time,
                ':exec_status':'failed',
                ':reason':r'condition not satisfied,domains number is {},auto mode is {}, fcst days is {}'.format(domains_num,auto_mode,fcst_days)
            }
        )
        return
    for item in items:
        item['cores']=str(item['cores'])
        item.pop('domain_size')
        item.pop('domain_center')
    domain_items=json.dumps(items)
    sfn = boto3.client('stepfunctions')
    sfn.start_execution(
        stateMachineArn=os.getenv("SM_ARN"),
        input = "{\"action\" : \"create\",\"type\" : \"od\",\"ftime\":\"" + ftime + "\",\"fcst_days\":\""+fcst_days+"\",\"domains\":"+domain_items+",\"id\":\""+current_timestamp+"\",\"receive_time\":\""+current_time+"\"}"
    )
    exec_table.update_item(
        Key={            
            'id': current_timestamp,
            'receive_time': current_time
        },
        UpdateExpression = 'SET start_time = :start_time, exec_status = :exec_status, ftime = :ftime',
            ExpressionAttributeValues = {
                ':start_time':current_time,
                ':ftime':ftime,
                ':exec_status':"in progress"
            }
    )

