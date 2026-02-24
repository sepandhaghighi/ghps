# -*- coding: utf-8 -*-
"""Setup module."""
from typing import List
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_requires() -> List[str]:
    """Read requirements.txt."""
    requirements = open("requirements.txt", "r").read()
    return list(filter(lambda x: x != "", requirements.split()))


def read_description() -> str:
    """Read README.md and CHANGELOG.md."""
    try:
        with open("README.md") as r:
            description = "\n"
            description += r.read()
        with open("CHANGELOG.md") as c:
            description += "\n"
            description += c.read()
        return description
    except Exception:
        return '''Ghps is a minimal, zero-dependency GitHub Pages simulator written in pure Python for local development and testing.
        It accurately replicates GitHub Pages' static hosting behavior, including proper 404.html handling, project base path simulation,
        strict routing mode, and optional cache control - all while remaining lightweight, fast, and usable both as a CLI tool and as an importable Python library.'''


setup(
    name='ghps',
    packages=['ghps'],
    version='0.1',
    description='Ghps: A Minimal GitHub Pages Simulator for Local Development',
    long_description=read_description(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    author='Sepand Haghighi',
    author_email='me@sepand.tech',
    url='https://github.com/sepandhaghighi/ghps',
    download_url='https://github.com/sepandhaghighi/ghps/tarball/v0.1',
    keywords="github gh-pages static-server static-hosting development server local http simulator testing cli python",
    project_urls={
        'Source': 'https://github.com/sepandhaghighi/ghps'
    },
    install_requires=get_requires(),
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Topic :: Utilities',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Build Tools',
    ],
    license='MIT',
    entry_points={
        'console_scripts': [
            'ghps = ghps.cli:main',
        ]}
)
