import os, os.path
import shutil

import setuptools

# This is a big hack, but I can't think of a better solution here
if os.path.isfile('../README.md') and not os.path.isfile('./README.md'):
    shutil.copy('../README.md', './README.md')
if os.path.isfile('../libimagequant/libimagequant.c') and not os.path.isdir('./libimagequant_c'):
    shutil.copytree('../libimagequant', './libimagequant_c')

with open('./README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='libimagequant',
    version='2.14.1.0',
    author='RoadrunnerWMC, Kornel Lesiński',
    author_email='roadrunnerwmc@gmail.com',
    description='Unofficial Python bindings for libimagequant',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/RoadrunnerWMC/libimagequant-python',
    packages=setuptools.find_packages(),
    python_requires='>=3.5',
    setup_requires=[
        'cffi>=1.0.0'
    ],
    cffi_modules=[
        'build_cffi.py:ffibuilder',
    ],
    install_requires=[
        'cffi>=1.0.0',
    ],
    classifiers=[
        'Programming Language :: C',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Multimedia :: Graphics',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    ],
)
