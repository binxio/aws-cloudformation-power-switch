from .asg import ASGPowerSwitch
from .ec2 import EC2PowerSwitch
from .power_switch import PowerSwitch
from .rds import RDSPowerSwitch
from .rds_cluster import RDSClusterPowerSwitch
from .ecs import ECSPowerSwitch


class MasterPowerSwitch(PowerSwitch):
    def __init__(self):
        super(MasterPowerSwitch, self).__init__()

    def select_instances(self):
        result = [
            ASGPowerSwitch(),
            EC2PowerSwitch(),
            RDSClusterPowerSwitch(),
            RDSPowerSwitch(),
            ECSPowerSwitch(),
        ]
        for switch in result:
            switch.session = self.session
            switch.dry_run = self.dry_run
            switch.stack_name_prefix = self.stack_name_prefix
            switch.verbose = self.verbose
        return result

    def instance_needs_startup(self, instance) -> bool:
        return True

    def instance_needs_shutdown(self, instance) -> bool:
        return True

    def startup(self, instance: PowerSwitch):
        instance.on()

    def shutdown(self, instance: PowerSwitch):
        instance.off()


def power_switch(
    stack_name_prefix, dry_run=True, verbose=False, profile=None, region=None
):
    result = MasterPowerSwitch()
    result.set_session(profile, region)
    result.dry_run = dry_run
    result.verbose = verbose
    result.stack_name_prefix = stack_name_prefix
    assert stack_name_prefix, "stack name prefix is required"
    return result
