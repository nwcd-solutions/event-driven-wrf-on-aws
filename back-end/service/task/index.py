import boto3
import random
import json
import base64
import os
from boto3.dynamodb.conditions import Key
from datetime import datetime,timedelta

ddb = boto3.resource('dynamodb')
table = ddb.Table(os.getenv('EXEC_DB'))
#table = ddb.Table('test_db2')
def handler(event, context):
    #if not event['requestContext']['authorizer']:
    #    raise Exception('Authorization not configured')
    #username = event['requestContext']['authorizer']['claims']['cognito:username']
    operation = event['httpMethod']
    if operation == 'GET':
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        past = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        print(start_date,end_date)
        response = table.scan(
            FilterExpression=Key("receive_time").gt(start_date)
        )
        if 'Items' in response:
            last_7d_success=0
            last_7d_failed=0
            last_7d_error=0
            last_d_success=[]
            last_d_failed=[]
            print(response['Items'])
            for item in response['Items']:
                if item['exec_status']=='success':
                    last_7d_success =last_7d_success +1
                elif item['exec_status']=='failed':
                    last_7d_failed=last_7d_failed+1
                elif item['exec_status'] == 'error':
                    last_7d_failed = last_7d_error +1
                if item['receive_time']> past:
                    last_d_item={}
                    last_d_item['receive_time']=item['receive_time']
                    last_d_item['ftime']=item['ftime']
                    last_d_item['exec_status']=item['exec_status']
                    
                    if item['exec_status']=='success':
                        last_d_item['job_finished_time']=item['job_finished_time']
                        last_d_item['cluster_created_time'] = item['cluster_create_completed_time']
                        #last_d_item['cluster_deleted_time'] = item['cluster_delete_completed_time']
                        date_format = "%Y-%m-%d %H:%M:%S"
                        start_time = datetime.strptime(item['cluster_create_completed_time'], date_format)
                        end_time = datetime.strptime(item['job_finished_time'], date_format)
                        time_diff = end_time - start_time
                        last_d_item['run_duration'] = str(int(time_diff.total_seconds() / 60))
                        last_d_success.append(last_d_item)
                    else:
                        last_d_item['reason']=item['reason']
                        last_d_failed.append(last_d_item)
            response={
                "last_7d_success":last_7d_success,
                "last_7d_failed":last_7d_failed,
                "last_day_success":last_d_success,
                "last_day_failed": last_d_failed
            }        

            print(last_d_failed,last_d_success,last_7d_error,last_7d_failed,last_7d_success)
            return {
                'statusCode': 200,
                'body': json.dumps(response),
                'headers': {'Access-Control-Allow-Origin': '*'}
            }
        else:
            response={
                "last_7d_success":0,
                "last_7d_failed":0,
                "last_day_success":[],
                "last_day_failed": []
            }  
            return {
                'statusCode': 200,
                'body': json.dumps(response),
                'headers': {'Access-Control-Allow-Origin': '*'}
            }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid operation'),
            'headers': { 'Access-Control-Allow-Origin': '*' }
        }    
