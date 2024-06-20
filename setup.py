# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


NAME = "ali openapi client"
PACKAGE = "aliclient"
VERSION = __import__(PACKAGE).__version__
AUTHOR = "ximenes"
AUTHOR_EMAIL = "min.ximenes@gmail.com"
DESCRIPTION = "a simple client for ali openapi"
REQUIRES = [
    "click",
    "alibabacloud_ecs20140526>=3.0.1, <4.0.0",
    "alibabacloud_tea_openapi>=0.3.8, <1.0.0",
    "alibabacloud_tea_util>=0.3.11, <1.0.0",
    "alibabacloud_darabonba_string>=0.0.1, <1.0.0",
    "alibabacloud_darabonba_env>=0.0.1, <1.0.0",
]

# command:
#     local:
#         pip3 install .
#         pip3 install -e .  # editable mode
#     pip:
#         python3 setup.py sdist bdist_wheel
#         twine upload dist/*
#         pip3 install aliclient
# include_package_data:
#     configure in MANIFEST.in
# console_scripts: 
#     executable_name = package_name.module_name:function_name
setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    packages=find_packages(exclude=["test*"]),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "ali = aliclient.main:run",
        ],
    },
    install_requires=REQUIRES,
    python_requires=">=3.6",
)