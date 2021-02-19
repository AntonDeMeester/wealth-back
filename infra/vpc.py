from aws_cdk import aws_ec2 as ec2
from aws_cdk import core
from config2.config import config


class WealthVpcStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = self.create_vpc()

    def create_vpc(self) -> ec2.Vpc:
        base_name = config.infra.vpc.name
        return ec2.Vpc(
            self,
            "WealthVpc",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                    name=f"{base_name}-public",
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE,
                    cidr_mask=24,
                    name=f"{base_name}-private",
                ),
            ],
        )
