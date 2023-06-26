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
        forecast_tmpl = Fn.import_value("ForecastTemplate")

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
                    "FORECAST_TMPL": forecast_tmpl,
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

        create_cluster = tasks.LambdaInvoke(
            self, "LAMBDA:Command Parallelcluster",
            lambda_function=cluster_lambda,
            output_path="$.Payload",
            payload=sfn.TaskInput.from_object({
                "action": "create",
                "type": "od",              
            })
        )
        destroy_cluster = tasks.LambdaInvoke(
            self, "LAMBDA:Command Parallelcluster",
            lambda_function=cluster_lambda,
            output_path="$.Payload",
        )
        check_cluster_status = tasks.LambdaInvoke(
            self, "LAMBDA:Command Parallelcluster",
            lambda_function=cluster_lambda,
            output_path="$.Payload",
        )
        wait_x = sfn.Wait(self, "Wait X Seconds",
            time= 60
        )
        process=sfn.Pass(self,"submit jobs")
        create_failed = sfn.Fail(self,"Cluster create failed")
        
        definition=create_cluster.next(sfn.Choice(self,'Whether cluster could be created?')
                                       .when(sfn.Condition.string_notequals('$.clusterStatus','CREATE_IN_PROGRESS'),wait_x.next(check_cluster_status)
                                           .next(sfn.Choice(self,'Whether cluster created?')
                  .when(sfn.Condition.string_equals('$.clusterStatus','CREATE_IN_PROGRESS'),wait_x.next(check_cluster_status))
                  .when(sfn.Condition.string_equals('$.clusterStatus','CREATE_COMPLETE'),send_create_success_notification.next(process))
                  .otherwise(send_create_failed_notification)))
                                       .otherwise(create_failed))\
          
                  
        
        
