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

```
git clone https://github.com/nwcd-solutions/event-driven-wrf-on-aws.git
cd event-driven-wrf-on-aws
bash deployment.sh
```

## Cleanup

To completely tear down all infrastructure when it is not needed.

```
bash destroy.sh
```
