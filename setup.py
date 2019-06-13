import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='hueyx',
    version='1.0.0.dev1',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',  # example license
    description='Django huey extension which supports multiple huey queues.',
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/Sebubu/hueyx',
    author='Severin Bühler',
    author_email='severin.buehler@apgsga.ch',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'cached-property',
        'huey',
        'redis',
        'python-redis-lock',
        'uwsgi'
    ]
)
