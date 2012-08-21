#!/usr/bin/env python

from setuptools import setup, find_packages

tests_require = [
    'Django>=1.2',
    'unittest2',
]

setup(
    name='django-perftools',
    version='0.7.2',
    author='DISQUS',
    author_email='opensource@disqus.com',
    url='http://github.com/disqus/django-perftools',
    description = '',
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    install_requires=[],
    license='Apache License 2.0',
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='unittest2.collector',
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)