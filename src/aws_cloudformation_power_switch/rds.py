import logging

from botocore.exceptions import ClientError

from aws_cloudformation_power_switch.power_switch import PowerSwitch
from aws_cloudformation_power_switch.tag import logical_id, stack_name


class RDSPowerSwitch(PowerSwitch):
    def __init__(self):
        super(RDSPowerSwitch, self).__init__()

    def startup(self, instance: dict):
        db = instance["DBInstanceIdentifier"]
        logging.info("startup rds instance %s", db)
        if not self.dry_run:
            try:
                self.rds.start_db_instance(DBInstanceIdentifier=db)
            except ClientError as e:
                logging.error("failed to start %s, %s", db, e)

    def shutdown(self, instance: dict):
        db = instance["DBInstanceIdentifier"]
        name = logical_id(instance)
        logging.info("shutdown rds instance %s (%s)", name, db)
        if not self.dry_run:
            try:
                self.rds.stop_db_instance(DBInstanceIdentifier=db)
            except ClientError as e:
                logging.error("failed to stop %s, %s", db, e)

    def instance_state(self, instance) -> str:
        return instance["DBInstanceStatus"]

    def instance_needs_shutdown(self, instance) -> bool:
        return self.instance_state(instance) == "available"

    def instance_needs_startup(self, instance) -> bool:
        return self.instance_state(instance) == "stopped"

    @property
    def rds(self):
        return self.session.client("rds")

    def select_instances(self):
        result = []
        paginator = self.rds.get_paginator("describe_db_instances")
        for response in paginator.paginate():
            for instance in response["DBInstances"]:
                arn = instance["DBInstanceArn"]
                instance.update(self.rds.list_tags_for_resource(ResourceName=arn))
                if 'DBClusterIdentifier' not in instance and stack_name(instance).startswith(self.stack_name_prefix):
                    result.append(instance)

        result = sorted(
            result,
            key=lambda instance: logical_id(instance)
        )

        for i in filter(lambda i: self.verbose, result):
            logging.info(
                "db instance %s (%s) in state %s"
                % (logical_id(i), i["DBInstanceIdentifier"], i["DBInstanceStatus"])
            )

        if not result:
            logging.info("No RDS instances found (todo)")

        return result
