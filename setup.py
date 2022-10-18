import os

from setuptools import find_packages, setup

VERSION = __import__('herald').__version__


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


install_requires = [
    'django>=3.2',
    'six',
    'jsonpickle',
]
dev_requires = [
    'pytz',
]
twilio_requires = [
    'twilio',
]
html2text_requires = [
    'html2text',
]

setup(
    name='django-herald',
    version=VERSION,
    author='Worthwhile',
    author_email='devs@worthwhile.com',
    install_requires=install_requires,
    extras_require={
        'dev': install_requires + dev_requires,
        'twilio': twilio_requires,
        'html2text': html2text_requires,
    },
    packages=find_packages(include=('herald', 'herald.*')),
    include_package_data=True,  # declarations in MANIFEST.in
    license='MIT',
    url='https://github.com/worthwhile/django-herald/',
    download_url='https://github.com/worthwhile/django-herald/tarball/'+VERSION,
    description="Django library for separating the message content from transmission method",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    keywords=['django', 'notifications', 'messaging'],
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
    ],
)
