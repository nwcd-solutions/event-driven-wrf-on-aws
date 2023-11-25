from aws_cdk import (
    aws_cloudfront as cloudfront,
    aws_s3 as s3,
    core as cdk
)

class WebApp(cdk.Construct):
    def __init__(self, scope: cdk.Construct, id: str, props: OwnerWebAppProps):
        super().__init__(scope, id)
        smart_product_website_bucket = s3.Bucket(
            self, 'WebsiteBucket',
            website_error_document='index.html',
            website_index_document='index.html'
        )
        console_origin_access_identity = cloudfront.OriginAccessIdentity(
            self, 'ConsoleOriginAccessIdentity',
            comment=f'access-identity-{smart_product_website_bucket.bucket_name}'
        )
        console_distribution = cloudfront.CloudFrontWebDistribution(
            self, 'ConsoleDistribution',
            comment='Website distribution for smart product console',
            origin_configs=[{
                's3_origin_source': {
                    's3_bucket_source': smart_product_website_bucket,
                    'origin_access_identity': console_origin_access_identity
                },
                'behaviors': [{
                    'is_default_behavior': True,
                    'allowed_methods': cloudfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
                    'cached_methods': cloudfront.CloudFrontAllowedCachedMethods.GET_HEAD_OPTIONS,
                    'default_ttl': cdk.Duration.seconds(0),
                    'max_ttl': cdk.Duration.seconds(0),
                    'min_ttl': cdk.Duration.seconds(0)
                }]
            }],
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            error_configurations=[
                {
                    'error_code': 404,
                    'response_code': 200,
                    'response_page_path': '/index.html'
                },
                {
                    'error_code': 403,
                    'response_code': 200,
                    'response_page_path': '/index.html'
                }
            ],
            enable_ipv6=True,
            http_version=cloudfront.HttpVersion.HTTP2,
            default_root_object='index.html',
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL
        )

        smart_product_website_bucket.add_to_resource_policy(iam.PolicyStatement(
            actions=['s3:GetObject'],
            effect=iam.Effect.ALLOW,
            resources=[f'{smart_product_website_bucket.bucket_arn}/*'],
            principals=[iam.CanonicalUserPrincipal(console_origin_access_identity.cloud_front_origin_access_identity_s3_canonical_user_id)]
        ))

        # CFN_NAG Annotations
        website_bucket_resource = smart_product_website_bucket.node.find_child('Resource')
        website_bucket_resource.cfn_options.metadata = {
            'cfn_nag': {
                'rules_to_suppress': [
                    {
                        'id': 'W35',
                        'reason': 'SmartProductWebsiteBucket validated and does not require access logging to be configured.'
                    },
                    {
                        'id': 'W41',
                        'reason': 'SmartProductWebsiteBucket does not contain sensitive data so encryption is not needed.'
                    }
                ]
            }
        }

        website_distribution_resource = console_distribution.node.find_child('CFDistribution')
        website_distribution_resource.cfn_options.metadata = {
            'cfn_nag': {
                'rules_to_suppress': [{
                    'id': 'W10',
                    'reason': 'ConsoleDistribution validated and does not require access logging to be configured.'
                }]
            }
        }
