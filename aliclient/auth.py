# -*- coding: utf-8 -*-
import base64
import os
import sys
import time

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Tuple

from alibabacloud_tea_openapi import models as openapi_models
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_vpc20160428.client import Client as VpcClient
from alibabacloud_vpc20160428 import models as vpc_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_darabonba_env.client import Client as EnvClient
from alibabacloud_darabonba_string.client import Client as StringClient


class SimpleClient:
    def __init__(self):
        pass

    # constant
    ACCESS_KEY_ID = "ALIBABA_CLOUD_ACCESS_KEY_ID"
    ACCESS_KEY_SECRET = "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
    INSTANCE_PASSWORD = "ALIBABA_CLOUD_INSTANCE_PASSWORD"

    @staticmethod
    def Config(endpoint: str = "ecs") -> openapi_models.Config:
        """
        create configuration
        @param: endpoint(default "ecs")
        @return: Config
        """
        config = openapi_models.Config(
            access_key_id=EnvClient.get_env(SimpleClient.ACCESS_KEY_ID),
            access_key_secret=EnvClient.get_env(SimpleClient.ACCESS_KEY_SECRET),
            endpoint=f"{endpoint}.aliyuncs.com",
            connect_timeout=5000,
            read_timeout=5000,
        )
        return config

    @staticmethod
    def describeSecurityGroups(
        region_id: str, security_group_name: str = "vpn-_-"
    ) -> List[str]:
        """
        describe security groups
        @param: region_id, security_group_name(default "vpn-_-")
        @return: security_group_ids
        """
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        security_groups_request = ecs_models.DescribeSecurityGroupsRequest(
            region_id=region_id, security_group_name=security_group_name
        )
        security_groups_response = client.describe_security_groups_with_options(
            security_groups_request, runtime
        )
        security_groups = security_groups_response.body.security_groups.security_group
        return [group.security_group_id for group in security_groups]

    @staticmethod
    def createSecurityGroup(
        region_id: str, vpc_id: str, security_group_name: str = "vpn-_-"
    ) -> str:
        """
        create security group with initial permissions
        @param: region_id, vpc_id, security_group_name(default "vpn-_-")
        @return: security_group_id
        """
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()
        # create security group
        create_security_group_request = ecs_models.CreateSecurityGroupRequest(
            region_id=region_id, vpc_id=vpc_id, security_group_name=security_group_name
        )
        create_security_group_response = client.create_security_group_with_options(
            create_security_group_request, runtime
        )
        security_group_id = create_security_group_response.body.security_group_id
        # initialize permissions
        permissions = [
            ecs_models.AuthorizeSecurityGroupRequestPermissions(**v)
            for v in SimpleClient.getInitialPermissions()
        ]
        authorize_security_group_request = ecs_models.AuthorizeSecurityGroupRequest(
            region_id=region_id,
            security_group_id=security_group_id,
            permissions=permissions,
        )
        client.authorize_security_group_with_options(
            authorize_security_group_request, runtime
        )
        return security_group_id

    @staticmethod
    def getInitialPermissions() -> List[Dict]:
        """
        get initial permissions
        TCP22, RDP3389, ICMP-1, TCP5000, TCP/UDP8388, TCP1723, UDP500, UDP4500
        @return: list of permissons
        """
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
                "description": "shadow",
            },
            {
                "policy": "accept",
                "ip_protocol": "UDP",
                "port_range": "8388/8388",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "shadow",
            },
            {
                "policy": "accept",
                "ip_protocol": "TCP",
                "port_range": "1723/1723",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "pptp",
            },
            {
                "policy": "accept",
                "ip_protocol": "UDP",
                "port_range": "500/500",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "ikev2",
            },
            {
                "policy": "accept",
                "ip_protocol": "UDP",
                "port_range": "4500/4500",
                "source_cidr_ip": "0.0.0.0/0",
                "description": "ikev2",
            },
        ]

    @staticmethod
    def getUserData(script: str = "pptp") -> str:
        """
        get user data
        @return: script string or empty
        """
        user_data = ""
        # data_path = os.path.join(os.path.dirname(__file__), "user_data")
        # data_path = os.path.join(os.path.dirname(__file__), "user_data_shadow")
        # data_path = os.path.join(os.path.dirname(__file__), "user_data_pptp")
        data_path = os.path.join(os.path.dirname(__file__), "user_data_ikev2")
        if os.path.exists(data_path):
            with open(data_path, "r") as f:
                user_data = f.read()

        return base64.b64encode(user_data.encode("utf-8")).decode("utf-8")

    @staticmethod
    def describeInstances(region_ids: List[str]):
        """
        describe instances in regions
        @param: region_ids
        """
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        for region_id in region_ids:
            request = ecs_models.DescribeInstancesRequest(region_id=region_id)
            response = client.describe_instances_with_options(request, runtime)
            instances = response.body.instances.instance

            print(f"ECS instances in {region_id}:")
            for index, instance in enumerate(instances):
                SimpleClient.printIndent(
                    f"{index + 1} {instance.instance_id}",
                    f"Spec：{instance.instance_type} CPU:{instance.cpu} Memory:{int(instance.memory/1024)}GB",
                    f"OS:{instance.osname} public_ip_address: {instance.public_ip_address.ip_address}",
                    f"Status：{instance.status}",
                )

    @staticmethod
    def describeInstanceAttribute(instance_id: str):
        """
        describe attributes of instance
        @param: instance_id
        """
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
        print(f"ECS instance {instance_id} info:")
        SimpleClient.printIndent(
            # summary
            f"creation_time: {instance.creation_time}",
            f"instance_charge_type: {instance.instance_charge_type}",
            f"region_id: {region_id}",
            # instance and image
            f"instance_type: {instance.instance_type}",
            f"cpu: {instance.cpu}",
            f"memory: {int(instance.memory/1024)}GB",
            f"image_id: {instance.image_id}",
            # internet
            f"internet_charge_type: {instance.internet_charge_type}",
            f"public_ip_address: {instance.public_ip_address.ip_address}",
            f"internet_max_bandwidth_in: {instance.internet_max_bandwidth_in}",
            f"internet_max_bandwidth_out: {instance.internet_max_bandwidth_out}",
            f"security_group_id: {instance.security_group_ids.security_group_id}",
        )
        # system disk
        describe_disks_request = ecs_models.DescribeDisksRequest(
            region_id=region_id, instance_id=instance_id, disk_type="system"
        )
        describe_disks_response = client.describe_disks_with_options(
            describe_disks_request, runtime
        )
        disks = describe_disks_response.body.disks.disk
        print("disk info:")
        for disk in disks:
            SimpleClient.printIndent(
                f"category: {disk.category}",
                f"size: {disk.size}GB",
                f"delete_with_instance: {disk.delete_with_instance}",
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
        print(f"user_data:")
        SimpleClient.printIndent(*StringClient.split(user_data, "\n", None))

    @staticmethod
    def rebootInstance(instance_id: str):
        """
        reboot instance
        @param: instance_id
        """
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        request = ecs_models.RebootInstanceRequest(instance_id=instance_id)
        client.reboot_instance_with_options(request, runtime)

    @staticmethod
    def deleteInstance(instance_id: str):
        """
        delete instance
        @param: instance_id
        """
        ecs_client = EcsClient(SimpleClient.Config())
        vpc_client = VpcClient(SimpleClient.Config("vpc"))
        runtime = util_models.RuntimeOptions()
        # retrieve instance info
        describe_instance_attribute_request = ecs_models.DescribeInstanceAttributeRequest(
            instance_id=instance_id
        )
        describe_instance_attribute_response = ecs_client.describe_instance_attribute_with_options(
            describe_instance_attribute_request, runtime
        )
        instance = describe_instance_attribute_response.body
        region_id = instance.region_id
        v_switch_id = instance.vpc_attributes.v_switch_id
        vpc_id = instance.vpc_attributes.vpc_id
        security_group_id = instance.security_group_ids.security_group_id[0]
        # delete instance
        delete_instance_request = ecs_models.DeleteInstanceRequest(
            instance_id=instance_id, force=True
        )
        ecs_client.delete_instance_with_options(delete_instance_request, runtime)
        # delete security_group
        delete_security_group_request = ecs_models.DeleteSecurityGroupRequest(
            region_id=region_id, security_group_id=security_group_id
        )
        if not SimpleClient.waitforDeletion(
            (ecs_client.delete_security_group_with_options, delete_security_group_request, runtime)
        ):
            return
        # delete v_switch
        delete_vswitch_request = vpc_models.DeleteVSwitchRequest(
            region_id=region_id, v_switch_id=v_switch_id
        )
        if not SimpleClient.waitforDeletion(
            (vpc_client.delete_vswitch_with_options, delete_vswitch_request, runtime)
        ):
            return
        # delete vpc
        delete_vpc_request = vpc_models.DeleteVpcRequest(
            region_id=region_id, vpc_id=vpc_id, force_delete=True
        )
        if not SimpleClient.waitforDeletion(
            (vpc_client.delete_vpc_with_options, delete_vpc_request, runtime)
        ):
            return

    @staticmethod
    def waitforDeletion(params: Tuple) -> bool:
        """
        wait until previous task finished
        @param: tuple of function handler, parameters
        @return: true when success or false when timeout
        """
        func_name, para1, para2 = params
        starttm = time.perf_counter()
        while True:
            try:
                func_name(para1, para2)
                return True
            except Exception as error:
                if error.code.startswith("DependencyViolation"):
                    if time.perf_counter() - starttm > 30:
                        return False
                    time.sleep(5)
                else:
                    raise error

    @staticmethod
    def getAliveTime(alive_minutes: int) -> str:
        """
        get alive time after minutes
        @param: alive_minutes
        @return: UTC+0, format should be yyyy-MM-ddTHH:mm:00Z
        """
        if alive_minutes < 30:
            alive_minutes = 30

        utc_now = datetime.utcnow()
        utc_later = utc_now + timedelta(minutes=alive_minutes)
        return utc_later.strftime('%Y-%m-%dT%H:%M:00Z')

    @staticmethod
    def autoReleaseInstance(instance_id: str, alive_minutes: int):
        """
        set auto release time
        @param: instance_id, alive_minutes
        """
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        auto_release_tm = SimpleClient.getAliveTime(alive_minutes)
        request = ecs_models.ModifyInstanceAutoReleaseTimeRequest(
            instance_id=instance_id, auto_release_time=auto_release_tm
        )
        client.modify_instance_auto_release_time_with_options(request, runtime)

    @staticmethod
    def describeRegionsWithCondition(region_range: str) -> List[str]:
        """
        describe regions in given range
        @param: region range
        @return: region_ids
        """
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        request = ecs_models.DescribeRegionsRequest(
            resource_type="instance",
            instance_charge_type="SpotAsPriceGo"
        )
        response = client.describe_regions_with_options(request, runtime)
        regions = response.body.regions.region
        region_ids = [r.region_id for r in regions]

        if region_range == "in":
            return list(filter(lambda r: r.startswith("cn-") and r != "cn-hongkong", region_ids))
        elif region_range == "out":
            return list(filter(lambda r: not r.startswith("cn-") or r == "cn-hongkong", region_ids))
        elif region_range in ("us", "eu"):
            return list(filter(lambda r: r.startswith(f"{region_range}-"), region_ids))
        elif region_range == "NEasia":
            return list(filter(lambda r: r.startswith("ap-northeast-"), region_ids))
        elif region_range == "SEasia":
            return list(filter(lambda r: r.startswith("ap-southeast-"), region_ids))
        else:
            rlt = list(filter(lambda r: r == region_range, region_ids))
            if len(rlt) == 0:
                raise ValueError(f"Region range {region_range} is unrecognizable")
            return rlt

    @staticmethod
    def describeAvailableInstances(
        region_ids: List[str], vCPUs: List[int] = [1, 2], memGiBs: List[float] = [1, 2]
    ) -> List[Dict]:
        """
        describe instance type in given regions
        @param: region_ids, vCPU(default 1), memGiB(default 1)
        @return: instance_types
        """
        instance_types = []
        for region_id in region_ids:
            config = SimpleClient.Config(f"ecs.{region_id}")
            client = EcsClient(config)
            runtime = util_models.RuntimeOptions()

            for vCPU, memGiB in ((x, y) for x in vCPUs for y in memGiBs):
                request = ecs_models.DescribeAvailableResourceRequest(
                    region_id=region_id,
                    destination_resource="InstanceType",
                    instance_charge_type="PostPaid",
                    spot_strategy="SpotAsPriceGo",
                    cores=vCPU,
                    memory=memGiB,
                    io_optimized="optimized",
                    network_category='vpc'
                )
                response = client.describe_available_resource_with_options(request, runtime)

                available_zones = response.body.available_zones.available_zone
                for zone in list(filter(lambda z: z.status_category == "WithStock", available_zones)):
                    for resource in zone.available_resources.available_resource:
                        supported_resources = resource.supported_resources.supported_resource
                        for supported_res in list(filter(lambda s: s.status_category == "WithStock", supported_resources)):
                            instance_types.append({
                                "region_id": region_id,
                                "zone_id": zone.zone_id,
                                "instance_type": supported_res.value,
                                "cores": vCPU,
                                "memory": memGiB,
                            })

        if len(instance_types) == 0:
            raise ValueError(f"There is no available instance resource in region {region_ids}")
        return instance_types

    @staticmethod
    def describePrice(
        region_id: str, zone_id: str, instance_type: str, cores: int, memory: float, bandwidth: int
    ) -> Tuple:
        """
        describe instance price
        @param: region_id, zone_id, instance_type
        @return: instance disk category and price
        """
        config = SimpleClient.Config(f"ecs.{region_id}")
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        category_prices = []
        for disk_category in [
            "cloud_efficiency",
            "cloud_essd_entry",
        ]:
            request = ecs_models.DescribePriceRequest(
                region_id=region_id,
                resource_type="instance",
                instance_type=instance_type,
                io_optimized="optimized",
                instance_network_type="vpc",
                # bandwidth
                internet_charge_type="PayByBandwidth",
                internet_max_bandwidth_out=bandwidth,
                # system disk
                image_id=SimpleClient.describeUbuntuImage(region_id),
                system_disk=ecs_models.DescribePriceRequestSystemDisk(
                    size=20, category=disk_category
                ),
                # spot
                spot_strategy="SpotAsPriceGo",
                spot_duration=0,
                zone_id=zone_id,
            )
            try:
                response = client.describe_price_with_options(request, runtime)
                category_prices.append(
                    (disk_category, response.body.price_info.price.trade_price)
                )
            except Exception as error:
                continue

        if len(category_prices) == 0:
            return ("", -1)
        else:
            return min(category_prices, key=lambda p: p[1])

    @staticmethod
    def comparePrice(instance_types: List[Dict], bandwidth: int = 2, amount: int = 3) -> List[Dict]:
        """
        compare instance price
        @param: instance info, bandwidth(default 2Mbps), amount(default 3)
        @return: instances of given amount at lowest price
        """
        instance_prices = []
        for instance_tp in instance_types:
            disk_category, price = SimpleClient.describePrice(
                **instance_tp, bandwidth=bandwidth
            )
            instance_prices.append(
                {**instance_tp, "disk_category": disk_category, "price": price}
            )

        return sorted(
            list(filter(lambda p: p["price"] > 0, instance_prices)),
            key=lambda p: p["price"],
        )[:amount]

    @staticmethod
    def createInstance(
        region_id: str, zone_id: str, instance_type: str, disk_category: str, bandwidth: int, alive_minutes: int = 60
    ):
        """
        create instance
        @param: region_id, zone_id, instance_type, disk_category, bandwidth, alive_minutes(default 60)
        @return: instance_ids
        """
        config = SimpleClient.Config()
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        vpc_id, v_switch_id = SimpleClient.createDefaultVSwitch(region_id, zone_id)
        image_id = SimpleClient.describeUbuntuImage(region_id)
        security_group_id = SimpleClient.createDefaultSecurityGroup(region_id, vpc_id)
        auto_release_time = SimpleClient.getAliveTime(alive_minutes)
        password = EnvClient.get_env(SimpleClient.INSTANCE_PASSWORD)
        user_data = SimpleClient.getUserData()

        run_instances_request = ecs_models.RunInstancesRequest(
            amount=1,
            auto_release_time=auto_release_time,
            region_id=region_id,
            v_switch_id=v_switch_id,
            instance_type=instance_type,
            instance_charge_type="PostPaid",
            spot_strategy="SpotAsPriceGo",
            spot_duration=0,
            password=password,
            security_group_id=security_group_id,
            user_data=user_data,
            # bandwidth
            internet_charge_type="PayByBandwidth",
            internet_max_bandwidth_out=bandwidth,
            # system disk
            image_id=image_id,
            system_disk=ecs_models.DescribePriceRequestSystemDisk(
                size=20, category=disk_category
            ),
        )

        try:
            run_instances_response = client.run_instances_with_options(
                run_instances_request, runtime
            )
        except Exception as error:
            print(error.data.get("Message"))
            return

        instance_ids = run_instances_response.body.instance_id_sets.instance_id_set
        return instance_ids[0]

    @staticmethod
    def createDefaultSecurityGroup(region_id: str, vpc_id: str) -> str:
        """
        retrieve or create security group
        @param: region_id, vpc_id
        @return: security_group_id
        """
        security_group_ids = SimpleClient.describeSecurityGroups(region_id)
        if len(security_group_ids) == 0:
            return SimpleClient.createSecurityGroup(region_id, vpc_id)
        else:
            return security_group_ids[0]

    @staticmethod
    def createDefaultVSwitch(region_id: str, zone_id: str) -> Tuple:
        """
        retrieve or create default vswitch
        @param: region_id, zone_id
        @return: default vpc_id, vswitch_id
        """
        config = SimpleClient.Config("vpc")
        client = VpcClient(config)
        runtime = util_models.RuntimeOptions()

        vpc_id = SimpleClient.createDefaultVpc(region_id)
        describe_vswitches_request = vpc_models.DescribeVSwitchesRequest(
            region_id=region_id, vpc_id=vpc_id, zone_id=zone_id, is_default=True
        )
        describe_vswitches_respnse = client.describe_vswitches_with_options(
            describe_vswitches_request, runtime
        )
        v_switchs = describe_vswitches_respnse.body.v_switches.v_switch
        if len(v_switchs) == 0:
            # create default v_switch
            create_default_vswitch_request = vpc_models.CreateDefaultVSwitchRequest(
                region_id=region_id, zone_id=zone_id
            )
            create_default_vswitch_response = client.create_default_vswitch_with_options(
                create_default_vswitch_request, runtime
            )
            v_switch_id = create_default_vswitch_response.body.v_switch_id
        else:
            v_switch_id = v_switchs[0].v_switch_id

        return (vpc_id, v_switch_id)

    @staticmethod
    def createDefaultVpc(region_id: str) -> str:
        """
        retrieve or create default vpc
        @param: region_id
        @return: default vpc_id
        """
        config = SimpleClient.Config("vpc")
        client = VpcClient(config)
        runtime = util_models.RuntimeOptions()

        describe_vpcs_request = vpc_models.DescribeVpcsRequest(
            region_id=region_id, is_default=True
        )
        describe_vpcs_response = client.describe_vpcs_with_options(
            describe_vpcs_request, runtime
        )
        vpcs = describe_vpcs_response.body.vpcs.vpc
        if len(vpcs) == 0:
            # create default vpc
            create_default_vpc_request = vpc_models.CreateDefaultVpcRequest(
                region_id=region_id
            )
            create_default_vpc_response = client.create_default_vpc_with_options(
                create_default_vpc_request, runtime
            )
            vpc_id = create_default_vpc_response.body.vpc_id
            # wait for available
            SimpleClient.waitforAvailable((region_id, "vpc", vpc_id))
            return vpc_id
        else:
            return vpcs[0].vpc_id

    @staticmethod
    def waitforAvailable(params: Tuple):
        starttm = time.perf_counter()
        region_id, resource_type, resource_id = params

        if resource_type == "vpc":
            config = SimpleClient.Config("vpc")
            client = VpcClient(config)
            runtime = util_models.RuntimeOptions()

            request = vpc_models.DescribeVpcAttributeRequest(
                region_id=region_id, vpc_id=resource_id
            )
            response = client.describe_vpc_attribute_with_options(request, runtime)
            vpc = response.body
            while vpc.status != "Available":
                if time.perf_counter() - starttm > 30:
                    return
                time.sleep(3)
                response = client.describe_vpc_attribute_with_options(request, runtime)
                vpc = response.body

    @staticmethod
    @lru_cache(maxsize=None)
    def describeUbuntuImage(region_id: str) -> str:
        """
        describe ubuntu image
        @param: region_id
        @return: ubuntu image_id
        """
        config = SimpleClient.Config(f"ecs.{region_id}")
        client = EcsClient(config)
        runtime = util_models.RuntimeOptions()

        request = ecs_models.DescribeImagesRequest(
            region_id=region_id, status="Available", image_family="acs:ubuntu_22_04_x64"
        )
        response = client.describe_images_with_options(request, runtime)
        return response.body.images.image[0].image_id


if __name__ == "__main__":
    # pass
    
    # regs = SimpleClient.describeRegionsWithCondition(sys.argv[1])
    # # sys.maxsize
    # xs = SimpleClient.comparePrice(SimpleClient.describeAvailableInstances(regs), 2, 5)
    # for x in xs:
    #     print(x)
    # SimpleClient.createInstance(xs[0]["region_id"], xs[0]["zone_id"], xs[0]["instance_type"], xs[0]["disk_category"], 2)

    # SimpleClient.describeUbuntuImage.cache_clear()
    # SimpleClient.describeInstanceAttribute(sys.argv[1])

    SimpleClient.deleteInstance('i-bp13g9asdcj538lodxq8')
