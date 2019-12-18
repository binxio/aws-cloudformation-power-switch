import logging
from typing import List


from aws_cloudformation_power_switch.power_switch import PowerSwitch
from aws_cloudformation_power_switch.tag import stack_name, logical_id


class ASGPowerSwitch(PowerSwitch):
    def __init__(self):
        super(ASGPowerSwitch, self).__init__()

    def startup(self, instance: dict):
        name = instance["AutoScalingGroupName"]
        desired_capacity = instance["DesiredCapacity"]
        max_size = instance["MaxSize"]

        logging.info("setting capacity of auto scaling group %s (%s) to %s", logical_id(instance), name, max_size)
        if not self.dry_run:
            self.autoscaling.update_auto_scaling_group(
                AutoScalingGroupName=name, DesiredCapacity=desired_capacity
            )

    def shutdown(self, instance: dict):
        name = instance["AutoScalingGroupName"]
        logging.info("setting capacity of auto scaling group %s (%s) to 0", logical_id(instance), name)
        if not self.dry_run:
            self.autoscaling.update_auto_scaling_group(
                AutoScalingGroupName=name, DesiredCapacity=0, MinSize=0
            )

    def instance_desired_capacity(self, instance) -> int:
        return instance["DesiredCapacity"]

    def instance_needs_shutdown(self, instance) -> bool:
        return self.instance_desired_capacity(instance) > 0

    def instance_needs_startup(self, instance) -> bool:
        return self.instance_desired_capacity(instance) == 0

    @property
    def autoscaling(self):
        return self.session.client("autoscaling")

    def select_instances(self) -> List[dict]:
        result = []
        paginator = self.autoscaling.get_paginator("describe_auto_scaling_groups")
        for response in paginator.paginate():
            result.extend(
                filter(
                    lambda a: stack_name(a).startswith(self.stack_name_prefix),
                    response["AutoScalingGroups"],
                )
            )

        for i in filter(lambda i: self.verbose, result):
                logging.info(
                    "found auto scaling group %s (%s) with desired capacity %s",
                    logical_id(i),
                    i["AutoScalingGroupName"],
                    i["DesiredCapacity"],
                )

        if not result:
            logging.info("No auto scaling groups found")

        return result
