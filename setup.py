import setuptools
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="congo-lab",
    version="0.7.9",
    author="Richard Ingham, Gary Short",
    description="Real-time laboratory automation and monitoring in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gar-syn/congo-lab",
    packages=find_packages(where='src', exclude=['*.test']),
    package_dir={'': 'src'},
    install_requires=requirements,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
