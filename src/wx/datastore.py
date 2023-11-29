# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_ssm as ssm,
    aws_secretsmanager as secretsmanager,
    App, CfnOutput, Fn, NestedStack, RemovalPolicy
)
import aws_cdk as core
from constructs import Construct

class DataStore(NestedStack):
    def __init__(self, scope:Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        #-------------------------------------------------
        # Create SSM parameter store to store parameters
        #-------------------------------------------------
        self.job_timeout_ssm = ssm.StringParameter(
            self, "job_timeout_ssm",
            parameter_name="/event-driven-wrf/job_timeout",
            string_value="1800"
        )

        self.fcst_days_ssm = ssm.StringParameter(
            self, "fcst_days_ssm",
            parameter_name="/event-driven-wrf/fcst_days",
            string_value="2"
        )
        self.key_str_ssm = ssm.StringParameter(
            self, "key_str_ssm",
            parameter_name="/event-driven-wrf/key_string",
            string_value=r"gfs.t(?P=h)z.pgrb2.0p50.f096"
        )
        self.auto_mode_ssm = ssm.StringParameter(
            self, "auto_mode_ssm",
            parameter_name="/event-driven-wrf/auto_mode",
            string_value="False"
        )
        self.ftime_ssm = ssm.StringParameter(
            self, "ftime_ssm",
            parameter_name="/event-driven-wrf/ftime",
            string_value="False"
        )
        self.exec_id_ssm = ssm.StringParameter(
            self, "exec_id_ssm",
            parameter_name="/event-driven-wrf/id",
            string_value="False"
        )
        #----------------------------------------------------------------------------------------------
        # Create a DynamoDB table to store parameters of Domain and Step function execution record
        #----------------------------------------------------------------------------------------------
        self.para_db = dynamodb.Table(
            self, "Parameters_Table",
            partition_key=dynamodb.Attribute(
                name="name",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=core.RemovalPolicy.DESTROY,

        )
        
        self.exec_db = dynamodb.Table(
            self, "execution_Table",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="ftime",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        


    @property
    def outputs(self):
        return self.exec_db
