import boto3
import random
import json
import base64
import gzip
import os
from boto3.dynamodb.conditions import Key
from config import get_all_configs_in_system
from config import get_config_from_system
from config import add_config_to_system
from config import delete_config_from_system
from config import update_config_in_system
from config import WrfConfig



def handler(event, context):
    if not event['requestContext']['authorizer']:
        raise Exception('Authorization not configured')
    username = event['requestContext']['authorizer']['claims']['cognito:username']
    response: dict = {}
    body = {}
    errors = []
    print(event)
    operation = event['httpMethod']
    if operation == 'GET':
        if event['queryStringParameters'] is None or  ('configuration_name' not in event['queryStringParameters']):
            try:
                configs = get_all_configs_in_system()
                response = [config.data for config in configs]
                return {
                    'statusCode': 200,
                    'isBase64Encoded': True,
                    'body': base64.b64encode(gzip.compress(json.dumps(response).encode())),
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Content-Type': 'application/json',
                        'Content-Encoding': 'gzip'
                    }
                }
            except Exception as e:
                return {
                'statusCode': 500,
                'body': json.dumps({
                    'Error': 'Failed to get a list of model configurations in the system'+ str(e),
                    'Reference': context.aws_request_id
                }),
                'headers': { 'Access-Control-Allow-Origin': '*' }
            }
        else:
            try:
                config = get_config_from_system(event['queryStringParameters']['configuration_name'])
                response = config.sanitized_data 
                return {
                    'statusCode': 200,
                    'isBase64Encoded': True,
                    'body': base64.b64encode(gzip.compress(json.dumps(response).encode())),
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Content-Type': 'application/json',
                        'Content-Encoding': 'gzip'
                    }
                }
            except Exception as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'Error': 'Failed to get model configurations in the system'+ str(e),
                        'Reference': context.aws_request_id
                    }),
                    'headers': { 'Access-Control-Allow-Origin': '*' }
                }
                
    elif operation == 'POST':
        request=json.loads(event['body'])
        body['ok'],body['errors'],body['data'] = CreateNewDomain(json.loads(request['data']['model_config']))
        if body['ok']:
            return {
                'statusCode': 200,
                'isBase64Encoded': True,
                'body': base64.b64encode(gzip.compress(json.dumps(body).encode())),
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json',
                    'Content-Encoding': 'gzip'
                }    
            }
        else:
            return {
                'statusCode': 500,
                'body': body,
                'headers': { 'Access-Control-Allow-Origin': '*' } 
            }
            
    elif operation == 'PUT':

        request=json.loads(event['body'])
        body['ok'],body['errors'],body['data'] = UpdateDomain(json.loads(request['data']['model_config']))
        if body['ok']:
            return {
                'statusCode': 200,
                'isBase64Encoded': True,
                'body': base64.b64encode(gzip.compress(json.dumps(body).encode())),
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json',
                    'Content-Encoding': 'gzip'
                }    
            }
        else:
            return {
                'statusCode': 500,
                'body': body,
                'headers': { 'Access-Control-Allow-Origin': '*' } 
            }
        
    elif operation == 'DELETE':
        body['ok'],body['errors'],body['data'] = DeleteDomain(event['queryStringParameters']['configuration_name'])
        if body['ok']:
            return {
                'statusCode': 200,
                'isBase64Encoded': True,
                'body': base64.b64encode(gzip.compress(json.dumps(body).encode())),
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json',
                    'Content-Encoding': 'gzip'
                }    
            }
        else:
            return {
                'statusCode': 500,
                'body': body,
                'headers': { 'Access-Control-Allow-Origin': '*' } 
            }
            
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid operation'),
            'headers': { 'Access-Control-Allow-Origin': '*' }
        }    
        

def CreateNewDomain(request):
    errors=[]
    response={}
    try:
        # build a WrfConfig object
        config: WrfConfig = WrfConfig(request)
        # validate the configuration data
        if not config.validate():
            errors.append('Configuration is invalid.')
            ok = False
            return ok,errors,response
        # check if there is already a configuration with the same name
        existing: WrfConfig = get_config_from_system(config.name)
        if existing is not None:
            errors.append('The configuration name is already in use. Please choose a unique name.')
            ok = False
            return ok,errors,response
        # add the model configuration to the system
        ok = add_config_to_system(config)
        if ok:
            response['model_config'] = config.sanitized_data
        return ok,errors,response
    except Exception as e:
        errors.append('Failed to add a model configuration to the system'+ str(e))
        ok=False
        return ok,errors,response   
        
        
def DeleteDomain(request):
    errors=[]
    response={}
    try:
        # build a WrfConfig object
        configuration_name: str = request

        # check if there is already a configuration with the same name
        existing: WrfConfig = get_config_from_system(configuration_name)
        if existing is None:
            errors.append('The configuration does not exist.')
            ok = False
            return ok,errors,response
        # delete the model configuration from the system
        ok = delete_config_from_system(existing)
        if ok:
            response['model_config'] = existing.sanitized_data
        return ok,errors,response
    except Exception as e:
        errors.append('Failed to delete a model configuration to the system', e)
        ok=False
        return ok,errors,response   
        
        
def UpdateDomain(request):
    errors=[]
    response={}
    try:
        # build a WrfConfig object
        config: WrfConfig = WrfConfig(request)
        # validate the configuration data
        if not config.validate():
            errors.append('Configuration is invalid.')
            ok = False
            return ok,errors,response
        # check if the configuration with the name already exists
        existing: WrfConfig = get_config_from_system(config.name)
        if existing is None:
            errors.append('The configuration does not exist and cannot be updated.')
            ok = False
            return ok,errors,response

        # update the model configuration in the system
        ok = update_config_in_system(config)
        if ok:
            response['model_config'] = config.sanitized_data
        return ok,errors,response
        
    except Exception as e:
        errors.append('Failed to update a model configuration in the system'+str(e))
        ok = False    
        return ok,errors,response
