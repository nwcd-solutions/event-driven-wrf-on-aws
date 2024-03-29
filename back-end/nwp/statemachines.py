from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as λ,
    aws_lambda_event_sources as λ_events,
    aws_logs as logs,
    aws_s3 as s3,
    aws_s3_assets as assets,
    aws_s3_notifications,
    aws_sns as sns,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_secretsmanager as secretsmanager,
    aws_dynamodb as dynamodb,
    aws_ssm as ssm,
    Aws, CfnOutput, Duration, Fn, NestedStack, Tags
)
import aws_cdk as core
from constructs import Construct
import json

class StepFunction (NestedStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)
        bucket_name = kwargs["bucket"]
        vpc = kwargs["vpc"]
        datastore = kwargs["datastore"]
        layer = kwargs["layer"]
        cluster_name = "wx-pcluster001"
       
        purl = Fn.import_value("ParallelClusterApiInvokeUrl")
        hostname = Fn.select(2, Fn.split("/", Fn.select(0, Fn.split('.', purl))))
        parn = f"arn:aws:execute-api:{Aws.REGION}::{hostname}/*/*/*"
        post_head_amd64 = assets.Asset(self, "PostComputeFileAsset",
                path="scripts/post_install_amd64.sh")

        jwt_key = "JWTKey"
        jwt = secretsmanager.Secret(self, "JWTCreds",
                secret_name=jwt_key,
                description="JSON Web Token for SLURM"
              )       
                
        sg_rds = ec2.SecurityGroup(
                self,
                id="sg_slurm",
                vpc=vpc,
                security_group_name="sg_slurm"
        )
        sg_rds.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(8080)
        )
        #-------------------------------------------------
        # Create SSM parameter store to store parameters
        #-------------------------------------------------
        fcst_days_ssm = datastore.fcst_days_ssm
        key_str_ssm = datastore.key_str_ssm
        auto_mode_ssm = datastore.auto_mode_ssm
        ftime_ssm = datastore.ftime_ssm
        exec_id_ssm = datastore.exec_id_ssm
        job_timeout_ssm = datastore.job_timeout_ssm
        receive_time_ssm = datastore.receive_time_ssm
        #----------------------------------------------------------------------------------------------
        # Create a DynamoDB table to store parameters of Domain and Step function execution record
        #----------------------------------------------------------------------------------------------
        domain_db = datastore.domain_db      
        exec_db = datastore.exec_db
        #--------------------------------------------------------------------------------------------
        # Create IAM policy for KMS ALL
        #--------------------------------------------------------------------------------------------
        kms_all_policy_doc = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid= "VisualEditor0",
                    effect=iam.Effect.ALLOW,
                    actions=["kms:*"],
                    resources=["*"]
                )
            ]
        )

        kms_all_policy = iam.ManagedPolicy(
            self,
            "kms_all",
            managed_policy_name="kms_all",
            document=kms_all_policy_doc
        )
        #-------------------------------------------------------------------------------------------
        # Create Lambda  Subnet
        #-------------------------------------------------------------------------------------------

        public_subnet = vpc.public_subnets[1].subnet_id
        for net in vpc.public_subnets:
            if net.availability_zone == "us-east-2b":
                public_subnet = net
        private_subnet = vpc.private_subnets[1].subnet_id
        for net in vpc.private_subnets:
            if net.availability_zone == "us-east-2b":
                private_subnet = net
        #-----------------------------------------------------------------------------------------------------------------------------
        # Create Lambda function to create parallel-cluster
        #-----------------------------------------------------------------------------------------------------------------------------
        create_policy_doc = iam.PolicyDocument(statements=[
            iam.PolicyStatement(
                actions=["execute-api:Invoke", "execute-api:ManageConnections"],
                resources=["arn:aws:execute-api:*:*:*"],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["states:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["iam:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["cloudformation:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=[
                    "dynamodb:*",
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath"
                ],
                resources=["*"],
                effect=iam.Effect.ALLOW),
        ])
        create_lambda_role = iam.Role(self, "Create_Lambda_Role",
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal("lambda.amazonaws.com"),
                    iam.ServicePrincipal("sts.amazonaws.com"),
                ),
                description="CreateAPILambdaRole",
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                    ],
                inline_policies={"cluster_lambda": create_policy_doc},
        )        
        cluster_lambda = λ.Function(self, "create_cluster",
                code=λ.Code.from_asset("./lambda/cluster"),
                environment={
                    "BUCKET_NAME": bucket_name,
                    "CLUSTER_NAME": cluster_name,
                    "JWTKEY": jwt_key,
                    "PCLUSTER_API_URL": purl,
                    "REGION": Aws.REGION,
                    "S3_URL_POST_INSTALL_HEADNODE": f"{post_head_amd64.s3_object_url}",
                    "SG": sg_rds.security_group_id,
                    "PUBLIC_SUBNETID": public_subnet,
                    "PRIVATE_SUBNETID": private_subnet,
                    "FORECAST_DAYS": fcst_days_ssm.parameter_name,
                    #"NUM_DOMAINS": domains,                    
                    "KMS_POLICY": kms_all_policy.managed_policy_arn,
                    "PARA_DB": domain_db.table_name,
                    "EXEC_DB": exec_db.table_name,
                    "PYTHONPATH":"/opt/python"
                },
                handler="index.handler",
                layers=[layer],
                log_retention=logs.RetentionDays.ONE_DAY,
                role=create_lambda_role,
                runtime=λ.Runtime.PYTHON_3_9,
                timeout=Duration.seconds(60)
            )
        Tags.of(cluster_lambda).add("Purpose", "Event Driven Weather Forecast", priority=300)    
        #-----------------------------------------------------------------------------
        # Create lambda function to submit fcst job
        #----------------------------------------------------------------------------- 
        run_policy_doc = iam.PolicyDocument()
        run_policy_doc.add_statements(iam.PolicyStatement(
            actions=[
                "secretsmanager:GetResourcePolicy",
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret",
                "secretsmanager:ListSecretVersionIds",
                "secretsmanager:ListSecrets",
            ],
            resources=["*"],
            effect=iam.Effect.ALLOW))
        run_policy_doc.add_statements(iam.PolicyStatement(
            actions=[
                "dynamodb:*",  
            ],
            resources=[
                domain_db.table_arn,
                exec_db.table_arn              
            ],
            effect=iam.Effect.ALLOW))
        run_policy_doc.add_statements(iam.PolicyStatement(
            actions=[
                "ssm:*",  
                "s3:*"
            ],
            resources=[
                "*"             
            ],
            effect=iam.Effect.ALLOW))
        run_role = iam.Role(self, "Run_Role",
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal("lambda.amazonaws.com"),
                    iam.ServicePrincipal("sts.amazonaws.com"),
                ),
                description="CreateForecastLambdaRole",
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                    ],
                inline_policies={"secretsmanager": run_policy_doc},
        )

        run = λ.Function(self, "run_forecast",
                code=λ.Code.from_asset("./lambda/forecast"),
                environment={
                    "BUCKET_NAME": bucket_name,
                    #"DOMAINS_NUM": domains,
                    #"FORECAST_DAYS":fcst_days_ssm.parameter_name,
                    "PARA_DB":domain_db.table_name,
                    #"EXEC_DB":exec_db.table_name,
                    "FTIME":ftime_ssm.parameter_name ,
                    "EXEC_ID": exec_id_ssm.parameter_name,
                    "JOB_TIMEOUT": job_timeout_ssm.parameter_name,
                    "EXEC_RECEIVE_TIME": receive_time_ssm.parameter_name,
                    "PYTHONPATH":"/opt/python"
                },
                handler="index.handler",
                layers=[layer],
                role=run_role,
                runtime=λ.Runtime.PYTHON_3_9,
                timeout=Duration.seconds(60),
                vpc=vpc,
            )
        Tags.of(run).add("Purpose", "Event Driven Weather Forecast", priority=300)

        #-----------------------------------------------------------------------------
        # Create lambda function to submit fcst job
        #----------------------------------------------------------------------------- 
        timeout_policy_doc = iam.PolicyDocument()
        timeout_policy_doc.add_statements(iam.PolicyStatement(
            actions=[
                "dynamodb:*",  
            ],
            resources=[
                domain_db.table_arn,
                exec_db.table_arn              
            ],
            effect=iam.Effect.ALLOW))
        timeout_policy_doc.add_statements(iam.PolicyStatement(
            actions=[
                "cloudformation:*",  
            ],
            resources=[
                "*"             
            ],
            effect=iam.Effect.ALLOW))
        timeout_role = iam.Role(self, "timeout_Role",
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal("lambda.amazonaws.com"),
                    iam.ServicePrincipal("sts.amazonaws.com"),
                ),
                description="CreateForecastLambdaRole",
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                    ],
                inline_policies={"secretsmanager": timeout_policy_doc},
        )

        timeout_func = λ.Function(self, "timeout_func",
                code=λ.Code.from_asset("./lambda/timeout"),
                environment={
                    "EXEC_DB":exec_db.table_name,
                    "PYTHONPATH":"/opt/python"
                },
                handler="index.handler",
                layers=[layer],
                role=timeout_role,
                runtime=λ.Runtime.PYTHON_3_9,
                timeout=Duration.seconds(60),
                vpc=vpc,
            )
        #-------------------------------------------------
        # Create IAM policy for step function
        #-------------------------------------------------
        sf_topic = sns.Topic(self, "WRF_workflow")
        main_sf_policy = iam.PolicyDocument(statements=[
            iam.PolicyStatement(
                actions=["sns:Publish"],
                resources=[sf_topic.topic_arn],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["events:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["states:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[cluster_lambda.function_arn,run.function_arn,timeout_func.function_arn],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"],
                resources=["*"],
                effect=iam.Effect.ALLOW),            
        ])    
        sf_role = iam.Role(self, "Main SF Role",
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal("states.amazonaws.com"),
                    iam.ServicePrincipal("sts.amazonaws.com"),
                ),
                description="Create Main Step Function Role",
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchEventsFullAccess"),
                    ],
                inline_policies={"main_sf_policy": main_sf_policy},
        )
        #-------------------------------------------------
        # Main Step function definition
        #-------------------------------------------------    
        main_sf_def={
          "Comment": "state machine to manager lifecycle of cluster",
          "StartAt": "Create cluster",
          "States": {
            "Create cluster": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": cluster_lambda.function_arn
              },
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 6,
                  "BackoffRate": 2
                }
              ],
              "Next": "Whether cluster could be created"
            },
            "Whether cluster could be created": {
              "Type": "Choice",
              "Choices": [
                {
                  "Not": {
                    "Variable": "$.clusterStatus",
                    "StringEquals": "CREATE_IN_PROGRESS"
                  },
                  "Next": "Publish Fail to create cluster message-1"
                }
              ],
              "Default": "Wait for cluster creating"
            },
            "Publish Fail to create cluster message-1": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn":sf_topic.topic_arn
              },
              "ResultPath":None,
              "Next": "Fail"
            },
            "Fail": {
              "Type": "Fail"
            },
            "destroy cluster": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": cluster_lambda.function_arn
              },
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 6,
                  "BackoffRate": 2
                }
              ],
              "Next": "Choice"
            },
            "Choice": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.cluster.clusterStatus",
                  "StringEquals": "DELETE_IN_PROGRESS",
                  "Next": "Wait for cluster deleting"
                }
              ],
              "Default": "Destroy failed notification (1)"
            },
            "Destroy failed notification (1)": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "ResultPath":None,
              "Next": "Fail"
            },
            "Wait for cluster deleting": {
              "Type": "Wait",
              "Seconds": 60,
              "Next": "Monitor deleting status"
            },
            "Monitor deleting status": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": cluster_lambda.function_arn
              },
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 6,
                  "BackoffRate": 2
                }
              ],
              "Next": "Whether Success Deleted"
            },
            "Whether Success Deleted": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.cluster.clusterStatus",
                  "StringEquals": "DELETE_COMPLETE",
                  "Next": "Destroy complete notification"
                },
                {
                  "Variable": "$.cluster.clusterStatus",
                  "StringEquals": "DELETE_IN_PROGRESS",
                  "Next": "Wait for cluster deleting"
                }
              ],
              "Default": "Destroy failed notification (2)"
            },
            "Destroy complete notification": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "ResultPath":None,
              "Next": "Fail"
            },
            "Destroy failed notification (2)": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "ResultPath":None,                
              "Next": "Fail"
            },
            "Success": {
              "Type": "Succeed"
            },
            "Wait for cluster creating": {
              "Type": "Wait",
              "Seconds": 60,
              "Next": "Monitor creating status"
            },
            "Monitor creating status": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": cluster_lambda.function_arn
              },
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 6,
                  "BackoffRate": 2
                }
              ],
              "Next": "Whether Success Created",
              "OutputPath": "$.Payload"
            },
            "Whether Success Created": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.clusterStatus",
                  "StringEquals": "CREATE_IN_PROGRESS",
                  "Next": "Wait for cluster creating"
                },
                {
                  "Variable": "$.clusterStatus",
                  "StringEquals": "CREATE_COMPLETE",
                  "Next": "Create complete notification"
                }
              ],
              "Default": "Publish Fail to create cluster message-2"
            },
            "Publish Fail to create cluster message-2": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "ResultPath":None,                
              "Next": "destroy cluster"
            },
            "Create complete notification": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "ResultPath":None,                
              "Next": "Submit WRF Job"
            },
            "Submit WRF Job": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": run.function_arn
              },
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 6,
                  "BackoffRate": 2
                }
              ],
              "Next": "Wait for timeout"
            },
            "Wait for timeout": {
              "Type": "Wait",
              "SecondsPath": "$.job_timeout",
              "Next": "check stack exist"
            },
            "check stack exist": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": timeout_func.function_arn
              },
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 1,
                  "MaxAttempts": 3,
                  "BackoffRate": 2
                }
              ],
              "Next": "whether job timeout"
            },
            "whether job timeout": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.stack_status",
                  "StringEquals": "exist",
                  "Next": "destroy cluster"
                }
              ],
              "Default": "Success"
            }
          }
        }
        main_sf = sfn.CfnStateMachine(self, "WX_mainStateMachine",
            definition_string=json.dumps(main_sf_def),
            role_arn = sf_role.role_arn )
        self.main_sf=main_sf.attr_arn

        destroy_sf_def={
          "Comment": "state machine to manager lifecycle of cluster",
          "StartAt": "Publish Job Finished Notification",
          "States": {
            "Publish Job Finished Notification": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn":sf_topic.topic_arn
              },
              "ResultPath":None,
              "Next": "destroy cluster"
            },
            "Fail": {
              "Type": "Fail"
            },
            "destroy cluster": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": cluster_lambda.function_arn
              },
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 6,
                  "BackoffRate": 2
                }
              ],
              "Next": "Choice"
            },
            "Choice": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.cluster.clusterStatus",
                  "StringEquals": "DELETE_IN_PROGRESS",
                  "Next": "Wait for cluster deleting"
                }
              ],
              "Default": "Destroy failed notification (1)"
            },
            "Destroy failed notification (1)": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "ResultPath":None,
              "Next": "Fail"
            },
            "Wait for cluster deleting": {
              "Type": "Wait",
              "Seconds": 60,
              "Next": "Monitor deleting status"
            },
            "Monitor deleting status": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "OutputPath": "$.Payload",
              "Parameters": {
                "Payload.$": "$",
                "FunctionName": cluster_lambda.function_arn
              },
              "Retry": [
                {
                  "ErrorEquals": [
                    "Lambda.ServiceException",
                    "Lambda.AWSLambdaException",
                    "Lambda.SdkClientException",
                    "Lambda.TooManyRequestsException"
                  ],
                  "IntervalSeconds": 2,
                  "MaxAttempts": 6,
                  "BackoffRate": 2
                }
              ],
              "Next": "Whether Success Deleted"
            },
            "Whether Success Deleted": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.cluster.clusterStatus",
                  "StringEquals": "DELETE_COMPLETE",
                  "Next": "Destroy complete notification"
                },
                {
                  "Variable": "$.cluster.clusterStatus",
                  "StringEquals": "DELETE_IN_PROGRESS",
                  "Next": "Wait for cluster deleting"
                }
              ],
              "Default": "Destroy failed notification (2)"
            },
            "Destroy complete notification": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "ResultPath":None,
              "Next": "Success"
            },
            "Destroy failed notification (2)": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "ResultPath":None,                
              "Next": "Fail"
            },
            "Success": {
              "Type": "Succeed"
            },
          }
        }
        #-------------------------------------------------
        # Destroy Step Function definition
        #-------------------------------------------------        
        destroy_sf = sfn.CfnStateMachine(self, "WX_destroyStateMachine",
            definition_string=json.dumps(destroy_sf_def),
            role_arn = sf_role.role_arn )
        
        trigger_policy_doc = iam.PolicyDocument(statements=[
            iam.PolicyStatement(
                actions=[
                    "dynamodb:*",
                ],
                resources=[
                    domain_db.table_arn,
                    exec_db.table_arn
                ],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=[
                    "ssm:*",
                ],
                resources=["*"],
                effect=iam.Effect.ALLOW),   
            iam.PolicyStatement(
                actions=["states:*"],
                resources=["*"],
                effect=iam.Effect.ALLOW),
        ])
        trigger_lambda_role = iam.Role(self, "TriggerRole",
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal("lambda.amazonaws.com"),
                    iam.ServicePrincipal("sts.amazonaws.com"),
                ),
                description="CreateAPILambdaRole",
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                    ],
                inline_policies={"cluster_lambda": trigger_policy_doc},
        )
        #-----------------------------------------------------------------------------
        # Create lambda function to subscribe notification of GFS Open data change
        #-----------------------------------------------------------------------------
        trigger_create = λ.Function(self, "start_stepfuction",
                code=λ.Code.from_asset("./lambda/trigger"),
                environment={
                    "SM_ARN": main_sf.attr_arn,
                    "PARA_DB": domain_db.table_name,
                    "EXEC_DB": exec_db.table_name,
                    "KEY_STR": key_str_ssm.parameter_name,
                    "FCST_DAYS": fcst_days_ssm.parameter_name,
                    "AUTO_MODE": auto_mode_ssm.parameter_name,
                    "BUCKET_NAME": bucket_name,
                },
                handler="index.handler",
                log_retention=logs.RetentionDays.ONE_DAY,
                role=trigger_lambda_role,
                runtime=λ.Runtime.PYTHON_3_9,
                timeout=Duration.seconds(60)
            )
        Tags.of(trigger_create).add("Purpose", "Event Driven Weather Forecast", priority=300)
        gfs = sns.Topic.from_topic_arn(self, "NOAAGFS", "arn:aws:sns:us-east-1:123901341784:NewGFSObject")
        trigger_create.add_event_source(λ_events.SnsEventSource(gfs))
        #-----------------------------------------------------------------------------
        # Create lambda function to response for s3 receiving fcst.done file
        #-----------------------------------------------------------------------------
        trigger_destroy = λ.Function(self, "destroy_cluster",
                code=λ.Code.from_asset("./lambda/destroy"),
                environment={
                    "CLUSTER_NAME": cluster_name,
                    #"PCLUSTER_API_URL": purl,
                    "REGION": Aws.REGION,
                    "SM_ARN":destroy_sf.attr_arn,
                    "EXEC_DB":exec_db.table_name,
                    "FTIME": ftime_ssm.parameter_name,
                    "EXEC_ID": exec_id_ssm.parameter_name,
                    "PYTHONPATH":"/opt/python",
                    "EXEC_RECEIVE_TIME": receive_time_ssm.parameter_name
                },
                handler="index.handler",
                layers=[layer],
                log_retention=logs.RetentionDays.ONE_DAY,
                role=trigger_lambda_role,
                runtime=λ.Runtime.PYTHON_3_9,
                timeout=Duration.seconds(60)
            )
        Tags.of(trigger_destroy).add("Purpose", "Event Driven Weather Forecast", priority=300)

        outputs = aws_s3_notifications.LambdaDestination(trigger_destroy)
        bucket = s3.Bucket.from_bucket_name(self, "nwp-bucket", bucket_name)
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED, outputs,
                s3.NotificationKeyFilter(prefix="outputs/", suffix="done"))


        CfnOutput(self, "StateMachineArn", value=main_sf.attr_arn,
            export_name="StateMachineArn")

    @property
    def outputs(self):
        return self.main_sf
