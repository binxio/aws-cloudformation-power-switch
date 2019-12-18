import logging

from botocore.exceptions import ClientError

from aws_cloudformation_power_switch.power_switch import PowerSwitch
from aws_cloudformation_power_switch.tag import logical_id, stack_name


class RDSClusterPowerSwitch(PowerSwitch):
    def __init__(self):
        super(RDSClusterPowerSwitch, self).__init__()

    def startup(self, instance: dict):
        db = instance["DBClusterIdentifier"]
        logging.info("startup rds cluster %s", db)
        if not self.dry_run:
            try:
                self.rds.start_db_cluster(DBClusterIdentifier=db)
            except ClientError as e:
                logging.error("failed to start %s, %s", db, e)

    def shutdown(self, instance: dict):
        db = instance["DBClusterIdentifier"]
        name = logical_id(instance)
        logging.info("shutdown rds cluster %s (%s)", name, db)
        if not self.dry_run:
            try:
                self.rds.stop_db_cluster(DBClusterIdentifier=db)
            except ClientError as e:
                logging.error("failed to stop %s, %s", db, e)

    def instance_state(self, instance) -> str:
        return instance["Status"]

    def instance_needs_shutdown(self, instance) -> bool:
        return self.instance_state(instance) == "available"

    def instance_needs_startup(self, instance) -> bool:
        return self.instance_state(instance) == "stopped"

    @property
    def rds(self):
        return self.session.client("rds")

    def select_instances(self):
        result = []
        paginator = self.rds.get_paginator("describe_db_clusters")
        for response in paginator.paginate():
            for instance in response["DBClusters"]:
                arn = instance["DBClusterArn"]
                instance.update(self.rds.list_tags_for_resource(ResourceName=arn))
                ## TODO: RDS Clusters do not carry any AWS CloudFormation tags...
                if stack_name(instance).startswith(self.stack_name_prefix):
                    result.append(instance)

        result = sorted(
            result,
            key=lambda instance: logical_id(instance)
        )

        for i in filter(lambda i: self.verbose, result):
            logging.info(
                "db cluster %s (%s) in state %s"
                % (logical_id(i), i["DBClusterIdentifier"], i["DBInstanceStatus"])
            )

        if not result:
            logging.info("No RDS clusters found")

        return result
