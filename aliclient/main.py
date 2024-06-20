# -*- coding: utf-8 -*-
from os import path as ospath
import sys
sys.path.append(ospath.dirname(ospath.dirname(ospath.abspath(__file__))))

import click

from alibabacloud_darabonba_string.client import Client as StringClient
from aliclient.simple_client import SimpleClient


# check argument1
def checkObject(ctx, param, value):
    if value not in ["instance", "ins", "security", "sec", "permission", "per"]:
        raise click.BadArgumentUsage("arg1 should be instance(ins) | security(sec) | permission(per)")
    return value


# check argument2
def checkAction(ctx, param, value):
    obj = ctx.params["arg1"]
    # instance
    if obj in ["instance", "ins"] and value not in [
        "create", "delete", "release", "reboot", "desc",
    ]:
        raise click.BadArgumentUsage(
            "arg2 should be create | delete | release | reboot | desc"
        )
    # security group
    if obj in ["security", "sec"] and value not in ["create", "delete", "desc"]:
        raise click.BadArgumentUsage("arg2 should be create | delete | desc")
    # permission
    if obj in ["permission", "per"] and value not in ["add", "remove"]:
        raise click.BadArgumentUsage("arg2 should be add | remove")
    return value


@click.command()
@click.argument('arg1', callback=checkObject)
@click.argument('arg2', callback=checkAction)
@click.option('--region', '-r')
@click.option('--instance', '-i')
@click.option('--group', '-g')
@click.option('--groupname', '-n')
@click.option('--port', '-p')
@click.option('--alive', '-a')
@click.option('--setting', '-s')
def main(arg1, arg2, region, instance, group, groupname, port, alive, setting):
    if arg1 in ["instance", "ins"]:
        if arg2 == "create":
            createInstance(region, group, setting)
        elif arg2 == "delete":
            deleteInstanceWithConfirm(instance)
        elif arg2 == "release":
            autoReleaseInstance(instance, alive)
        elif arg2 == "reboot":
            rebootInstance(instance)
        elif arg2 == "desc":
            descInstance(region, instance)
    if arg1 in ["security", "sec"]:
        if arg2 == "create":
            createSecurityGroup(region, groupname)
        elif arg2 == "delete":
            deleteSecurityGroup(region, group)
        elif arg2 == "desc":
            describeSecurityGroups(region, groupname)
    if arg1 in ["permission", "per"]:
        if arg2 == "add":
            addPermissions(region, group, port)
        elif arg2 == "remove":
            removePermissions(region, group, port)


# parameter validation
class ParamValidation():
    def __init__(self, val, valname):
        self.val = val
        self.valname = valname
    def requiredCheck(self):
        if self.val == None or len(self.val) == 0:
            raise ValueError(f"Please input {self.valname}")
        return self
    def TypeCheck(self, typename):
        if type(self.val) != typename:
            raise ValueError(f"Please input {self.valname} in {typename}")
        return self


"""
instance
"""
def createInstance(region_id, security_group_id, setting):
    # parameter
    ParamValidation(region_id, "region").requiredCheck()
    ParamValidation(security_group_id, "security group").requiredCheck()

    if setting == None or len(setting) == 0:
        SimpleClient.createInstance(region_id, security_group_id)
    else:
        settingTuple = tuple(int(x) for x in StringClient.split(setting, ",", 3))
        if len(settingTuple) < 3:
            raise ValueError(f"Setting {settingTuple} should have 3 elements")

        SimpleClient.createInstance(region_id, security_group_id, settingTuple)


def deleteInstanceWithConfirm(instance_id):
    # parameter
    ParamValidation(instance_id, "instance").requiredCheck()

    while True:
        user_confirm = input("Plese input [delete] for confirm before you delete instance: ")
        if user_confirm == "delete":
            break
        else:
            print("Skip and stop deletion")
            return
    SimpleClient.deleteInstance(instance_id)


def autoReleaseInstance(instance_id, alive_minutes):
    # parameter
    ParamValidation(instance_id, "instance").requiredCheck()
    ParamValidation(alive_minutes, "alive").requiredCheck().TypeCheck("int")

    SimpleClient.autoReleaseInstance(instance_id, int(alive_minutes))


def rebootInstance(instance_id):
    # parameter
    ParamValidation(instance_id, "instance").requiredCheck()

    SimpleClient.rebootInstance(instance_id)


def descInstance(region, instance_id):
    if region == None or len(region) == 0:
        # parameter
        ParamValidation(instance_id, "instance").requiredCheck()
        # describe instance
        SimpleClient.describeInstanceAttribute(instance_id)
    else:
        region_ids = StringClient.split(region, ",", None)
        # describe multi regions
        SimpleClient.describeInstances(region_ids)


"""
security group
"""
def createSecurityGroup(region_id, group_name):
    # parameter
    ParamValidation(region_id, "region").requiredCheck()
    if group_name == None or len(group_name) == 0:
        SimpleClient.createSecurityGroup(region_id)
    else:
        SimpleClient.createSecurityGroup(region_id, group_name)


def deleteSecurityGroup(region_id, security_group_id):
    # parameter
    ParamValidation(region_id, "region").requiredCheck()
    ParamValidation(security_group_id, "security group").requiredCheck()

    SimpleClient.deleteSecurityGroup(region_id, security_group_id)


def describeSecurityGroups(region_id, group_name):
    # parameter
    ParamValidation(region_id, "region").requiredCheck()
    ParamValidation(security_group_id, "security group").requiredCheck()

    if group_name == None or len(group_name) == 0:
        SimpleClient.describeSecurityGroups(region_id=region_id)
    else:
        SimpleClient.describeSecurityGroups(region_id=region_id, security_group_name=group_name)


"""
security permission
"""
def addPermissions(region_id, security_group_id, port):
    # parameter
    ParamValidation(region_id, "region").requiredCheck()
    ParamValidation(security_group_id, "security group").requiredCheck()
    ParamValidation(port, "port").requiredCheck().TypeCheck("int")

    SimpleClient.addPermissions(region_id, security_group_id, port)


def removePermissions(region_id, security_group_id, port):
    # parameter
    ParamValidation(region_id, "region").requiredCheck()
    ParamValidation(security_group_id, "security group").requiredCheck()
    ParamValidation(port, "port").requiredCheck().TypeCheck("int")

    SimpleClient.removePermissions(region_id, security_group_id, port)


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
    instance create | delete | release | reboot | desc
    """
    pass

@instance.command
@click.option('--region', '-r', required=True, help="region id")
@click.option('--group', '-g', required=True, help="security group id")
@click.option('--setting', '-s', type=(int, int ,int), help="setting of vCPU, memGiB, bandwidthMbps")
def create(region, group, setting):
    """
    create instance with security group and setting of vCPU, memGiB, bandwidth
    """
    if setting == None:
        SimpleClient.createInstance(region, group)
    else:
        SimpleClient.createInstance(region, group, setting)

@instance.command
@click.option('--instance', '-i', required=True, help="instance id")
def delete(instance):
    """
    delete instance after confirm
    """
    if click.confirm("Are you sure you want to delete the instance immediately?"):
        SimpleClient.deleteInstance(instance)

@instance.command
@click.option('--instance', '-i', required=True, help="instance id")
@click.option('--alive', '-a', type=int, required=True, help="alive minutes")
def release(instance, alive):
    """
    release instance after given minutes
    """
    SimpleClient.autoReleaseInstance(instance, alive)

@instance.command
@click.option('--instance', '-i', required=True, help="instance id")
def reboot(instance):
    """
    reboot instance
    """
    SimpleClient.rebootInstance(instance)

@instance.command
@click.option('--region', '-r', nargs=-1, help="region ids")
@click.option('--instance', '-i', help="instance id")
def desc(region, instance):
    """
    describe instance when instance id is given, otherwise describe multi regions
    """
    if instance == None:
        # describe multi regions
        SimpleClient.describeInstances(region)
    else:
        # describe instance
        SimpleClient.describeInstanceAttribute(instance)

# security group
@run.group()
def security():
    """
    security group create | delete | desc
    """
    pass

@security.command
@click.option('--region', '-r', required=True, help="region id")
@click.option('--groupname', '-n', help="security group name")
def create(region, groupname):
    """
    create security group with permissions if not exist
    """
    if groupname == None:
        SimpleClient.createSecurityGroup(region)
    else:
        SimpleClient.createSecurityGroup(region, groupname)

@security.command
@click.option('--region', '-r', required=True, help="region id")
@click.option('--group', '-g', required=True, help="security group id")
def delete(region, group):
    """
    delete security group that not related to any instance
    """
    SimpleClient.deleteSecurityGroup(region, group)

@security.command
@click.option('--region', '-r', required=True, help="region id")
@click.option('--groupname', '-n', help="security group name")
def desc(region, groupname):
    """
    desc security group
    """
    if groupname == None:
        SimpleClient.describeSecurityGroups(region_id=region)
    else:
        SimpleClient.describeSecurityGroups(region_id=region, security_group_name=groupname)

# permission
@run.group()

def permission():
    """
    port permission add | remove
    """
    pass

@permission.command
@click.option('--region', '-r', required=True, help="region id")
@click.option('--group', '-g', required=True, help="security group id")
@click.option('--port', '-p', type=int, required=True, help="allowed port")
def add(region, group, port):
    """
    add permissions in security group
    """
    SimpleClient.addPermissions(region, group, port)

@permission.command
@click.option('--region', '-r', required=True, help="region id")
@click.option('--group', '-g', required=True, help="security group id")
@click.option('--port', '-p', type=int, required=True, help="allowed port")
def remove(region, group, port):
    """
    remove permissions in security group
    """
    SimpleClient.addPermissions(region, group, port)

if __name__ == "__main__":
    run()
