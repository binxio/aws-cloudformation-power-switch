# AWS CloudFormation power switch
AWS CloudFormation power switch allows you to shutdown and startup all EC2, RDS and AutoScaling instances managed
by one or more CloudFormation stacks.

## install the power switch
to install the power switch, type:

```sh
pip install aws-cloudformation-power-switch
```

## shutdown
to shutdown all instances managed by CloudFormation stacks starting with the name `dev`, type:
```sh
cfn-power-switch --dry-run --stack-name-prefix dev on
```
This will show you which EC2, RDS and AutoScaling instances will be shutdown. For Auto Scaling groups, the 
desired number of instances is set to 0. If the minimum is greater than 0, it will change the minimum setting too.

## startup`
to startup all instances managed by a CloudFormation stacks starting with the name `dev`, type:
```sh
cfn-power-switch --dry-run --stack-name-prefix dev off
```
This will show you which EC2, RDS and AutoScaling instances will be started. The AutoScaling desired number of 
instances will be set the maximum desired instances. Remove the `--dry-run` and it will be activated.


## deploy the power switch
To deploy the power switch as an AWS Lambda, type:

```sh
git clone https://github.com/binxio/aws-cloudformation-power-switch.git
cd aws-cloudformation-power-switch.git
aws cloudformation deploy \
	--capabilities CAPABILITY_IAM \
	--stack-name aws-cloudformation-power-switch \
	--template-file ./cloudformation/aws-cloudformation-power-switch.yaml
```

## Demo
install the demonstration, type:
```
aws cloudformation deploy \
	--capabilities CAPABILITY_IAM \
	--stack-name aws-cloudformation-power-switch-demo \
	--template-file ./cloudformation/demo-stack.yaml
```
This deploy an ec2 instance, an autoscaling group and a RDS MySQL database instance, It will shutdown down all EC2, RDS and Auto Scaling instances managed by CloudFormation stacks starting with the name `dev` at 23:30 and start them backup at 7:30 in the morning.

To manual stop all the instance, type:
```
cfn-power-switch --verbose --stack-name-prefix aws-cloudformation-power-switch off
```
It will take few minutes before everything is shutdown and you can restart the stack.

to start everything back up, type:
```
cfn-power-switch --verbose --stack-name-prefix aws-cloudformation-power-switch off
```
It will take few minutes before everything is running again.

Do not forget to delete the stack:
```
aws cloudformation delete-stack --stack-name aws-cloudformation-power-switch-demo
```

## caveats
The RDS clusters are not detected as CloudFormation does not place `aws:cloudformation:` tags on the cluster resource.  Will fix this
by querying the stack resources instead. A PR is welcome!
