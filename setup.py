"""setup.py"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="meteo_lt",
    version="0.1.5",
    description="A library to fetch weather data from api.meteo.lt",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Brunas",
    author_email="brunonas@gmail.com",
    url="https://github.com/Brunas/meteo_lt-pkg",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
