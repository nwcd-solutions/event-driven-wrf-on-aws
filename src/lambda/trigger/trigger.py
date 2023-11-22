import json
import boto3
import os
import re

def main(event, context):
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
    print(msg)
    print(key)
    ftime = f"{m.group('y')}-{m.group('m')}-{m.group('d')}T{m.group('h')}:00:00Z"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_timestamp = str(int(datetime.now().timestamp()))
    
    dynamodb = boto3.resource('dynamodb')
    exec_table = dynamodb.Table(os.getenv('EXEC_DB'))
    exec_table.put_item(Item={'ftime': ftime, 'receive_time': current_time,'id':current_timestamp})
    para_table = dynamodb.Table(os.getenv('PARA_DB'))
    response = para_table.scan()
    items = response['Items']
    domains_num = "0"
    fcst_days = "0"
    auto_mode = "False"
    
    domains_num=str(len(items))
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=os.getenv('AUTO_MODE'))
    auto_mode = response['Parameter']['Value']    
    response = ssm.get_parameter(Name=os.getenv('FCST_DAYS'))
    fcst_days = response['Parameter']['Value']    
    if domains_num=="0" or auto_mode=="False" or fcst_days=="0":
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
    sfn = boto3.client('stepfunctions')
    sfn.start_execution(
        stateMachineArn=os.getenv("SM_ARN"),
        input = "{\"action\" : \"create\",\"type\" : \"od\",\"ftime\":\"" + ftime + "\",\"fcst_days\":\""+fcst_days+"\",\"domains_num\":\""+domains_num+"\",\"id\":\""+current_timestamp+"\",\"id\":\""+current_timestamp+"\"}"
    )
    exec_table.update_item(
        Key={
            'ftime':ftime,
            'id': current_timestamp
        },
        UpdateExpression = 'SET start_time = :start_time',
            ExpressionAttributeValues = {
                ':start_time':current_time
            }
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
