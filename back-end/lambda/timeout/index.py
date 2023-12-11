import json
import boto3
from datetime import datetime
import os

def handler(event, context):
    stack_arn = event['clustername']
    ftime=event['ftime']
    id=event['id']
    region=event['region']
    receive_time=event['receive_time']
    stark_name=stack_arn.split('/')[1]
    cfn = boto3.client('cloudformation')
    res = cfn.describe_stacks(StackName=stack_arn)
    if res['Stacks'][0]['StackStatus']=="DELETE_COMPLETE":
        print(f"Stack {stack_arn} does not exist")
        return {"stack_status":"not exist"}    
    else:
        print(f"Stack {stack_arn} exists")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dynamodb = boto3.resource('dynamodb')
        exec_table = dynamodb.Table(os.getenv('EXEC_DB'))
        exec_table.update_item(
            Key={
                'id': id,
                'receive_time': current_time
            },
            UpdateExpression = 'SET job_timeout_time = :job_timeout_time , exec_status = :exec_status, ftime = :ftime',
            ExpressionAttributeValues = {
            ':job_timeout_time':current_time,
            ':ftime':ftime, 
            ':exec_status': "error"
            }
        )        
        out={
            "stack_status":"exist",
            "action":"destroy",
            "status":"error",
            "ftime":ftime,
            "id":id,
            "region":region,
            "receive_time":receive_time,
            "clusterName":stack_name
        }
        return out




