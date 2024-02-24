from setuptools import setup, find_packages

VERSION = '2024.02.25-post3'
DESCRIPTION = 'A Python package for searching apps in Apkpure'

setup(
    name="py-apkpure",
    version=VERSION,
    author="Anhy Krishna Fitiavana",
    author_email="fitiavana.krishna@gmail.com",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=['requests', 'bs4', 'lxml'],
    keywords=['python', 'apkpure', 'scraping'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)