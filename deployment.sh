#!/bin/bash 

cd src/
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cd layer
pip install -r requirements.txt -t python/
cd python
rm -Rf pygrib pygrib.libs matplotlib numpy numpy.libs pyproj netCDF4 netCDF4.libs Pillow.libs fontTools kiwisolver setuptools cftime PIL contourpy botocore pyproj.libs mpl_toolkits
cd ..
zip -r ../layer.zip python
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
cdk_out=$(cdk deploy)
cognito_userpool_id=$(echo "$cdk_output" | grep "WRF.cognitouserpoolid" | awk '{print $2}')
cognito_client_id=$(echo "$cdk_output" | grep "WRF.cognitoclientid" | awk '{print $2}')
echo $cognito_userpool_id
echo $cognito_client_id
sed -i "s/<aws_user_pools_id>/$cognito_userpool_id/g" console/src/aws-export.js
sed -i "s/<aws_user_pools_web_client_id>/$cognito_client_id/g" console/src/aws-export.js
