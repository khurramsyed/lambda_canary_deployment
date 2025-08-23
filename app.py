#!/usr/bin/env python3

import aws_cdk as cdk

from lambda_canary_workshop.lambda_canary_workshop_stack import LambdaCanaryWorkshopStack


app = cdk.App()
LambdaCanaryWorkshopStack(app, "LambdaCanaryWorkshopStack")

app.synth()
