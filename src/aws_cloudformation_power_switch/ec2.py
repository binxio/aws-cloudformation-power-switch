import logging

from aws_cloudformation_power_switch.power_switch import PowerSwitch
from aws_cloudformation_power_switch.tag import logical_id, stack_name


class EC2PowerSwitch(PowerSwitch):
    def __init__(self):
        super(EC2PowerSwitch, self).__init__()

    def startup(self, instance: dict):
        instance_id = instance["InstanceId"]
        logging.info("starting ec2 instance %s (%s)", logical_id(instance), instance_id)
        if not self.dry_run:
            self.ec2.start_instances(InstanceIds=[instance_id])

    def instance_state(self, instance) -> str:
        return instance.get("State", {}).get("Name", "unknown")

    def instance_needs_shutdown(self, instance) -> bool:
        return self.instance_state(instance) == "running"

    def instance_needs_startup(self, instance) -> bool:
        return self.instance_state(instance) == "stopped"

    def shutdown(self, instance: dict):
        instance_id = instance["InstanceId"]
        logging.info("shutting down ec2 instance %s (%s)", logical_id(instance), instance_id)
        if not self.dry_run:
            self.ec2.stop_instances(InstanceIds=[instance_id])

    @property
    def ec2(self):
        return self.session.client("ec2")

    def select_instances(self):
        result = []
        paginator = self.ec2.get_paginator("describe_instances")
        for response in paginator.paginate():
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    if stack_name(instance).startswith(self.stack_name_prefix):
                        result.append(instance)

        result = sorted(result, key=lambda instance: logical_id(instance))

        for i in filter(lambda i: self.verbose, result):
            logging.info(
                "found ec2 instance %s (%s) in state %s",
                logical_id(i),
                i["InstanceId"],
                i.get("State", {}).get("Name", "unknown"),
            )

        if not result:
            logging.info("no EC2 instances found")

        return result
