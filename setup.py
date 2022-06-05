from setuptools import find_packages, setup

setup(
    name="castanets",
    version="1.0.0",
    description="Tool for Multi-stage Review Process",
    install_requires=[
        "python-dotenv",
        "PyYAML",
        "requests",
        "pydantic",
        "inflection",
        "jinja2",
        "jinja2-time",
        "slack_sdk",
        "markdown",
        "importlib_metadata",
    ],
    url="https://github.com/team-castanets/castanets.git",
    author="Castanets",
    author_email="sunghwan@scatterlab.co.kr",
    packages=find_packages(exclude=["tests"]),
)
