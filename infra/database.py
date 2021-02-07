import json

from aws_cdk import core, aws_ec2 as ec2, aws_docdb as docdb, aws_secretsmanager as sm

from config2.config import config


class WealthDatabaseStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self._vpc = vpc

        sg = self.get_database_sg()
        user = self.create_database_user()
        db = self.create_db(sg, user)

        self.database = db
        self.user = user
        self.security_group = sg

    def get_database_sg(self) -> ec2.SecurityGroup:
        return ec2.SecurityGroup(self, "WealthDatabaseSecurityGroup", vpc=self._vpc)

    def create_database_user(self) -> sm.Secret:
        username = config.infra.database.user_name
        return sm.Secret(
            self,
            "WealthDatabaseUser",
            generate_secret_string=sm.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                password_length=20,
                generate_string_key="password",
                secret_string_template=json.dumps({"username": username}),
            ),
        )

    def create_db(
        self, sg: ec2.SecurityGroup, user: sm.Secret
    ) -> docdb.DatabaseCluster:
        cluster = docdb.DatabaseCluster(
            self,
            "WealthDatabaseCluster",
            instance_props=docdb.InstanceProps(
                vpc=self._vpc,
                security_group=sg,
                instance_type=ec2.InstanceType.of(
                    instance_class=ec2.InstanceClass.MEMORY5,
                    instance_size=ec2.InstanceSize.LARGE,
                ),
            ),
            instances=1,
            master_user=docdb.Login(
                username=config.infra.database.user_name,
                password=user.secret_value_from_json("password"),
            ),
        )
        return cluster