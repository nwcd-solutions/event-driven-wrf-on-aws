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
    Aws, CfnOutput, Duration, Fn, NestedStack, Tags
)
from constructs import Construct
import json

class stepfunction (NestedStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)
        bucket_name = kwargs["bucket"]
        vpc = kwargs["vpc"]
        cluster_name = "wx-pcluster001"
        purl = Fn.import_value("ParallelClusterApiInvokeUrl")
        hostname = Fn.select(2, Fn.split("/", Fn.select(0, Fn.split('.', purl))))
        parn = f"arn:aws:execute-api:{Aws.REGION}::{hostname}/*/*/*"
        post_head_amd64 = assets.Asset(self, "PostComputeFileAsset",
                path="scripts/post_install_amd64.sh")
        jwt_key = Fn.import_value("JWTKey")
        sns_topic = Fn.import_value("ForecastSnsArn")
        
                
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
        policy_doc = iam.PolicyDocument(statements=[
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
        ])
        lambda_role = iam.Role(self, "Role",
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal("lambda.amazonaws.com"),
                    iam.ServicePrincipal("sts.amazonaws.com"),
                ),
                description="CreateAPILambdaRole",
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                    ],
                inline_policies={"cluster_lambda": policy_doc},
        )

        subnet = vpc.public_subnets[1].subnet_id
        for net in vpc.public_subnets:
            if net.availability_zone == "us-east-2b":
                subnet = net

        layer = λ.LayerVersion(self, "lambda_layer",
                compatible_runtimes=[λ.Runtime.PYTHON_3_9],
                code=λ.Code.from_asset("./layer.zip"),
                layer_version_name="wx_layer",
                description="WX Lambda Layer",
            )

        cluster_lambda = λ.Function(self, "lambda_func_cluster",
                code=λ.Code.from_asset("./lambda"),
                environment={
                    "BUCKET_NAME": bucket_name,
                    "CLUSTER_NAME": cluster_name,
                    "JWTKEY": jwt_key,
                    "PCLUSTER_API_URL": purl,
                    "REGION": Aws.REGION,
                    "S3_URL_POST_INSTALL_HEADNODE": f"{post_head_amd64.s3_object_url}",
                    "SG": sg_rds.security_group_id,
                    "SNS_TOPIC": sns_topic,
                    "SUBNETID": subnet,
                },
                handler="cluster.main",
                layers=[layer],
                log_retention=logs.RetentionDays.ONE_DAY,
                role=lambda_role,
                runtime=λ.Runtime.PYTHON_3_9,
                timeout=Duration.seconds(60)
            )
        Tags.of(cluster_lambda).add("Purpose", "Event Driven Weather Forecast", priority=300)    

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
                resources=[cluster_lambda.function_arn],
                effect=iam.Effect.ALLOW),
            iam.PolicyStatement(
                actions=["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"],
                resources=["*"],
                effect=iam.Effect.ALLOW),            
        ])    
        main_sf_role = iam.Role(self, "Main SF Role",
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
        sf_def={
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
              "Next": "Fail"
            },
            "Fail": {
              "Type": "Fail"
            },
            "Pass": {
              "Type": "Pass",
              "Next": "destroy cluster"
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
              "Next": "Success"
            },
            "Destroy failed notification (2)": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
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
              "Next": "destroy cluster"
            },
            "Create complete notification": {
              "Type": "Task",
              "Resource": "arn:aws:states:::sns:publish",
              "Parameters": {
                "Message.$": "$",
                "TopicArn": sf_topic.topic_arn
              },
              "Next": "Pass"
            }
          }
        }
        main_sf = sfn.CfnStateMachine(self, "WX_mainStateMachine",
            definition_string=json.dumps(sf_def),
            role_arn = main_sf_role.role_arn )
        self.main_sf=main_sf.attr_arn
        CfnOutput(self, "StateMachineArn", value=main_sf.attr_arn,
            export_name="StateMachineArn")

    @property
    def outputs(self):
        return self.main_sf
