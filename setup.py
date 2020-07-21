#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read()

requirements = requirements.split("\n")

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='rugby',
    description="A simple interface to rugby data.",
    long_description=readme + '\n\n' + history,
    author="Daniel Williams",
    author_email='mail@daniel-williams.co.uk',
    url='https://github.com/transientlunatic/',
    packages=find_packages(),
    use_scm_version=True,
    setup_requires=['setuptools_scm', 'click'],
    # package_dir={
    #     'rugby': 'rugby'
    # },
    include_package_data=True,
    install_requires=requirements,
    entry_points='''
        [console_scripts]
        rugby=rugby.scripts.cli:rugbycli
        rugbyapi=rugby.scripts.api:app
    ''',
    license="ISCL",
    zip_safe=False,
    keywords='rugby, sport',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
    tests_require=test_requirements
)

