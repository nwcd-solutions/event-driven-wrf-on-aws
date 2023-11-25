# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Aws, CfnOutput, CfnParameter, Duration, Fn, NestedStack, Stack, Tags
)

from constructs import Construct
from wx.network import Vpc
from wx.pclusterapi import ParallelClusterApi
from wx.slurmdb import SlurmDb
from wx.statemachines import StepFunction
from wx.apigateway import ApiGateway
from wx.datastore import DataStore

class Root(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_name = CfnParameter(self, "BucketName", type="String",
            description="The name of the Amazon S3 bucket where the forecast files will be stored.")

        slurm_acct= CfnParameter(self, "SlurmAcct",type="String", default="false",description="whether slurm account is neccessary")

        vpc = Vpc(self, "vpc")
        datastore = DataStore(self, "datastore")
        pcluster_api = ParallelClusterApi(self, "parallel-cluster-api")
        if (slurm_acct == "true") :
            slurmdb = SlurmDb(self, "slurmdbd", vpc=vpc.outputs)
            slurmdb.add_dependency(vpc)

        sf = StepFunction(self, "workflow", vpc=vpc.outputs, bucket=bucket_name.value_as_string, datastore=datastore)
        sf.add_dependency(pcluster_api)  
        if (slurm_acct == "true") :
            sf.add_dependency(slurmdb)
        sf.add_dependency(vpc)
       
        api = ApiGateway(self,"api",para_db=datastore.para_db,bucket=bucket_name.value_as_string)
        api.add_dependency(sf)


    @property
    def outputs(self):
        return self
