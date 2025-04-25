from setuptools import setup, find_packages
import os
import io

# Check if omblepy-main directory exists
omblepy_path = os.path.join(os.path.dirname(__file__), 'omblepy-main')
if not os.path.exists(omblepy_path):
    print("Warning: omblepy-main directory not found. Please run:")
    print("git clone https://github.com/userx14/omblepy.git omblepy-main")

# Read README with proper encoding
def read_file(fname):
    with io.open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8') as f:
        return f.read()

setup(
    name="bp-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "xlsxwriter>=3.1.0",
        "colorama>=0.4.6",
        "bleak>=0.21.1",
        "terminaltables>=3.1.10",
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="Tools for analyzing and processing CSV data",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bp-tools",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # Add the omblepy-main directory to the package data
    package_data={
        '': ['omblepy-main/*'],
    },
) 