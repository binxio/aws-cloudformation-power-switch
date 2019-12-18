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
aws-cfn-power-switch --dry-run --stack-name-prefix dev shutdown
```
This will show you which EC2, RDS and AutoScaling instances will be shutdown. For Auto Scaling groups, the 
desired number of instances is set to 0. If the minimum is greater than 0, it will change the minimum setting too.

## startup`
to startup all instances managed by a CloudFormation stacks starting with the name `dev`, type:
```sh
aws-cfn-power-switch --dry-run --stack-name-prefix dev startup
```
This will show you which EC2, RDS and AutoScaling instances will be started. The AutoScaling desired number of 
instances will be set the maximum desired instances.

## deploy the power switch
To deploy the power switch as an AWS Lambda, type:

```sh
git clone https://github.com/binxio/aws-cloudwatch-log-minder.git
cd aws-cloudwatch-log-minder
aws cloudformation deploy \
	--capabilities CAPABILITY_IAM \
	--stack-name aws-cloudformation-power-switch \
	--template-file ./cloudformation/aws-cloudformation-power-switch.yaml \
    --override-parameters \
        StackNamePrefix=dev \
	    "Startup=cron(30 7 ? * MON-FRI *)" \
        "Shutdown=cron(30 23 ? * MON-FRI *)"
```
This will shutdown down all EC2, RDS and Auto Scaling instances managed by CloudFormation stacks starting with the
name `dev` at 23:30 and start them backup at 7:30 in the morning.


## verbose

```sh
export LOG_LEVEL=INFO
cwlog-minder ...
```
