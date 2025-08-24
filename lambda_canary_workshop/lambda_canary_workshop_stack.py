from datetime import datetime
from aws_cdk import Stack, RemovalPolicy
from constructs import Construct
from aws_cdk.aws_lambda import Function, Runtime, Code, Alias, VersionOptions
from aws_cdk.aws_apigateway import LambdaRestApi, StageOptions
from aws_cdk.aws_cloudwatch import Alarm, ComparisonOperator
from aws_cdk.aws_codedeploy import LambdaDeploymentGroup, LambdaDeploymentConfig
from cdk_nag import NagSuppressions



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
        api = LambdaRestApi(
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
        # Add cdk-nag suppressions
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            [
                f"/{self.stack_name}/MyLambdaFunction/ServiceRole/Resource",
                f"/{self.stack_name}/CanaryDeploymentGroup/ServiceRole/Resource"
            ],
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Using AWS managed policies is acceptable for this demo/development environment"
                }
            ]
        )

        NagSuppressions.add_resource_suppressions(
            api,
            [
                {
                    "id": "AwsSolutions-APIG2",
                    "reason": "Request validation not required for this demo API"
                }
            ]
        )

        NagSuppressions.add_resource_suppressions(
            api.deployment_stage,
            [
                {
                    "id": "AwsSolutions-APIG1",
                    "reason": "Access logging not required for this demo/development API"
                },
                {
                    "id": "AwsSolutions-APIG6",
                    "reason": "CloudWatch logging not required for this demo/development API"
                },
                {
                    "id": "AwsSolutions-APIG3",
                    "reason": "WAF integration not required for this demo/development API"
                }
            ]
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            [
                f"/{self.stack_name}/RestAPI/Default/{{proxy+}}/ANY/Resource",
                f"/{self.stack_name}/RestAPI/Default/ANY/Resource"
            ],
            [
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "Authorization not required for this demo/development API"
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "Cognito user pool not required for this demo/development API"
                }
            ]
        )

        NagSuppressions.add_resource_suppressions(
            my_lambda,
            [
                {
                    "id": "AwsSolutions-L1",
                    "reason": "Using specific runtime version for compatibility reasons"
                }
            ]
        )