import boto3
from typing import List
import logging
import sys


class PowerSwitch(object):
    def __init__(self):
        self.stack_name_prefix = None
        self.verbose = False
        self.dry_run = True
        self.session = None

    def select_instances(self) -> List:
        raise Exception("not implemented")

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
            logging.error('no stack name prefix specified')
            sys.exit(1)

    def on(self):
        self.check_precondition()
        for instance in filter(lambda i: self.instance_needs_startup(i), self.select_instances()):
            self.startup(instance)

    def off(self):
        self.check_precondition()
        for instance in filter(lambda i: self.instance_needs_shutdown(i), self.select_instances()):
            self.shutdown(instance)

    def set_session(self, profile, region):
        kwargs = {}
        if region:
            kwargs["region_name"] = region
        if profile:
            kwargs["profile_name"] = profile

        self.session = boto3.Session(**kwargs)