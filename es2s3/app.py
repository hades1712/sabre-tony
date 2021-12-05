#!/usr/bin/env python3

from aws_cdk import core
from es2s3.es2s3_stack import Es2S3Stack
import yaml

f = open('./app-config.yml', 'r')
confMap = yaml.safe_load(f)['es2s3']
f.close()

env_US = core.Environment(account=confMap['account'], region=confMap['region'])
app = core.App()
Es2S3Stack(app, "es2s3", confMap, env=env_US)

app.synth()
