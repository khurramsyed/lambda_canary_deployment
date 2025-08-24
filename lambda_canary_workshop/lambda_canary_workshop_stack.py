from datetime import datetime
from aws_cdk import Stack, RemovalPolicy
from constructs import Construct
from aws_cdk.aws_lambda import Function, Runtime, Code, Alias, VersionOptions
from aws_cdk.aws_apigateway import LambdaRestApi, StageOptions
from aws_cdk.aws_cloudwatch import Alarm, ComparisonOperator
from aws_cdk.aws_codedeploy import LambdaDeploymentGroup, LambdaDeploymentConfig


class LambdaCanaryWorkshopStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        environmet_type = self.node.try_get_context("environmentType")
        context = self.node.try_get_context(environmet_type)

        self.alias_name = context["lambda"]["alias"]
        self.stage_name = context["lambda"]["stage"]

        current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        my_lambda = Function(
            scope=self,
            id="MyLambdaFunction",
            function_name=context["lambda"]["name"],
            runtime=Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=Code.from_asset("lambda"),
            current_version_options=VersionOptions(
                description=f"Version deployed on - {current_time}",
                removal_policy=RemovalPolicy.RETAIN,
                retry_attempts=1,
            ),
        )

        new_version = my_lambda.current_version
        new_version.apply_removal_policy(RemovalPolicy.RETAIN)

        # self.alias_name is coming from
        alias = Alias(
            scope=self,
            id="FuncitonAlias",
            alias_name=self.alias_name,
            version=new_version,
        )

        # This Rest API will use Lamba alias as handler and deploy to stage defined in contex
        LambdaRestApi(
            scope=self,
            id="RestAPI",
            description="This service serves the Lambda function.",
            handler=alias,
            deploy_options=StageOptions(stage_name=self.stage_name),
        )

        failure_alarm = Alarm(
            scope=self,
            id="FunctionFailureAlarm",
            metric=alias.metric_errors(),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Latest Deployment Failure Alarm > 0",
            alarm_name=f"{self.stack_name}-canary-alarm",
            comparison_operator=ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        )

        LambdaDeploymentGroup(
            scope=self,
            id="CanaryDeploymentGroup",
            alias=alias,
            deployment_config=LambdaDeploymentConfig.CANARY_10_PERCENT_5_MINUTES,
            alarms=[failure_alarm],
        )
