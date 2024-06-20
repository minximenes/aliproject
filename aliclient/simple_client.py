# -*- coding: utf-8 -*-
import base64
import os
import sys

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from alibabacloud_tea_openapi import models as openapi_models
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_darabonba_env.client import Client as EnvClient


class SimpleClient:
    def __init__(self):
        pass

    # constant
    ACCESS_KEY_ID = "ALIBABA_CLOUD_ACCESS_KEY_ID"
    ACCESS_KEY_SECRET = "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
    INSTANCE_PASSWORD = "ALIBABA_CLOUD_INSTANCE_PASSWORD"

    # create configuration
    @staticmethod
    def Config(endpoint: str = "ecs.aliyuncs.com") -> openapi_models.Config:
        config = openapi_models.Config(
            access_key_id=EnvClient.get_env(SimpleClient.ACCESS_KEY_ID),
            access_key_secret=EnvClient.get_env(SimpleClient.ACCESS_KEY_SECRET),
            endpoint=endpoint,
            connect_timeout=5000,
            read_timeout=5000,
        )
        return config

    # describe security groups
    # option parameter: region_id, security_group_name(optional)
    # return security_group_ids
    @staticmethod
    def describeSecurityGroups(**kwargs: Dict) -> List[str]:
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        region_id = kwargs.get("region_id")
        # groups
        security_groups_request = ecs_models.DescribeSecurityGroupsRequest(**kwargs)
        security_groups_response = client.describe_security_groups_with_options(
            security_groups_request, runtime
        )
        security_groups = security_groups_response.body.security_groups.security_group
        # attr info
        for group in security_groups:
            group_id = group.security_group_id
            group_name = group.security_group_name
            group_attr_request = ecs_models.DescribeSecurityGroupAttributeRequest(
                region_id=region_id, security_group_id=group_id
            )
            security_group_response = client.describe_security_group_attribute_with_options(
                group_attr_request, runtime
            )
            permissions = security_group_response.body.permissions.permission
            print(f"Security group {group_id}/{group_name} permission info")
            for permission in permissions:
                print(
                    "".join(
                        [
                            f"direction: {permission.direction} ",
                            f"policy: {permission.policy} ",
                            f"priority: {permission.priority} ",
                            f"ip_protocol: {permission.ip_protocol} ",
                            f"port_range: {permission.port_range} ",
                            f"source_cidr_ip: {permission.source_cidr_ip}"
                        ]
                    )
                )
        return [group.security_group_id for group in security_groups]

    # create security group with initial permissions
    # parameter: region_id, security_group_name
    # return security_group_id
    @staticmethod
    def createSecurityGroup(
        region_id: str, security_group_name: str = "socks"
    ) -> str:
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()
        # create security group
        create_security_group_request = ecs_models.CreateSecurityGroupRequest(
            region_id=region_id, security_group_name=security_group_name
        )
        create_security_group_response = client.create_security_group_with_options(
            create_security_group_request, runtime
        )
        security_group_id = create_security_group_response.body.security_group_id
        print(f"security group {security_group_id} has been created")

        # initialize permissions
        permissions = [
            ecs_models.AuthorizeSecurityGroupRequestPermissions(**v)
            for v in SimpleClient.getInitialPermissions()
        ]
        authorize_security_group_request = ecs_models.AuthorizeSecurityGroupRequest(
            region_id=region_id,
            security_group_id=security_group_id,
            permissions=permissions
        )
        client.authorize_security_group_with_options(authorize_security_group_request, runtime)
        print(f'security group {security_group_id} has been initialized')
        return security_group_id

    # get initial permissions
    # TCP22, RDP3389, ICMP-1, TCP5000, TCP/UDP8388
    # return list of permissons
    @staticmethod
    def getInitialPermissions() -> List[Dict]:
        return [
            {
                "policy": "accept",
                "ip_protocol": "TCP",
                "port_range": "22/22",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "SSH",
            },
            {
                "policy": "accept",
                "ip_protocol": "TCP",
                "port_range": "3389/3389",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "RDP",
            },
            {
                "policy": "accept",
                "ip_protocol": "ICMP",
                "port_range": "-1/-1",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "ICMP",
            },
            {
                "policy": "accept",
                "ip_protocol": "TCP",
                "port_range": "5000/5000",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "FlaskHttp",
            },
            {
                "policy": "accept",
                "ip_protocol": "TCP",
                "port_range": "8388/8388",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "vpn",
            },
            {
                "policy": "accept",
                "ip_protocol": "UDP",
                "port_range": "8388/8388",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "vpn",
            },
        ]

    # delete security group that not related to any instance
    # parameter: region_id, security_group_id
    # Exception: ValueError
    @staticmethod
    def deleteSecurityGroup(region_id, security_group_id):
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        # retrieve all instances
        describe_instances_request = ecs_models.DescribeInstancesRequest(region_id=region_id)
        describe_instances_response = client.describe_instances_with_options(
            describe_instances_request, runtime
        )
        # if in use
        instances = describe_instances_response.body.instances.instance
        security_group_ids = set()
        for instance in instances:
            security_group_ids.update(instance.security_group_ids.security_group_id)
        if security_group_id in security_group_ids:
            raise ValueError(f'Security group {security_group_id} is in use, can not be deleted')

        # delete when not related to any instance
        delete_security_group_request = ecs_models.DeleteSecurityGroupRequest(
            region_id=region_id, security_group_id=security_group_id
        )
        client.delete_security_group_with_options(delete_security_group_request, runtime)
        print(f'Security group {security_group_id} has been deleted')

    # add permissions in security group
    # parameter: region_id, security_group_id, port
    @staticmethod
    def addPermissions(region_id: str, security_group_id: str, port: int):
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()
        # add permissions
        permissions = [
            ecs_models.AuthorizeSecurityGroupRequestPermissions(**v)
            for v in SimpleClient.getPermListByPort(port)
        ]
        authorize_security_group_request = ecs_models.AuthorizeSecurityGroupRequest(
            region_id=region_id,
            security_group_id=security_group_id,
            permissions=permissions
        )
        client.authorize_security_group_with_options(authorize_security_group_request, runtime)
        print(f'TCP/UDP {port} has been added to security group')

    # remove permissions in security group
    # parameter: region_id, security_group_id, port
    @staticmethod
    def removePermissions(region_id: str, security_group_id: str, port: int):
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()
        # remove permissions
        permissions = [
            ecs_models.RevokeSecurityGroupRequestPermissions(**v)
            for v in SimpleClient.getPermListByPort(port)
        ]
        revoke_security_group_request = ecs_models.RevokeSecurityGroupRequest(
            region_id=region_id,
            security_group_id=security_group_id,
            permissions=permissions
        )
        client.revoke_security_group_with_options(revoke_security_group_request, runtime)
        print(f'TCP/UDP {port} has been removed from security group')

    # get permissions by port
    # parameters: port
    # return list of TCP/UDP permissons
    @staticmethod
    def getPermListByPort(port: int) -> List[Dict]:
        return [
            {
                "policy": "accept",
                "ip_protocol": "TCP",
                "port_range": f"{port}/{port}",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "vpn",
            },
            {
                "policy": "accept",
                "ip_protocol": "UDP",
                "port_range": f"{port}/{port}",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "vpn",
            },
        ]

    # create instance
    # parameter: region_id, security_group_id, setting(vCPU, memGiB, bandwidth)
    # return instance_ids
    # Exception: ValueError
    @staticmethod
    def createInstance(
        region_id: str, security_group_id: str, setting: Tuple = (1, 1, 3)
    ) -> List[str]:
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        # v_switch
        describe_vswitches_request = ecs_models.DescribeVSwitchesRequest(
            region_id=region_id, is_default=True
        )
        describe_vswitches_response = client.describe_vswitches_with_options(
            describe_vswitches_request, runtime
        )
        v_switches = describe_vswitches_response.body.v_switches.v_switch
        if len(v_switches) == 0:
            raise ValueError(f"There is no v-switch in region {region_id}, please initialize in web")
        v_switch_id = v_switches[0].v_switch_id

        run_instances_request = ecs_models.RunInstancesRequest(
            amount=1,
            auto_release_time=SimpleClient.getAliveTime(60),
            image_id="ubuntu_22_04_x64_20G_alibase_20240530.vhd",
            instance_charge_type="PostPaid",
            internet_charge_type="PayByBandwidth",
            password=EnvClient.get_env(SimpleClient.INSTANCE_PASSWORD),
            region_id=region_id,
            security_group_id=security_group_id,
            user_data=SimpleClient.getUserData(),
            v_switch_id = v_switch_id,
        )
        # additional setting
        run_instances_request = SimpleClient.specInstanceSetting(run_instances_request, setting)

        run_instances_response = client.run_instances_with_options(
            run_instances_request, runtime
        )
        instance_ids = run_instances_response.body.instance_id_sets.instance_id_set
        print(f"Instance {instance_ids} have been created")
        for instance_id in instance_ids:
            SimpleClient.describeInstanceAttribute(instance_id)

        return instance_ids

    # specificate run instance request by setting
    # parameter: runInstancesRequest, setting(vCPU, memGiB, bandwidth)
    # return instance request
    # Exception: ValueError
    @staticmethod
    def specInstanceSetting(
        request: ecs_models.RunInstancesRequest, setting: Tuple
    ) -> ecs_models.RunInstancesRequest:
        # vCPU, memGiB, bandwidth
        vCPUGiB, bandwidth = setting[:2], setting[-1]
        if vCPUGiB == (1, 1):
            instance_type, disk_category = ("ecs.xn4.small", "cloud_ssd")
        elif vCPUGiB == (1, 2):
            instance_type, disk_category = ("ecs.n4.small", "cloud_ssd")
        elif vCPUGiB == (2, 2):
            instance_type, disk_category = ("ecs.u1-c1m1.large", "cloud_essd")
        elif vCPUGiB == (2, 4):
            instance_type, disk_category = ("ecs.u1-c1m2.large", "cloud_essd")
        else:
            raise ValueError(f"vCPUGiB {vCPUGiB} is not supported")

        request.instance_type = instance_type
        request.internet_max_bandwidth_out = bandwidth
        request.system_disk = ecs_models.RunInstancesRequestSystemDisk(
            size="20", category=disk_category
        )
        return request

    # get user data
    # return script string or empty
    @staticmethod
    def getUserData() -> str:
        user_data = ""
        data_path = os.path.join(os.path.dirname(__file__), "user_data")
        if os.path.exists(data_path):
            with open(data_path, "r") as f:
                user_data = f.read()

        return base64.b64encode(user_data.encode("utf-8")).decode("utf-8")

    # describe instances in regions
    # parameter: region_ids
    @staticmethod
    def describeInstances(region_ids: List[str]):
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        for region_id in region_ids:
            request = ecs_models.DescribeInstancesRequest(region_id=region_id)
            response = client.describe_instances_with_options(request, runtime)
            instances = response.body.instances.instance

            print(f"ECS instances in {region_id}")
            for index, instance in enumerate(instances):
                print(
                    "".join(
                        [
                            f"{index + 1} {instance.instance_id}", "\n",
                            f"Spec：{instance.instance_type} CPU:{instance.cpu} Memory:{int(instance.memory/1024)}GB", "\n",
                            f"OS:{instance.ostype}({instance.osname}) ",
                            f"public_ip_address: {instance.public_ip_address.ip_address}", "\n",
                            f"Status：{instance.status}",
                        ]
                    )
                )

    # describe attributes of instance
    # parameter: instance_id
    @staticmethod
    def describeInstanceAttribute(instance_id: str):
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        # instance attribute
        describe_instance_attribute_request = ecs_models.DescribeInstanceAttributeRequest(
            instance_id=instance_id
        )
        describe_instance_attribute_response = client.describe_instance_attribute_with_options(
            describe_instance_attribute_request, runtime
        )
        instance = describe_instance_attribute_response.body
        region_id = instance.region_id
        print(f"ECS instance {instance_id} info")
        print(
            "".join(
                [
                    # summary
                    f"creation_time: {instance.creation_time}", "\n",
                    f"instance_charge_type: {instance.instance_charge_type}", "\n",
                    f"region_id: {region_id}", "\n",
                    # instance and image
                    f"instance_type: {instance.instance_type}", "\n",
                    f"cpu: {instance.cpu}", "\n",
                    f"memory: {int(instance.memory/1024)}GB", "\n",
                    f"image_id: {instance.image_id}", "\n",
                    # internet
                    f"internet_charge_type: {instance.internet_charge_type}", "\n",
                    f"public_ip_address: {instance.public_ip_address.ip_address}", "\n",
                    f"internet_max_bandwidth_in: {instance.internet_max_bandwidth_in}", "\n",
                    f"internet_max_bandwidth_out: {instance.internet_max_bandwidth_out}", "\n",
                    f"security_group_id: {instance.security_group_ids.security_group_id}"
                ]
            )
        )
        # system disk
        describe_disks_request = ecs_models.DescribeDisksRequest(
            region_id=region_id, instance_id=instance_id, disk_type="system"
        )
        describe_disks_response = client.describe_disks_with_options(
            describe_disks_request, runtime
        )
        disks = describe_disks_response.body.disks.disk
        print("disk info")
        for disk in disks:
            print(
                "".join(
                    [
                        f"category: {disk.category}", "\n"
                        f"size: {disk.size}GB", "\n"
                        f"delete_with_instance: {disk.delete_with_instance}"
                    ]
                )
            )
        # user data
        describe_user_data_request = ecs_models.DescribeUserDataRequest(
            region_id=region_id, instance_id=instance_id
        )
        describe_user_data_response = client.describe_user_data_with_options(
            describe_user_data_request, runtime
        )
        user_data_base64 = describe_user_data_response.body.user_data
        user_data = base64.b64decode(user_data_base64).decode('utf-8')
        print(f"user_data:\n{user_data}")

    # reboot instance
    # parameter: instance_id
    @staticmethod
    def rebootInstance(instance_id: str):
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        request = ecs_models.RebootInstanceRequest(instance_id=instance_id)
        client.reboot_instance_with_options(request, runtime)
        print(f"ECS instance {instance_id} has been rebooted")

    # delete instance
    # parameter: instance_id
    @staticmethod
    def deleteInstance(instance_id: str):
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        request = ecs_models.DeleteInstanceRequest(instance_id=instance_id, force=True)
        client.delete_instance_with_options(request, runtime)
        print(f"ECS instance {instance_id} has been released")

    # get alive time after minutes
    # parameter: alive_minutes
    # return: UTC+0, format should be yyyy-MM-ddTHH:mm:00Z
    @staticmethod
    def getAliveTime(alive_minutes: int) -> str:
        if alive_minutes < 30:
            alive_minutes = 30

        utc_now = datetime.utcnow()
        utc_later = utc_now + timedelta(minutes=alive_minutes)
        return utc_later.strftime('%Y-%m-%dT%H:%M:00Z')

    # set auto release time
    # parameter: instance_id, alive_minutes
    @staticmethod
    def autoReleaseInstance(instance_id: str, alive_minutes: int):
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        auto_release_tm = SimpleClient.getAliveTime(alive_minutes)
        request = ecs_models.ModifyInstanceAutoReleaseTimeRequest(
            instance_id=instance_id, auto_release_time=auto_release_tm
        )
        client.modify_instance_auto_release_time_with_options(request, runtime)
        print(f"ECS instance {instance_id} has been set to release at {auto_release_tm}")


if __name__ == "__main__":
    pass
