import setuptools

with open('../README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='libimagequant',
    version='2.12.5.0',
    author='RoadrunnerWMC, Kornel Lesiński',
    author_email='roadrunnerwmc@gmail.com',
    description='Unofficial Python bindings for libimagequant',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/RoadrunnerWMC/libimagequant-python',
    packages=setuptools.find_packages(),
    setup_requires=[
        'cffi>=1.0.0'
    ],
    cffi_modules=[
        'libimagequant/build_cffi.py:ffibuilder',
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
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Multimedia :: Graphics',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    ],
)
