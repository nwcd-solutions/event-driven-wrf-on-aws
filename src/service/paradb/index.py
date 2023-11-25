import boto3
import random
import json
import base64
import os
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb')
table = ddb.Table(os.getenv('PARA_DB'))

def handler(event, context):
    if not event['requestContext']['authorizer']:
        raise Exception('Authorization not configured')
    username = event['requestContext']['authorizer']['claims']['cognito:username']
    operation = event['httpMethod']
    if operation == 'GET':
        if 'id' in event['queryStringParameters']:
            response = table.get_item(
                Key={
                    'id': event['queryStringParameters']['id']
                }
            )
            return {
                'statusCode': 200,
                'body': json.dumps(response['Item']),
                'headers': {'Access-Control-Allow-Origin': '*'}
            }
        else:
            response = table.scan()
            return {
                'statusCode': 200,
                'body': json.dumps(response['Items']),
                'headers': {'Access-Control-Allow-Origin': '*'}
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
        table.update_item(
            Key={
                'id': event['pathParameters']['id']
            },
            UpdateExpression='SET #n = :val1, nodes = :val2',
            ExpressionAttributeNames={
                '#n': 'name'
            },
            ExpressionAttributeValues={
                ':val1': item['name'],
                ':val2': item['nodes']
            }
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
