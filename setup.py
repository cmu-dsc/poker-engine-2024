from setuptools import setup, find_packages

setup(
    name="pokerbot-protocols",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "grpcio",
        "grpcio-tools",
    ],
)
