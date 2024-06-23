# -*- coding: utf-8 -*-
from os import path as ospath
import sys

sys.path.append(ospath.dirname(ospath.dirname(ospath.abspath(__file__))))

import click

from alibabacloud_darabonba_string.client import Client as StringClient
from aliclient.simple_client import SimpleClient


@click.group()
def run():
    """
    Use Ali openapi with commands:\n
        retrieve security group id by name\n
        create security group with permissions(ICMP-1, TCP22, TCP5000, TCP/UDP3389) if not exist\n
        create instance with joining the security group\n
        add/delete permissions in security group\n
        retrieve instance's public ip, create time and release time\n
        delete instance\n
        delete security group that not related to any instance\n
    """
    pass


# instance
@run.group()
def instance():
    """
    instance create | delete | release | reboot | desc | qrcode
    """
    pass


@instance.command
@click.option("--region", "-r", required=True, help="region id")
@click.option("--group", "-g", required=True, help="security group id")
@click.option("--setting", "-s", type=(int, int, int), help="setting of vCPU, memGiB, bandwidthMbps")
@click.option("--alive", "-a", type=int, help="alive minutes")
def create(region, group, setting, alive):
    """
    create instance with security group and setting of vCPU, memGiB, bandwidth
    """
    if click.confirm("Create new instance will be charged. You sure want to create?"):
        kwargs = {"region_id": region, "security_group_id": group}
        if setting:
            kwargs["setting"] = setting
        if alive:
            kwargs["alive_minutes"] = alive

        SimpleClient.createInstance(**kwargs)
    else:
        print("Operation stop!")


@instance.command
@click.option("--instance", "-i", required=True, help="instance id")
def delete(instance):
    """
    delete instance after confirm
    """
    if click.confirm("You sure want to delete the instance immediately?"):
        SimpleClient.deleteInstance(instance)
    else:
        print("Operation stop!")


@instance.command
@click.option("--instance", "-i", required=True, help="instance id")
@click.option("--alive", "-a", type=int, required=True, help="alive minutes")
def release(instance, alive):
    """
    release instance after given minutes
    """
    SimpleClient.autoReleaseInstance(instance, alive)


@instance.command
@click.option("--instance", "-i", required=True, help="instance id")
def reboot(instance):
    """
    reboot instance
    """
    SimpleClient.rebootInstance(instance)


def instance_desc_option(ctx, param, value):
    """
    instance desc option check
    """
    if not value:
        region = ctx.params.get("region")
        if not region:
            raise click.UsageError("--instance is required when --region is not provided")
    return value


@instance.command
@click.option("--region", "-r", help="region ids, seperated by comma")
@click.option("--instance", "-i", callback=instance_desc_option, help="instance id")
def desc(region, instance):
    """
    describe instance when instance id is given, otherwise describe regions
    """
    if not instance:
        # describe regions
        region_ids = StringClient.split(region, ",", None)
        SimpleClient.describeInstances(region_ids)
    else:
        # describe instance
        SimpleClient.describeInstanceAttribute(instance)


@instance.command
@click.option("--instance", "-i", required=True, help="instance id")
def qrcode(instance):
    """
    print instance's ss qrcode
    """
    SimpleClient.printInstanceSsqrcode(instance)


# security group
@run.group()
def security():
    """
    security group create | delete | desc
    """
    pass


@security.command
@click.option("--region", "-r", required=True, help="region id")
@click.option("--groupname", "-n", help="security group name")
def create(region, groupname):
    """
    create security group with permissions if not exist
    """
    if not groupname:
        SimpleClient.createSecurityGroup(region)
    else:
        SimpleClient.createSecurityGroup(region, groupname)


@security.command
@click.option("--region", "-r", required=True, help="region id")
@click.option("--group", "-g", required=True, help="security group id")
def delete(region, group):
    """
    delete security group that not related to any instance
    """
    SimpleClient.deleteSecurityGroup(region, group)


@security.command
@click.option("--region", "-r", required=True, help="region id")
@click.option("--groupname", "-n", help="security group name")
def desc(region, groupname):
    """
    desc security group
    """
    if not groupname:
        SimpleClient.describeSecurityGroups(region_id=region)
    else:
        SimpleClient.describeSecurityGroups(
            region_id=region, security_group_name=groupname
        )


# permission
@run.group()
def permission():
    """
    port permission add | remove
    """
    pass


@permission.command
@click.option("--region", "-r", required=True, help="region id")
@click.option("--group", "-g", required=True, help="security group id")
@click.option("--port", "-p", type=int, required=True, help="allowed port")
def add(region, group, port):
    """
    add permissions in security group
    """
    SimpleClient.addPermissions(region, group, port)


@permission.command
@click.option("--region", "-r", required=True, help="region id")
@click.option("--group", "-g", required=True, help="security group id")
@click.option("--port", "-p", type=int, required=True, help="allowed port")
def remove(region, group, port):
    """
    remove permissions in security group
    """
    SimpleClient.addPermissions(region, group, port)


if __name__ == "__main__":
    run()
