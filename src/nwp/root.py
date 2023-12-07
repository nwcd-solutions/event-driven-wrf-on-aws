# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Aws, CfnOutput, CfnParameter, Duration, Fn, NestedStack, Stack, Tags, aws_lambda as λ,
)
from constructs import Construct
from nwp.network import Vpc
from nwp.pclusterapi import ParallelClusterApi
from nwp.slurmdb import SlurmDb
from nwp.statemachines import StepFunction
from npw.apigateway import ApiGateway
from npw.datastore import DataStore
from npw.bucket import Bucket
class Root(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        slurm_acct= CfnParameter(self, "SlurmAcct",type="String", default="false",description="whether slurm account is neccessary")
        
        bucket = Bucket(self,"bucket")     
        vpc = Vpc(self, "vpc")
        datastore = DataStore(self, "datastore")
        pcluster_api = ParallelClusterApi(self, "parallel-cluster-api")
        if (slurm_acct == "true") :
            slurmdb = SlurmDb(self, "slurmdbd", vpc=vpc.outputs)
            slurmdb.add_dependency(vpc)
            
        layer = λ.LayerVersion(self, "lambda_layer",
                compatible_runtimes=[λ.Runtime.PYTHON_3_9],
                code=λ.Code.from_asset("./layer.zip"),
                layer_version_name="wx_layer",
                description="WX Lambda Layer",
            )
        
        sf = StepFunction(self, "workflow", vpc=vpc.outputs, bucket=bucket.outputs.value_as_string, datastore=datastore,layer=layer)
        sf.add_dependency(pcluster_api)  
        if (slurm_acct == "true") :
            sf.add_dependency(slurmdb)
        sf.add_dependency(vpc)
       
        api = ApiGateway(self,"api",datastore=datastore ,bucket=bucket.outputs.value_as_string,layer=layer)
        api.add_dependency(sf)


    @property
    def outputs(self):
        return self
