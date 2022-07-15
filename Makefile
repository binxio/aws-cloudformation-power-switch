include Makefile.mk

NAME=aws-cloudformation-power-switch
AWS_REGION=eu-central-1
S3_BUCKET_PREFIX=binxio-public
S3_BUCKET=$(S3_BUCKET_PREFIX)-$(AWS_REGION)

ALL_REGIONS=$(shell printf "import boto3\nprint('\\\n'.join(map(lambda r: r['RegionName'], boto3.client('ec2').describe_regions()['Regions'])))\n" | python | grep -v '^$(AWS_REGION)$$')

help:
	@echo 'make                 - builds a zip file to target/.'
	@echo 'make release         - builds a zip file and deploys it to s3.'
	@echo 'make clean           - the workspace.'
	@echo 'make test            - execute the tests, requires a working AWS connection.'
	@echo 'make deploy	    - lambda to bucket $(S3_BUCKET)'
	@echo 'make deploy-all-regions - lambda to all regions with bucket prefix $(S3_BUCKET_PREFIX)'
	@echo 'make deploy-lambda	- deploys the power switch.'
	@echo 'make delete-lambda	- undeploys the power switch.'
	@echo 'make demo	 	- deploys the demo.'
	@echo 'make delete-demo	 	- undeploys the demo.'

deploy-all-regions: deploy
	@for REGION in $(ALL_REGIONS); do \
		echo "copying to region $$REGION.." ; \
		aws s3 --region $$REGION \
			cp --acl public-read \
			s3://$(S3_BUCKET_PREFIX)-$(AWS_REGION)/lambdas/$(NAME)-$(VERSION).zip \
			s3://$(S3_BUCKET_PREFIX)-$$REGION/lambdas/$(NAME)-$(VERSION).zip; \
		aws s3 --region $$REGION \
			cp  --acl public-read \
			s3://$(S3_BUCKET_PREFIX)-$$REGION/lambdas/$(NAME)-$(VERSION).zip \
			s3://$(S3_BUCKET_PREFIX)-$$REGION/lambdas/$(NAME)-latest.zip; \
	done

do-push: deploy

pre-build:
	pipenv run python setup.py check
	pipenv run python setup.py build

do-build: target/$(NAME)-$(VERSION).zip

upload-dist:
	rm -rf dist/*
	pipenv run python setup.py sdist
	pipenv run twine upload dist/*

target/$(NAME)-$(VERSION).zip: src/*/*.py Dockerfile.lambda
	mkdir -p target
	docker build --build-arg ZIPFILE=$(NAME)-$(VERSION).zip -t $(NAME)-lambda:$(VERSION) -f Dockerfile.lambda . && \
		ID=$$(docker create $(NAME)-lambda:$(VERSION) /bin/true) && \
		docker export $$ID | (cd target && tar -xvf - $(NAME)-$(VERSION).zip) && \
		docker rm -f $$ID && \
		chmod ugo+r target/$(NAME)-$(VERSION).zip

clean:
	rm -rf target
	find . -name \*.pyc | xargs rm 

Pipfile.lock: Pipfile setup.py
	pipenv install -d
	pipenv install

test: Pipfile.lock
	for i in $$PWD/cloudformation/*; do \
		aws cloudformation validate-template --template-body file://$$i > /dev/null || exit 1; \
	done
	PYTHONPATH=$(PWD)/src pipenv run pytest ../tests/test*.py

fmt:
	black $(find src -name *.py) tests/*.py

deploy: target/$(NAME)-$(VERSION).zip
	aws s3 --region $(AWS_REGION) \
		cp --acl \
		public-read target/$(NAME)-$(VERSION).zip \
		s3://$(S3_BUCKET)/lambdas/$(NAME)-$(VERSION).zip
	aws s3 --region $(AWS_REGION) \
		cp --acl public-read \
		s3://$(S3_BUCKET)/lambdas/$(NAME)-$(VERSION).zip \
		s3://$(S3_BUCKET)/lambdas/$(NAME)-latest.zip

deploy-lambda: target/$(NAME)-$(VERSION).zip
	aws cloudformation deploy \
		--capabilities CAPABILITY_IAM \
		--stack-name $(NAME) \
		--template-file ./cloudformation/aws-cloudformation-power-switch.yaml \
		--parameter-override LambdaZipFileName=lambdas/$(NAME)-$(VERSION).zip

delete-lambda:
	aws cloudformation delete-stack --stack-name $(NAME)
	aws cloudformation wait stack-delete-complete  --stack-name $(NAME)


demo: VPC_ID=$(shell  aws ec2  --output text --query 'Vpcs[?IsDefault].VpcId' describe-vpcs)
demo: SUBNET_IDS=$(shell aws ec2 describe-subnets --output text \
					 --query 'sort_by(Subnets, &AvailabilityZone)[?DefaultForAz].SubnetId' \
					 --filters Name=vpc-id,Values=$(VPC_ID) | tr '\t' ',')
demo:
	aws cloudformation deploy \
		--capabilities CAPABILITY_IAM \
		--stack-name $(NAME)-demo \
		--template-file ./cloudformation/demo-stack.yaml \
		--parameter-overrides VPC=$(VPC_ID) Subnets=$(SUBNET_IDS)


delete-demo:
	aws cloudformation delete-stack --stack-name $(NAME)-demo
	aws cloudformation wait stack-delete-complete  --stack-name $(NAME)-demo

deploy-pipeline:
	aws cloudformation deploy \
                --capabilities CAPABILITY_IAM \
                --stack-name $(NAME)-pipeline \
                --template-file ./cloudformation/cicd-pipeline.yaml \
                --parameter-overrides \
                        S3BucketPrefix=$(S3_BUCKET_PREFIX)
