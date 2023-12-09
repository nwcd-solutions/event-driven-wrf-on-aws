/* eslint-disable */
// WARNING: DO NOT EDIT. This file is automatically generated by AWS Amplify. It will be overwritten.

const config = {
    "aws_project_region": "<aws_region>",
    "aws_cognito_region": "<aws_region>",
    "aws_user_pools_id": "<aws_user_pools_id>",
    "aws_user_pools_web_client_id": "<aws_user_pools_web_client_id>",
    "oauth": {
        "domain": "<cognito_domain>"
    },
    "aws_cognito_username_attributes": [
        "EMAIL"
    ],
    "aws_cognito_social_providers": [],
    "aws_cognito_signup_attributes": [
        "EMAIL"
    ],
    "aws_cognito_mfa_configuration": "OFF",
    "aws_cognito_mfa_types": [],
    "aws_cognito_password_protection_settings": {
        "passwordPolicyMinLength": 8,
        "passwordPolicyCharacters": []
    },
    "aws_cognito_verification_mechanisms": [
        "EMAIL"
    ],
    "aws_cloud_logic_custom": [
        {
            "name": "<api_gateway_name>",
            "endpoint": "<api_gateway_endpoint>",
            "region": "<aws_region>"
        }
    ],
    "geo": {
        "amazon_location_service": {
          "region": "<aws_region>",
          "maps": {
            "items": {
              <map_name>: {
                "style": "VectorEsriStreets"
              }
            },
            "default": "<map_name>",
            "apikey":""
          }
        }
    }

};


export default config;
