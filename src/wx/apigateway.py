from aws_cdk import (
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_logs as logs,
    aws_s3 as s3,
    CfnOutput, NestedStack, Tags
)
from constructs import Construct

class ApiGateway(NestedStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)
        bucket_name = kwargs["bucket"]
        layer = kwargs["layer"]
        datastore = kwargs["datastore"]
        #---------------------------------------------------------------------------------------------
        # Create a Cognito User Pool
        #---------------------------------------------------------------------------------------------
        user_pool = cognito.UserPool(
            self, 
            "WrfUserPool",
            #sign_in_type=cognito.SignInType.EMAIL,
            #auto_verified_attributes=[cognito.UserPoolAttribute.EMAIL],
        )
        #---------------------------------------------------------------------------------------------
        # Create a Cognito User Pool Client
        #---------------------------------------------------------------------------------------------        
        user_pool_client = cognito.UserPoolClient(
            self,
            "WrfUserPoolClient",
            user_pool=user_pool,
            user_pool_client_name='wrf-web-app',
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
        )
        #---------------------------------------------------------------------------------------------
        # Create domain service Lambda functions
        #---------------------------------------------------------------------------------------------
        domain_service_handler_policy_doc = iam.PolicyDocument(statements=[
            iam.PolicyStatement(
                actions=["s3:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["dynamodb:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
        ])
        domain_service_handler_role = iam.Role(self, "domain_service_handler_Role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sts.amazonaws.com"),
            ),
            description="CreateAPILambdaRole",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ],
            inline_policies={"service_lambda": domain_service_handler_policy_doc},
        )

        domain_service_handler = _lambda.Function(self,"domain_service",
            code=_lambda.Code.from_asset("./service/domain"),
            environment={
                "DOAMIN_DB": datastore.domain_db.table_name,
                "DEPLOYMENT_TYPE":"production",
                "PATH":"/opt/node/bin:${PATH}",
                "PYTHONPATH":"/opt/python/lib",
                "WRFCLOUD_BUCKET":""
            },
            log_retention=logs.RetentionDays.ONE_DAY,
            role  =domain_service_handler_role,
            runtime = _lambda.Runtime.PYTHON_3_9,
            handler = "index.handler",
            layers=[layer],
            timeout=Duration.seconds(30),
            memory=Size.mebibytes(1024),  
            ephemeralStorageSize=Size.mebibytes(512),
        )
        #---------------------------------------------------------------------------------------------
        # Create Parameter Service Lambda fuction
        #---------------------------------------------------------------------------------------------
        parameter_service_handler_policy_doc = iam.PolicyDocument(statements=[
            iam.PolicyStatement(
                actions=["ssm:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
        ])
        parameter_service_handler_role = iam.Role(self, "parameter_service_handler_Role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sts.amazonaws.com"),
            ),
            description="CreateAPILambdaRole",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ],
            inline_policies={"service_lambda": parameter_service_handler_policy_doc},
        )

        parameter_service_handler = _lambda.Function(self,"parameter_service",
            code=_lambda.Code.from_asset("./service/parameter"),
            environment={
                "AUTO_MODE": datastore.ssm_auto_mode,
                "PARAS_LIST":datastore..ssm_fcst_days,
            },
            log_retention=logs.RetentionDays.ONE_DAY,
            role  = parameter_service_handler_role,
            runtime = _lambda.Runtime.PYTHON_3_9,
            handler = "index.handler",
            layers=[layer],
        )

        #---------------------------------------------------------------------------------------------
        # Create an API Gateway
        #---------------------------------------------------------------------------------------------
        api = apigw.RestApi(
            self,
            "WrfAPIGateway",
            rest_api_name="WrfAPIGateway",
            #default_cors_preflight_options=apigw.CorsOptions(
            #    allow_origins=apigw.Cors.ALL_ORIGINS,
            #    allow_methods=apigw.Cors.ALL_METHODS,
            #    allow_headers=["*"],
            #),
        )

        # Create a Cognito Authorizer
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "Authorizer",
            cognito_user_pools=[user_pool],
        )
        api_lambda_exec_role = iam.Role(
            self,
            'ApiLambdaExecRole',
            assumed_by=iam.ServicePrincipal('apigateway.amazonaws.com')
        )
        api_lambda_exec_policy = iam.Policy(
            self,
            'apiLambdaExecPolicy',
            statements=[
                iam.PolicyStatement(
                    actions=['lambda:InvokeFunction'],
                    resources=[
                        domain_service_handler.function_arn,
                    ]
                )
            ]
        )
        api_lambda_exec_policy.attach_to_role(api_lambda_exec_role)

        # Create a Resource
        resource = api.root.add_resource("domain")

        # Create a Method

        options_method  = resource.add_method(
            'OPTIONS',
            apigw.MockIntegration(
                integration_responses=[{
                    'statusCode': '200',
                    'responseParameters': {
                        #'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,access-control-allow-headers,access-control-allow-origin'",
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Methods': "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'"
                    },
                }],
                passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH,
                credentials_role=api_lambda_exec_role,
                request_templates={
                    "application/json": "{\"statusCode\": 200}"
                },
            ),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True
                },
            }],
            request_parameters={'method.request.header.access-control-allow-origin':True}
         
        )
        any_method = resource.add_method(
            "GET",
            apigw.LambdaIntegration(domain_service_handler),
            authorizer=authorizer,
        )


