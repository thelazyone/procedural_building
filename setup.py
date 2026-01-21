"""
Setup script for procedural_building package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="procedural_building",
    version="0.1.0",
    author="Your Name",
    description="A hierarchical, deterministic procedural building generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/procedural_building",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "shapely>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
        ],
        "viewer": [
            "pygame>=2.5.0",
            "PyOpenGL>=3.1.6",
            "pygame-gui>=0.6.9",
        ],
    },
)
