# #!/usr/bin/env python3

# from aws_cdk import core
# from infra.database import WealthDatabaseStack
# from infra.server import WealthServerStack
# from infra.vpc import WealthVpcStack

# app = core.App()


# # vpc_stack = WealthVpcStack(app, "WealthVpcStack")
# # database_stack = WealthDatabaseStack(app, "WealthDatabaseStack", vpc=vpc_stack.vpc)
# # server_stack = WealthServerStack(
# #     app,
# #     "WealthServerStack",
# #     vpc=vpc_stack.vpc,
# #     db=database_stack.db,
# #     db_security_group=database_stack.security_group,
# #     db_user=database_stack.user,
# # )
# # server_stack = WealthServerStack()
# # app.synth()
