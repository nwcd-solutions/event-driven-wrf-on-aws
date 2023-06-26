# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Aws, CfnOutput, CfnParameter, Duration, Fn, NestedStack, Stack, Tags
)
from constructs import Construct

from wx.bucket import S3
from wx.gfs_trigger import Trigger
from wx.forecast import Forecast
from wx.network import Vpc
from wx.pclusterapi import ParallelClusterApi
from wx.slurmdb import SlurmDb
from wx.statemachines import stepfunction

class Root(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_name = CfnParameter(self, "BucketName", type="String",
            description="The name of the Amazon S3 bucket where the forecast files will be stored.")

        vpc = Vpc(self, "vpc")

        forecast = Forecast(self, "forecast", vpc=vpc.outputs, bucket=bucket_name.value_as_string)
        pcluster_api = ParallelClusterApi(self, "parallel-cluster-api")

        slurmdb = SlurmDb(self, "slurmdbd", vpc=vpc.outputs)
        slurmdb.add_dependency(vpc)

        #s3 = S3(self, "s3", bucket=bucket_name.value_as_string)
        sf = stepfunction(self, "cluster", vpc=vpc.outputs, bucket=bucket_name.value_as_string)
        sf.add_dependency(forecast)
        sf.add_dependency(pcluster_api)
        sf.add_dependency(s3)
        sf.add_dependency(slurmdb)
        sf.add_dependency(vpc)
        trigger = Trigger(self, "trigger", sf=sf.outputs)
        #trigger = Trigger(self, "trigger", sf=sf.outputs, bucket=bucket_name.value_as_string)
        #cluster.add_dependency(forecast)
        #cluster.add_dependency(pcluster_api)
        #cluster.add_dependency(s3)
        #cluster.add_dependency(slurmdb)
        #cluster.add_dependency(vpc)
        #cluster.add_dependency(sf)
        

    @property
    def outputs(self):
        return self
