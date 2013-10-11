from setuptools import setup, find_packages

setup(
    name='django-device-notifications',
    version='0.0.1',
    description='Generic library for APN & GCM notifications',
    author='Johann Heller',
    author_email='johann@rover.com',
    url='https://github.com/roverdotcom/django-device-notifications',
    packages=find_packages(exclude=('tests', 'docs'))
)
