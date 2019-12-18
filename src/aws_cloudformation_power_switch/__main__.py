import os
import logging
import click

from aws_cloudformation_power_switch.master import power_switch

@click.group(help="power off all running instances managed by CloudFormation stacks")
@click.pass_context
@click.option('--stack-name-prefix', '-s', required=True, help='of stacks to startup/shutdown')
@click.option('--dry-run', '-d', is_flag=True, default=False, help='do not change anything, just show what is going to happen')
@click.option('--profile', '-p', help='to use')
@click.option('--region', '-r', help='to use')
@click.option('--verbose', '-v', is_flag=True, default=False, help='output')
def main(ctx,**kwargs):
    ctx.obj = power_switch(**kwargs)

@main.command(name='on', help="start all ec2, rds and auto scaling instances")
@click.pass_context
def on(ctx):
    ctx.obj.on()

@main.command(name='off', help="stop all ec2, rds and auto scaling instances")
@click.pass_context
def off(ctx):
    ctx.obj.off()




if __name__ == '__main__':
    main()
