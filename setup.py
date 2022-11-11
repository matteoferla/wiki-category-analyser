from setuptools import setup, find_packages
from warnings import warn
from importlib import util
import os

import os
this_directory = os.path.abspath(os.path.dirname(__file__))

if os.path.exists(os.path.join(this_directory, 'README.md')):
    with open(os.path.join(this_directory, 'README.md'), 'r') as f:
        long_description = f.read()
else:
    long_description = ''

if os.path.exists(os.path.join(this_directory, 'requirements.txt')):
    with open(os.path.join(this_directory, 'requirements.txt'), 'r') as f:
        requirements = [line.split('#')[0].strip() for line in f.readlines()]
        requirements = [line for line in requirements if line]
else:
    requirements = ['requests', 'wikitextparser', 'pageviewapi']

setup(
    name='Wiki-Category-Analyser',
    version='0.1',
    description='Mining info within infoboxes in wikipedia articles for a given category',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.7',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    url='https://github.com/matteoferla/wiki-category-analyser',
    license='MIT',
    author='Matteo Ferla',
    author_email='matteo.ferla@gmail.com',
    classifiers=[  # https://pypi.org/classifiers/
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
