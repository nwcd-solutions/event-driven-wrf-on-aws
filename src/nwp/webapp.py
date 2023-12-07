from aws_cdk import (
    aws_cloudfront as cloudfront,
    aws_s3 as s3,
    core as cdk
)

class WebApp(cdk.Construct):
    def __init__(self, scope: cdk.Construct, id: str, props: OwnerWebAppProps):
        super().__init__(scope, id)

        amplify_react_sample_repo = codecommit.Repository(
            self, 'AmplifyReactTestRepo',
            repository_name='nwp-solution-repo',
            description='CodeCommit repository that will be used as the source repository for the sample react app and the cdk app',
        )
        # Part 2 - Creation of the Amplify Application
        amplify_app = amplify.App(
            self, 'nwp-web-app',
            source_code_provider=amplify.CodeCommitSourceCodeProvider(
                repository=amplify_react_sample_repo,
            ),
        )
        master_branch = amplify_app.add_branch('master')



