import boto3
import sys
from typing import List, NamedTuple
import logging
import sys


class PowerSwitch(object):
    def __init__(self):
        self.stack_name_prefix = None
        self.verbose = False
        self.dry_run = True
        self.session = None
        self._stack_resources = []
        self.resource_type = None

    def select_instances(self) -> List:
        if not self.resource_type:
            raise Exception("no CloudFormation resource type specified")
        return self.stack_resources

    def instance_needs_startup(self, instance) -> bool:
        raise Exception("not implemented")

    def instance_needs_shutdown(self, instance) -> bool:
        raise Exception("not implemented")

    def shutdown(self, instance):
        raise Exception("not implemented")

    def startup(self, instance):
        raise Exception("not implemented")

    def check_precondition(self):
        if not self.stack_name_prefix:
            logging.error("no stack name prefix specified")
            sys.exit(1)

    def on(self):
        self.check_precondition()
        for instance in filter(
            lambda i: self.instance_needs_startup(i), self.select_instances()
        ):
            self.startup(instance)

    def off(self):
        self.check_precondition()
        for instance in filter(
            lambda i: self.instance_needs_shutdown(i), self.select_instances()
        ):
            self.shutdown(instance)

    def set_session(self, profile, region):
        kwargs = {}
        if region:
            kwargs["region_name"] = region
        if profile:
            kwargs["profile_name"] = profile

        self.session = boto3.Session(**kwargs)

    def get_stack_resources(self):
        if self.session in stack_resources_per_session:
            self._stack_resources = stack_resources_per_session[self.session]
            return

        self._stack_resources = []
        logging.info(
            "retrieving all CloudFormation stacks with prefix %s",
            self.stack_name_prefix,
        )
        cfn = self.session.client("cloudformation")
        for response in cfn.get_paginator("describe_stacks").paginate():
            for stack_summary in response["Stacks"]:
                name = stack_summary["StackName"]
                if name.startswith(self.stack_name_prefix):
                    if self.verbose:
                        logging.info("loading all resources from stack %s", name)
                    for response in cfn.get_paginator("list_stack_resources").paginate(
                        StackName=name
                    ):
                        for r in response["StackResourceSummaries"]:
                            r["StackName"] = name
                        self._stack_resources.extend(response["StackResourceSummaries"])

        stack_resources_per_session[self.session] = self._stack_resources

    @property
    def stack_resources(self) -> List[dict]:
        if not self._stack_resources:
            self.get_stack_resources()

        return sorted(
            filter(
                lambda r: not self.resource_type
                or r.get("ResourceType") == self.resource_type,
                self._stack_resources,
            ),
            key=lambda r: r["StackName"] + "-" + r["LogicalResourceId"],
        )

    def get_stack_resource_by_physical_id(self, physical_resource_id: str):
        next(
            filter(
                lambda r: r["PhysicalResourceId"] == physical_resource_id,
                self.stack_resources,
            ),
            None,
        )


stack_resources_per_session = {}
