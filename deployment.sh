#!/bin/bash 

cd back-end/
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cd layer
pip install -r requirements.txt -t python/
cd python
rm -Rf pygrib pygrib.libs matplotlib numpy numpy.libs pyproj netCDF4 netCDF4.libs Pillow.libs fontTools kiwisolver setuptools cftime PIL contourpy botocore pyproj.libs mpl_toolkits
cd ..
zip -r ../layer.zip python
rm -rf python
cd ..

while true; do
    read -p "Do you want to use slurm accounting? (yes/no): " slurm_acct
    case $slurm_acct in
        [Yy]*) slurm_acct=true; break;;
        [Nn]*|"") slurm_acct=false; break;;
        *) echo "Please answer yes or no.";;
    esac
done

#read -p "Please enter the admin username" username

cdk bootstrap
cdk_out=$(cdk deploy --outputs-file outputs.json)
cognito_userpool_id=$(jq '.WRF.cognitouserpoolid' outputs.json)
cognito_client_id=$(jq '.WRF.cognitoclientid' outputs.json)
#cognito_domain=$(jq '.WRF.cognitodomain' outputs.json)
apigw_endpoint=$(jq '.WRF.apigwendpoint' outputs.json)
apigw_name=$(jq '.WRF.apigwname' outputs.json)
location_map_name=$(jq '.WRF.locationmapname' outputs.json)


cd ../front-end
cp aws-export.js console/src/
sed -i "s|<aws_user_pools_id>|$cognito_userpool_id|g" console/src/aws-export.js
sed -i "s|<aws_user_pools_web_client_id>|$cognito_client_id|g" console/src/aws-export.js
#sed -i "s|<cognito_domain>|$cognito_domain|g" console/src/aws-export.js
sed -i "s|<api_gateway_endpoint>|$apigw_endpoint|g" console/src/aws-export.js
sed -i "s|<api_gateway_name>|$apigw_name|g" console/src/aws-export.js
sed -i "s|<map_name>|$location_map_name|g" console/src/aws-export.js
sed -i "s|<aws_region>|us-east-2|g" console/src/aws-export.js

