import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="es2s3",
    version="0.0.1",

    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "es2s3"},
    packages=setuptools.find_packages(where="es2s3"),

    install_requires=[
        "aws-cdk.aws_iam==1.25.0",
        "aws-cdk.aws_s3==1.25.0",
        "aws-cdk.aws_lambda==1.25.0",
        "aws-cdk.aws_ec2==1.25.0",
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
