from aws_cdk import (
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_logs as logs,
    aws_s3 as s3,
    CfnOutput, NestedStack, Tags, Duration, Size
)
import aws_cdk as core
from constructs import Construct

class ApiGateway(NestedStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)
        bucket_name = kwargs["bucket"]
        domain_name = kwargs["bucket"]
        layer = kwargs["layer"]
        datastore = kwargs["datastore"]
        #---------------------------------------------------------------------------------------------
        # Create a Cognito User Pool
        #---------------------------------------------------------------------------------------------
        self.user_pool = cognito.UserPool(
            self, 
            "WrfUserPool",
            #sign_in_type=cognito.SignInType.EMAIL,
            #auto_verified_attributes=[cognito.UserPoolAttribute.EMAIL],
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        #---------------------------------------------------------------------------------------------
        # Create a Cognito User Pool Client
        #---------------------------------------------------------------------------------------------        
        self.user_pool_client = cognito.UserPoolClient(
            self,
            "WrfUserPoolClient",
            user_pool=self.user_pool,
            user_pool_client_name='wrf-web-app',
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            o_auth=cognito.OAuthSettings(
            #    flows=cognito.OAuthFlows(
            #        authorization_code_grant=True
            #    ),
            #    scopes=[cognito.OAuthScope.OPENID],
                callback_urls=["http://localhost:3000"],
                logout_urls=["http://localhost:3000"]
            )
        )
        #self.cognito_domain = self.user_pool.add_domain(
        #    "Domain",
        #    cognito_domain=cognito.CognitoDomainOptions(
        #        domain_prefix = domain_name
        #    )
        #)
        #self.cognito_domain.apply_removal_policy(core.RemovalPolicy.DESTROY)
        
        # Create a Cognito Identity Pool
        cognito_identity_provider_property = cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
            client_id = self.user_pool_client.user_pool_client_id,
            provider_name = self.user_pool.user_pool_provider_url,
        )
        identity_pool = cognito.CfnIdentityPool(self, "IdentityPool", 
            cognito_identity_providers=[
                {
                    client_id : self.user_pool_client.user_pool_client_id,
                    provider_name : self.user_pool.user_pool_provider_name,
                }
            ],
            allow_unauthenticated_identities=False
        )
        s3_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            resources=["*"],
        )
        auth_role = iam.Role(
            self, 'AuthRole',
            assumed_by=iam.FederatedPrincipal(
                'cognito-identity.amazonaws.com',
            ),
        )

        auth_role.add_to_policy(s3_policy)
        cognito.CfnIdentityPoolRoleAttachment(
            self, 'IdentityPoolRoleMap',
            identity_pool_id=identity_pool.ref,
            roles={
                'authenticated': auth_role.role_arn,
            },
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
                "DOMAIN_DB": datastore.domain_db.table_name,
                "DEPLOYMENT_TYPE":"production",
                "PATH":"/opt/node/bin:${PATH}",
                "PYTHONPATH":"/opt/python",
                "WRFCLOUD_BUCKET":bucket_name
            },
            log_retention=logs.RetentionDays.ONE_DAY,
            role  =domain_service_handler_role,
            runtime = _lambda.Runtime.PYTHON_3_9,
            handler = "index.handler",
            layers=[layer],
            timeout= Duration.seconds(30),
            memory_size= 1024, 
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
                "AUTO_MODE": datastore.auto_mode_ssm.parameter_name,
                "PARAS_LIST": f"{datastore.fcst_days_ssm.parameter_name},{datastore.key_str_ssm.parameter_name},{datastore.job_timeout_ssm.parameter_name}",
                "PYTHONPATH":"/opt/python",
            },
            log_retention=logs.RetentionDays.ONE_DAY,
            role  = parameter_service_handler_role,
            runtime = _lambda.Runtime.PYTHON_3_9,
            handler = "index.handler",
            layers=[layer],
        )
        #---------------------------------------------------------------------------------------------
        # Create Task Service Lambda fuction
        #---------------------------------------------------------------------------------------------
        task_service_handler_policy_doc = iam.PolicyDocument(statements=[
            iam.PolicyStatement(
                actions=["ssm:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
        ])
        task_service_handler_role = iam.Role(self, "task_service_handler_Role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sts.amazonaws.com"),
            ),
            description="CreateAPILambdaRole",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ],
            inline_policies={"service_lambda": task_service_handler_policy_doc},
        )

        task_service_handler = _lambda.Function(self,"task_service",
            code=_lambda.Code.from_asset("./service/task"),
            environment={
                "AUTO_MODE": datastore.auto_mode_ssm.parameter_name,
                "PARAS_LIST": f"{datastore.fcst_days_ssm.parameter_name},{datastore.key_str_ssm.parameter_name},{datastore.job_timeout_ssm.parameter_name}",
                "PYTHONPATH":"/opt/python",
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
        self.api = apigw.RestApi(
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
            cognito_user_pools=[self.user_pool],
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
        #---------------------------------------------------------------------------------------------
        # Create Domain Resource and methods
        #---------------------------------------------------------------------------------------------
        domain_resource = self.api.root.add_resource("domain")

        domain_options_method  = domain_resource.add_method(
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
        domain_any_method = domain_resource.add_method(
            "ANY",
            apigw.LambdaIntegration(domain_service_handler),
            authorizer=authorizer,
        )
        #---------------------------------------------------------------------------------------------
        # Create Parameter Resource and methods
        #---------------------------------------------------------------------------------------------
        parameter_resource = self.api.root.add_resource("parameter")

        parameter_options_method  = parameter_resource.add_method(
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
        parameter_any_method = parameter_resource.add_method(
            "ANY",
            apigw.LambdaIntegration(parameter_service_handler),
            authorizer=authorizer,
        )
        #---------------------------------------------------------------------------------------------
        # Create Task Resource and methods
        #---------------------------------------------------------------------------------------------
        task_resource = self.api.root.add_resource("task")

        task_options_method  = task_resource.add_method(
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
        task_any_method = task_resource.add_method(
            "ANY",
            apigw.LambdaIntegration(task_service_handler),
            authorizer=authorizer,
        )

