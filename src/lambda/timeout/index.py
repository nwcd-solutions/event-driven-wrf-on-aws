import json
import boto3
from datetime import datetime
import os

def handler(event, context):
    stack_name = event['clustername']
    ftime=event['ftime']
    id=event['id']
    region=event['region']
   
    cfn = boto3.client('cloudformation')
    res = cfn.describe_stacks(StackName=stack_name)
    if res['Stacks'][0]['StackStatus']=="DELETE_COMPLETE":
        print(f"Stack {stack_name} does not exist")
        return {"stack_staus":"not exist"}    
    else:
        print(f"Stack {stack_name} exists")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dynamodb = boto3.resource('dynamodb')
        exec_table = dynamodb.Table(os.getenv('EXEC_DB'))
        exec_table.update_item(
            Key={
                'ftime':ftime,
                'id': id
            },
            UpdateExpression = 'SET job_timeout_time = :job_timeout_time , exec_status = :exec_status',
            ExpressionAttributeValues = {
            ':job_timeout_time':current_time,
            ':exec_status': "error"
            }
        )        
        out={
            "stack_staus":"exist",
            "action":"destroy",
            "status":"error",
            "ftime":ftime,
            "id":id,
            "region":region,
            "clusterName":stack_name
        }
        return out



