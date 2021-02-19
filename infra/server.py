from aws_cdk import aws_apigateway as api_gw
from aws_cdk import aws_docdb as docdb
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_secretsmanager as sm
from aws_cdk import core
from config2.config import config


class WealthServerStack(core.Stack):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        # vpc: ec2.Vpc,
        # db: docdb.DatabaseCluster,
        # db_security_group: ec2.SecurityGroup,
        # db_user: sm.Secret,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = vpc

        repo = self.create_repo()
        lambda_lith = self.create_lambda(repo)
        gateway = self.create_gateway(lambda_lith)

    def create_repo(self) -> ecr.Repository:
        return ecr.Repository(self, "WealthServerRepo", repository_name="wealth-back-repo")

    def create_lambda(self, repo: ecr.Repository, db_user: sm.Secret):
        env = {**config.infra.get("lambda").env, "MONGO_DB_SECRET_NAME": db_user}
        lambda_lith = lambda_.Function(
            self,
            "WealthServerLambda",
            code=lambda_.Code.from_ecr_image(repo),
            environment=env,
        )

    def create_gateway(self, lambda_function: lambda_.Function) -> api_gw.LambdaRestApi:
        return api_gw.LambdaRestApi(self, "WealthServerAPI", handler=lambda_function)
