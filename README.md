# Event Driven WRF on AWS
![Overview image](./img/arch.png)

A fully automated cloud-native event driven weather forecasting.

For HPC6a instance only available in us-east-2, you should deploy the solution in this region.

## Prerequisites
1. Create an EC2 Key pair with name us-east-2.
2. Create Amazon Location API Keys and copy API Key value.
* Open the AWS Management Console and navigate to the Amazon Location Service console.
* In the left navigation pane, choose API keys.
* Choose Create API key.
* In the Create API key dialog box, enter a name for your API key in the Name field.
* Optionally, enter a description for your API key in the Description field.
* Under Referers, specify the domains where the API key can be used. This is an optional step.
* Choose Create API key.
* Once the API key is created, you can view the API key value by clicking on the Show button next to the key.Copy the value.



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
default forecast domains and default forecast days are both 2, if you need change the setting, please deploy the CDK stack with optional parameters. the number of domains need to be consistent with contents of S3 bucket' inputs folder.
```
cdk deploy --parameters BucketName=my-bucket-name --parameters DomainNum=1 --parameters ForecastDays=1 
```
## Cleanup

To completely tear down all infrastructure when it is not needed.

```
cdk destroy --all
```
