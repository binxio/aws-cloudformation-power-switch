import logging

from botocore.exceptions import ClientError

from aws_cloudformation_power_switch.power_switch import PowerSwitch
from aws_cloudformation_power_switch.tag import logical_id


class RDSClusterPowerSwitch(PowerSwitch):
    def __init__(self):
        super(RDSClusterPowerSwitch, self).__init__()
        self.resource_type = "AWS::RDS::DBCluster"

    def startup(self, instance: dict):
        name = logical_id(instance)
        cluster_id = self.instance_id(instance)
        logging.info("startup rds cluster %s", cluster_id)
        if not self.dry_run:
            try:
                self.rds.start_db_cluster(DBClusterIdentifier=cluster_id)
            except ClientError as e:
                logging.error("failed to stop %s (%s), %s", name, cluster_id, e)

    def shutdown(self, instance: dict):
        name = logical_id(instance)
        cluster_id = self.instance_id(instance)
        logging.info("shutdown rds cluster %s (%s)", name, cluster_id)
        if not self.dry_run:
            try:
                self.rds.stop_db_cluster(DBClusterIdentifier=cluster_id)
            except ClientError as e:
                logging.error("failed to stop %s (%s), %s", name, cluster_id, e)

    def instance_id(self, instance) -> str:
        return instance["DBClusterIdentifier"]

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
        if self.rds.describe_db_clusters().get("DBClusters"):
            for r in self.stack_resources:
                instance = self.rds.describe_db_clusters(
                    DBClusterIdentifier=r["PhysicalResourceId"]
                )["DBClusters"][0]
                instance["TagList"] = [
                    {"Key": "aws:cloudformation:stack-name", "Value": r["StackName"]},
                    {
                        "Key": "aws:cloudformation:logical-id",
                        "Value": r["LogicalResourceId"],
                    },
                ]
                result.append(instance)

        for i in filter(lambda i: self.verbose, result):
            logging.info(
                "rds cluster %s (%s) in state %s",
                logical_id(i),
                i["DBClusterIdentifier"],
                i["Status"],
            )

        if not result and self.verbose:
            logging.info("No RDS clusters found")

        return result
