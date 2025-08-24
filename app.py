from aws_cdk import App, Environment, Aspects
from lambda_canary_workshop.lambda_canary_workshop_stack import (
    LambdaCanaryWorkshopStack,
)
from cdk_nag import AwsSolutionsChecks

app = App()

environment_type = app.node.try_get_context("environmentType")
environment_context = app.node.try_get_context(environment_type)
region = environment_context["region"]
account = app.node.try_get_context("account")
tags = environment_context["tags"]
stack_name = f"{app.node.try_get_context('prefix')}-{environment_type}"

LambdaCanaryWorkshopStack(
    app,
    stack_name,
    env=Environment(account=account, region=region),
    tags=tags,
)

Aspects.of(app).add(AwsSolutionsChecks())
app.synth()
