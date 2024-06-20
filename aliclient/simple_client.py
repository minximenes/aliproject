import asyncio
import os
import sys

from typing import List

from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_tea_openapi import models as openapi_models
from alibabacloud_tea_util import models as util_models

class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> EcsClient:
        # environment
        config = openapi_models.Config(
            access_key_id = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID'),
            access_key_secret = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
            # https://api.aliyun.com/product/Ecs
            # ecs.cn-hongkong.aliyuncs.com
            # ecs.us-west-1.aliyuncs.com
            endpoint = 'ecs.cn-chengdu.aliyuncs.com'
        )
        return EcsClient(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        # create ecs client
        client = Sample.create_client()
        request = ecs_models.ModifySecurityGroupRuleRequest(
            region_id = 'your_value'
        )
        options = util_models.RuntimeOptions(
            read_timeout = 10000,
            connect_timeout = 5000
        )
        try:
            response = client.modify_security_group_rule_with_options(request, options)
            print(response.body)
        except Exception as error:
            print(error.message)

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        # create ecs client
        client = Sample.create_client()
        request = ecs_models.ModifySecurityGroupRuleRequest(
            region_id = 'your_value'
        )
        options = util_models.RuntimeOptions(
            read_timeout = 10000,
            connect_timeout = 5000
        )
        try:
            response = await client.modify_security_group_rule_with_options_async(request, options)
            print(response.body)
        except Exception as error:
            print(error.message)

if __name__ == '__main__':
    Sample.main(sys.argv[1:])
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(Sample.main_async(sys.argv[1:]))
