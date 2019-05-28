import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="octopus",
    version="0.2",
    author="Richard Ingham",
    description="Real-time laboratory automation and monitoring in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/richardingham/octopus",
    packages=['octopus'],
    install_requires=[
        'twisted',
        'numpy',
        'scipy',
        'pyserial',
        'crc16',
    ],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
