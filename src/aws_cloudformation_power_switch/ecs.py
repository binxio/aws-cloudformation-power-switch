import logging
import re
from typing import Iterator

from aws_cloudformation_power_switch.power_switch import PowerSwitch
from aws_cloudformation_power_switch.tag import logical_id, stack_name


class ECSPowerSwitch(PowerSwitch):
    def __init__(self):
        super(ECSPowerSwitch, self).__init__()

    def startup(self, instance: dict):
        desired_count = self.find_last_steady_state_count(instance)
        logging.info(
            "starting ecs service %s with desired count = %d",
            self.instance_id(instance),
            desired_count,
        )
        if not self.dry_run:
            self.ecs.update_service(
                service=self.instance_id(instance),
                cluster=self.cluster_id(instance),
                desiredCount=desired_count,
            )

    def desired_count(self, instance) -> int:
        return instance.get("desiredCount")

    def instance_id(self, instance) -> str:
        return instance.get("serviceArn")

    def cluster_id(self, instance) -> str:
        return instance.get("clusterArn")

    def instance_needs_shutdown(self, instance) -> bool:
        return self.desired_count(instance) > 0

    def instance_needs_startup(self, instance) -> bool:
        return self.desired_count(instance) == 0

    def find_last_steady_state_count(self, instance: dict) -> int:
        pattern = re.compile(r"has\s+started\s+(?P<count>[1-9][0-9]*)\s+tasks")
        for event in instance["events"]:
            match = pattern.search(event["message"])
            if match:
                return int(match.group("count"))
        return 0

    def shutdown(self, instance: dict):
        logging.info("shutting down ecs service %s", self.instance_id(instance))
        if not self.dry_run:
            self.ecs.update_service(
                service=self.instance_id(instance),
                cluster=self.cluster_id(instance),
                desiredCount=0,
            )

    @property
    def ecs(self):
        return self.session.client("ecs")

    def _list_clusters(self) -> Iterator[str]:
        resourcegroups = self.session.client("resourcegroupstaggingapi")
        paginator = resourcegroups.get_paginator("get_resources")
        for resources in paginator.paginate(
            ResourceTypeFilters=["ecs:cluster"],
            TagFilters=[{"Key": "aws:cloudformation:stack-name"}],
        ):
            for resource in resources["ResourceTagMappingList"]:
                if stack_name(resource).startswith(self.stack_name_prefix):
                    yield resource["ResourceARN"]

    def select_instances(self):
        result = []
        for cluster_arn in self._list_clusters():
            paginator = self.ecs.get_paginator("list_services")
            for services in paginator.paginate(cluster=cluster_arn, maxResults=10):
                response = self.ecs.describe_services(
                    services=services["serviceArns"], cluster=cluster_arn
                )
                result.extend(response["services"])

        result = sorted(result, key=lambda instance: instance["serviceName"])

        for i in filter(lambda i: self.verbose, result):
            logging.info(
                "found ecs service %s (%s) with desired count set to %s",
                logical_id(i),
                i["serviceName"],
                i["desiredCount"],
            )

        if not result and self.verbose:
            logging.info("no ECS services found")

        return result
