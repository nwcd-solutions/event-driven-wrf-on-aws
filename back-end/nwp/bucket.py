from aws_cdk import (
    aws_s3 as s3,
    CfnOutput, NestedStack, Tags
)
import aws_cdk as core
from constructs import Construct

class Bucket(NestedStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)
        bucket_name = kwargs["bucket_name"]
        self.bucket = s3.Bucket(
            self, 'NWPBucket',
            bucket_name = bucket_name,
            autoDeleteObjects = True,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

    @property
    def outputs(self):
        return  self.bucket.bucket_name
