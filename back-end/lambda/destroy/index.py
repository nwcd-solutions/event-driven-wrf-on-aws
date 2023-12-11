import json
import boto3
import os
import re
from datetime import datetime

ssm = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    print(event)
    response = ssm.get_parameter(Name=os.getenv('FTIME'))
    ftime = response['Parameter']['Value']    
    response = ssm.get_parameter(Name= os.getenv('EXEC_ID'))
    id = response['Parameter']['Value']    
    response = ssm.get_parameter(Name= os.getenv('EXEC_RECEIVE_TIME'))
    receive_time = response['Parameter']['Value'] 
    clustername=os.getenv('CLUSTER_NAME')
    region=os.getenv('REGION')
    sfn = boto3.client('stepfunctions')
    sfn.start_execution(
        stateMachineArn=os.getenv("SM_ARN"),
        input = "{\"status\" : \"in progress\",\"action\" : \"destroy\",\"clusterName\":\""+clustername+ "\",\"region\":\""+region+"\",\"ftime\":\""+ftime + "\",\"id\":\""+id + "\"}"
    )
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exec_table = dynamodb.Table(os.getenv('EXEC_DB'))
    exec_table.update_item(
        Key={
            'id': id,
            'receive_time': current_time
        },
        UpdateExpression = 'SET job_finished_time = :job_finished_time  , exec_status = :exec_status, ftime = :ftime',
        ExpressionAttributeValues = {
            ':job_finished_time':current_time,
            ':ftime':ftime,
            ':exec_status':"success"
        }
    )   
