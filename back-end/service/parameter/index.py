import boto3
import random
import json
import base64
import os
from boto3.dynamodb.conditions import Key

ssm = boto3.client('ssm')

def handler(event, context):
    print(event)
    if not event['requestContext']['authorizer']:
        raise Exception('Authorization not configured')
    username = event['requestContext']['authorizer']['claims']['cognito:username']
    operation = event['httpMethod']
    if operation == 'GET':
        if 'name' in event['queryStringParameters']:
            response = ssm.get_parameter(
                Name= event['queryStringParameters']['name'],
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps(response['Parameter']['Value']),
                'headers': {'Access-Control-Allow-Origin': '*'}
            }
        else:
            paras=[]
            envs=os.getenv('PARAS_LIST').split(',')
            print(envs)
            for para in envs:
                print(para)
                response = ssm.get_parameter(
                    Name= para,
                )
                item={
                    "name":para.split("/")[-1],
                    "description":para,
                    "value":response['Parameter']['Value']
                }
                paras.append(item)
                
            response = ssm.get_parameter(
                Name= os.getenv('AUTO_MODE'),
            )
            result={
                "auto":{
                    "value":response['Parameter']['Value']
                },
                "para":paras
            }
            print('result')
            print(paras)
            return {
                'statusCode': 200,
                'body': json.dumps(result),
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Header': '*'
                }
            }
    elif operation == 'POST':
        item = json.loads(event['body'])
        try:
            table.put_item(Item=item)
            return {
                'statusCode': 200,
                'body': json.dumps('Item added successfully'),
                'headers': {'Access-Control-Allow-Origin': '*'}
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'Error': str(e),
                    'Reference': context.aws_request_id
                }),
                'headers': { 'Access-Control-Allow-Origin': '*' }
            }
    elif operation == 'PUT':
        item = json.loads(event['body'])
        ssm.put_parameter(
            Name=item['name'],
            Value= item['value'],
            Type='String',
            Overwrite=True
        )
        return {
            'statusCode': 200,
            'body': json.dumps('Item updated successfully'),
            'headers': { 'Access-Control-Allow-Origin': '*' }
        }
    elif operation == 'DELETE':
        table.delete_item(
            Key={
                'id': event['pathParameters']['id']
            }
        )
        return {
            'statusCode': 200,
            'body': json.dumps('Item deleted successfully'),
            'headers': { 'Access-Control-Allow-Origin': '*' }
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid operation'),
            'headers': { 'Access-Control-Allow-Origin': '*' }
        }    
