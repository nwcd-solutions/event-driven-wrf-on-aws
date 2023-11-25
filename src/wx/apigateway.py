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
        para_db = kwargs["para_db"]
        #---------------------------------------------------------------------------------------------
        # Create a Cognito User Pool
        #---------------------------------------------------------------------------------------------
        user_pool = cognito.UserPool(
            self, 
            "WrfUserPool",
            sign_in_type=cognito.SignInType.EMAIL,
            auto_verified_attributes=[cognito.UserPoolAttribute.EMAIL],
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

        # Create a Lambda function
        para_db_handler_policy_doc = iam.PolicyDocument(statements=[
            iam.PolicyStatement(
                actions=["s3:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["dynamodb:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
        ])
        para_db_handler_role = iam.Role(self, "para_db_handler_Role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sts.amazonaws.com"),
            ),
            description="CreateAPILambdaRole",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                ],
            inline_policies={"service_lambda": para_db_handler_policy_doc},
        )

        para_db_handler = _lambda.Function(self,"para_db_op",
            code=_lambda.Code.from_asset("./service/paradb"),
            environment={
                "PARA_DB": para_db.table_name,
            },
            log_retention=logs.RetentionDays.ONE_DAY,
            role  =para_db_handler_role,
            runtime = _lambda.Runtime.PYTHON_3_9,
            handler = "index.handler",
        )

        # Create an API Gateway
        api = apigw.RestApi(
            self,
            "WrfAPIGateway",
            rest_api_name="WrfAPIGateway",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["*"],
            ),
        )

        # Create a Cognito Authorizer
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "Authorizer",
            cognito_user_pools=[user_pool],
        )

        # Create a Resource
        resource = api.root.add_resource("domain")

        # Create a Method
        method = resource.add_method(
            "GET",
            apigw.LambdaIntegration(para_db_handler),
            authorizer=authorizer,
        )
        method = resource.add_method(
            "POST",
            apigw.LambdaIntegration(para_db_handler),
            authorizer=authorizer,
        )
        method = resource.add_method(
            "PUT",
            apigw.LambdaIntegration(para_db_handler),
            authorizer=authorizer,
        )
        method = resource.add_method(
            "DELETE",
            apigw.LambdaIntegration(para_db_handler),
            authorizer=authorizer,
        )
