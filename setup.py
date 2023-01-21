from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as fd:
	long_desc = fd.read()

setup(
	name='lib2cubs-lowlevel-com',
	version='1.1.0',
	author='Ivan Ponomarev',
	author_email='pi@spaf.dev',
	description='2cubs low-level communication library',
	long_description=long_desc,
	long_description_content_type='text/markdown',
	url='https://github.com/2cubs/lib2cubs-lowlevel-com',
	packages=find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GPL-3",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.8',
)
