# Event Driven WRF on AWS
![Overview image](./img/arch.png)

A fully automated cloud-native event driven weather forecasting.


## Installation

Install the AWS CDK application and the python library.

```
npm install -g aws-cdk
cd src/
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```
## Deploying

Create a lambda layer that contains `requests` and `pyyaml`.
```
cd layer
pip install -r requirements.txt -t python/
zip -r ../layer.zip python
cd ..
```



Then deploy the CDK stack. Note: you must specify a bucket where you want the
forecast output uploaded to, in the following example I am using
`my-bucket-name`.

```
cdk bootstrap
cdk deploy --parameters BucketName=my-bucket-name
```
add inline policy to the role that contains "ParallelClusterUserRole"
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
               "iam:AttachRolePolicy",
               "iam:DetachRolePolicy"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:iam::<account-id>:role/parallelcluster/*"
        }
    ]
}
```
## Cleanup

To completely tear down all infrastructure when it is not needed.

```
cdk destroy --all
```
