from aws_cdk import (
    aws_cloudfront as cloudfront,
    aws_s3 as s3,
    aws_location as location,
    aws_codecommit as codecommit,
    aws_amplify as amplify,
    CfnOutput, NestedStack, Tags
)
from constructs import Construct

class WebApp(NestedStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)


        amplify_react_sample_repo = codecommit.Repository(
            self, 'AmplifyReactTestRepo',
            repository_name='nwp-solution-repo',
            description='CodeCommit repository that will be used as the source repository for the sample react app and the cdk app',
        )
        # Part 2 - Creation of the Amplify Application
        amplify_app = amplify.App(
            self, 'nwp-web-app',
            repository=amplify_react_sample_repo,
        )
        master_branch = amplify_app.add_branch('master')

        map = location.CfnMap(self, "DomainMap",
            configuration=location.CfnMap.MapConfigurationProperty(
                style="VectorEsriTopographic"
            ),
            map_name="DomainMap",
        )

