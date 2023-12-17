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
            cors=[s3.CorsRule(
                allowed_headers=["*"],
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.HEAD, s3.HttpMethods.PUT, s3.HttpMethods.POST, s3.HttpMethods.DELETE],
                allowed_origins=["*"],
                exposed_headers=["x-amz-server-side-encryption", "x-amz-request-id", "x-amz-id-2", "ETag"],
                id="S3CORSRuleId1",
                max_age=3000
            )],
            auto_delete_objects = True,
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        

    @property
    def outputs(self):
        return  self.bucket.bucket_name
