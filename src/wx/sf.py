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

class stepfunction (NestedStack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        vpc = kwargs["vpc"]
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
                    "FORECAST_TMPL": forecast_tmpl,
                    "S3_URL_POST_INSTALL_HEADNODE": f"{post_head_amd64.s3_object_url}",
                    "SG": sg_rds.security_group_id,
                    "SNS_TOPIC": sns_topic,
                    "SM_ARN": sm.state_machine_arn,
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
        destroy_sf_def= 
        destroy_sf = sfn.StateMachine(self, "WX_destroyStateMachine",
            definition_string=json.dumps(destroy_sf_def),
            timeout=Duration.minutes(65))

        create_sf_def= {
            "Comment": "state machine to create cluster",
            "StartAt": "destroy cluster",
            "States": {
                "destroy cluster": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "OutputPath": "$.Payload",
                    "Parameters": {
                        "Payload.$": "$",
                        "FunctionName": "arn:aws:lambda:us-east-2:880755836258:function:WX-clusterNestedStackclus-lambdafuncdestroy811B2A7-3cxqzYGHhxQz:$LATEST"
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
      "Next": "Whether cluster could be deleted"
    },
    "Whether cluster could be deleted": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.cluster.clusterStatus",
          "StringEquals": "DELETE_IN_PROGRESS",
          "Next": "Wait for cluster deleting"
        }
      ],
      "Default": "Fail"
    },
    "Wait for cluster deleting": {
      "Type": "Wait",
      "Seconds": 60,
      "Next": "Monitor deleting status"
    },
    "Monitor deleting status": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "Payload.$": "$",
        "FunctionName": "arn:aws:lambda:us-east-2:880755836258:function:WX-clusterNestedStackclus-lambdafuncdestroy811B2A7-3cxqzYGHhxQz:$LATEST"
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
      "Next": "Whether Success Deleted",
      "OutputPath": "$.Payload"
    },
    "Whether Success Deleted": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.cluster.clusterStatus",
          "StringEquals": "DELETE_COMPLETE",
          "Next": "Success"
        },
        {
          "Variable": "$.cluster.clusterStatus",
          "StringEquals": "DELETE_IN_PROGRESS",
          "Next": "Wait for cluster deleting"
        }
      ],
      "Default": "Fail"
    },
    "Fail": {
      "Type": "Fail"
    },
    "Success": {
      "Type": "Succeed"
    }
  }
}
        
        create_sf = sfn.StateMachine(self, "WX_createStateMachine",
            definition_string=json.dumps(create_sf_def),
            timeout=Duration.minutes(65))
        
        main_sf_def = {
            "Comment": "main state machine workflow",
            "StartAt": "Create single OD Cluster",
            "States": {
                "Create single OD Cluster": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::states:startExecution.sync:2",
                    "Parameters": {
                        "StateMachineArn": "arn:aws:states:us-east-2:880755836258:stateMachine:ClusterCreate",
                        "Input": {
                            "action": "create",
                            "type": "od",
                            "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id"
                        }
                    },
                    "OutputPath": "$.Output",
                    "Next": "Choice (1)"
                },
                "Choice (1)": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.clusterStatus",
                            "StringEquals": "CREATE_COMPLETE",
                            "Next": "Publish completed message (1)"
                        }
                    ],
                    "Default": "Publish Fail to create cluster message (1)"
                },
                "Publish Fail to create cluster message (1)": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sns:publish",
                    "Parameters": {
                        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
                        "Message": {
                            "message": "Clusters failed to be created complete, will start to destroy the cf",
                            "detail information": {
                                "OD cluster": {
                                    "cluster name": "$[0].clusterName"
                                },
                                "Spot cluster": {
                                    "cluster name": "$[1].clusterName"
                                }
                            }
                        }
                    },
                    "ResultPath": null,
                    "Next": "Destroy single Cluster"
                },
                "Publish completed message (1)": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sns:publish",
                    "Parameters": {
                        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
                        "Message": {
                            "message": "Clusters have been created successfully, will start to run forecast jobs",
                            "detail information": {
                                "OD cluster": {
                                    "cluster name": "$[0].clusterName",
                                    "head node": "$[0].headNode"
                                },
                                "Spot cluster": {
                                    "cluster name": "$[1].clusterName",
                                    "head node": "$[1].headNode"
                                }
                             }
                        }
                    },
                    "ResultPath": null,
                    "Next": "Pass (1)"
                },
                "Pass (1)": {
                    "Type": "Pass",
                    "Next": "Destroy single Cluster"
                },
                "Destroy single Cluster": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::states:startExecution.sync:2",
                    "Parameters": {
                        "StateMachineArn": "arn:aws:states:us-east-2:880755836258:stateMachine:ClusterDestroy",
                        "Input": {
                            "action": "destroy",
                            "clusterName.$": "$.clusterName",
                            "region.$": "$.region",
                            "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id"
                        }
                    },
                    "Next": "Choice (2)"
                },
                "Choice (2)": {
                    "Type": "Choice",
                    "Choices": [
                      {
                        "Variable": "$.Output.cluster.clusterStatus",
                        "StringEquals": "DELETE_COMPLETE",
                        "Next": "Destroy failed notification (1)"
                      }
                    ],
                    "Default": "Destroy complete notification (1)"
                },
                "Destroy complete notification (1)": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sns:publish",
                    "Parameters": {
                        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
                        "Message": {
                            "message": "Clusters has been deleted"
                        }
                    },
                    "Next": "Success",
                    "ResultPath": null
                },
                "Destroy failed notification (1)": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sns:publish",
                    "Parameters": {
                        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
                        "Message": {
                            "message": "Clusters failed to be deleted"
                        }
                    },
                    "Next": "Fail",
                    "ResultPath": null
                },
                "Fail": {
                    "Type": "Fail"
                },
                "Success": {
                    "Type": "Succeed"
                }
            }
        }
        main_sf = sfn.StateMachine(self, "WX_mainStateMachine",
            definition_string=json.dumps(main_sf_def),
            timeout=Duration.minutes(65))
