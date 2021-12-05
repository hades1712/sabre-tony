from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_ec2 as ec2
)


class Es2S3Stack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, confMap: dict, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        '''This stack will deploy 2 lambda functions inside a vpc,
           to manage the ES cluster snapshot repo, and indices lifecycle
        '''
        # create an s3 bucket
        bucket = s3.Bucket(self, 'es-s3-repo', bucket_name=confMap['s3']['bucket_name'])

        # create an iam role to allow ES cluster operate the s3 bucket
        es_s3_role = iam.Role(self, 'es-s3-role',
                              assumed_by=iam.ServicePrincipal('es.amazonaws.com')
                              )
        # create policies
        s3_list_bucket_policy = iam.PolicyStatement(actions=["s3:ListBucket"],
                                                    resources=[bucket.bucket_arn]
                                                    )
        s3_object_policy = iam.PolicyStatement(actions=["s3:GetObject",
                                                        "s3:PutObject",
                                                        "s3:DeleteObject",
                                                        "iam:PassRole"],
                                               resources=[bucket.bucket_arn + '/*']
                                               )
        es_iam_policy = iam.PolicyStatement(actions=["iam:PassRole"],
                                            resources=[es_s3_role.role_arn]
                                            )
        es_s3_role.add_to_policy(s3_list_bucket_policy)
        es_s3_role.add_to_policy(s3_object_policy)
        es_s3_role.add_to_policy(es_iam_policy)

        # create a lambda execution role to access ES cluster
        lambda_es_role = iam.Role(self, 'lambda-es-role',
                                  assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
                                  )
        # allow lambda to operate ES clusters
        es_http_policy = iam.PolicyStatement(actions=['es:ES*'],
                                             resources=['*']
                                             )
        # allow lambda to publish logs to cloudwatch
        lambda_log_policy = iam.PolicyStatement(actions=["logs:CreateLogGroup",
                                                         "logs:CreateLogStream",
                                                         "logs:PutLogEvents"
                                                         ],
                                                resources=["*"]
                                                )
        # allow lambda to assume any role
        lambda_iam_policy = iam.PolicyStatement(actions=['iam:PassRole',
                                                         'iam:GetRole'],
                                                resources=["*"]
                                                )
        # allow lambda to deploy inside a vpc
        lambda_ec2_policy = iam.PolicyStatement(actions=["ec2:CreateNetworkInterface",
                                                         "ec2:DeleteNetworkInterface",
                                                         "ec2:DescribeNetworkInterfaces",
                                                         "ec2:ModifyNetworkInterfaceAttribute",
                                                         "ec2:DescribeSecurityGroups",
                                                         "ec2:DescribeSubnets",
                                                         "ec2:DescribeVpcs"],
                                                resources=['*']
                                                )
        lambda_es_role.add_to_policy(es_http_policy)
        lambda_es_role.add_to_policy(lambda_log_policy)
        lambda_es_role.add_to_policy(lambda_iam_policy)
        lambda_es_role.add_to_policy(lambda_ec2_policy)

        cur_vpc = ec2.Vpc.from_lookup(self, 'es-vpc', vpc_id=confMap['vpc']['vpc_id'])
        cur_sg = ec2.SecurityGroup.from_security_group_id(self, 'es-sg',
                                                          security_group_id=confMap['vpc']['security_group_id'])

        register_repo = _lambda.Function(self, 'register-repo',
                                         runtime=_lambda.Runtime.PYTHON_3_7,
                                         code=_lambda.Code.asset('lambda'),
                                         handler='register_repo.handler',
                                         environment={
                                             'ES_REPO_NAME': confMap['lambda']['es_repo_name'],
                                             'S3_BUCKET_NAME': bucket.bucket_name,
                                             'IAM_ROLE_ARN': es_s3_role.role_arn,
                                             'HOST': confMap['lambda']['es_endpoint'],
                                             'REGION': confMap['region']
                                         },
                                         role=lambda_es_role,
                                         vpc=cur_vpc,
                                         security_group=cur_sg
                                         )

        manage_indices = _lambda.Function(self, 'manage-indices',
                                          runtime=_lambda.Runtime.PYTHON_3_7,
                                          code=_lambda.Code.asset('lambda'),
                                          handler='manage_indices.handler',
                                          environment={
                                              'ES_REPO_NAME': confMap['lambda']['es_repo_name'],
                                              'S3_BUCKET_NAME': bucket.bucket_name,
                                              'IAM_ROLE_ARN': es_s3_role.role_arn,
                                              'HOST': confMap['lambda']['es_endpoint'],
                                              'REGION': confMap['region'],
                                              'ES_INDEX_PREFIX': confMap['lambda']['es_index_prefix'],
                                              'SNAPSHOT_RETENTION': confMap['lambda']['snapshot_retention'],
                                              'INDEX_RETENTION': confMap['lambda']['index_retention'],
                                          },
                                          role=lambda_es_role,
                                          vpc=cur_vpc,
                                          security_group=cur_sg
                                          )

