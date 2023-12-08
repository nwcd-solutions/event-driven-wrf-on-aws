from aws_cdk import (
    aws_s3 as s3,
    CfnOutput, NestedStack, Tags
)
import aws_cdk as core
from constructs import Construct
import random
import string

def generate_bucket_name():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(10))

class Bucket(NestedStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        self.bucket = s3.Bucket(
            self, 'NWPBucket',
            bucket_name='nwp-',
            removal_policy=core.RemovalPolicy.DESTROY,
        )

    @property
    def outputs(self):
        return  self.bucket.bucket_name
