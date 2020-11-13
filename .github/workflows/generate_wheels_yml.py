
yml = []

# NOTE:
# The below notice applies to the generated
yml.append("""
name: Build and test
on: [push]

jobs:
""")

PLATFORMS = ['windows', 'macos', 'ubuntu']
PYTHON_BUILD_VERSIONS = [(3,5), (3,6), (3,7), (3,8), (3,9)]
PYTHON_TEST_VERSIONS = [(3,5), (3,6), (3,7), (3,8), (3,9)]


def strings_for(version_tuple):
    pyver_str_dot = '.'.join(str(x) for x in pyver)
    pyver_str_none = ''.join(str(x) for x in pyver)

    if platform == 'ubuntu':
        if pyver >= (3,8):
            py_cmd = f'/opt/python/cp{pyver_str_none}-cp{pyver_str_none}/bin/python'
        else:
            py_cmd = f'/opt/python/cp{pyver_str_none}-cp{pyver_str_none}m/bin/python'
    else:
        py_cmd = 'python'

    return pyver_str_dot, pyver_str_none, py_cmd


def add_build(platform, version):
    pyver_str_dot, pyver_str_none, py_cmd = strings_for(pyver)

    def only_on(platform_2, text):
        return text if (platform == platform_2) else ''

    def only_on_not(platform_2, text):
        return text if (platform != platform_2) else ''

    yml.append(f"""
  build-{platform}-{pyver_str_none}:

    runs-on: {platform}-latest
    {only_on('ubuntu', 'container: quay.io/pypa/manylinux2014_x86_64')}

    steps:
    - uses: actions/checkout@v2
    {only_on('windows', '- uses: ilammy/msvc-dev-cmd@v1')}
    {only_on_not('ubuntu', f'''
    - name: Set up Python {pyver_str_dot}
      uses: actions/setup-python@v2
      with:
        python-version: {pyver_str_dot}
    ''')}
    - name: Install dependencies
      run: |
        {py_cmd} -m pip install --upgrade pip
        {py_cmd} -m pip install --upgrade setuptools wheel cffi>=1.0.0 {only_on('ubuntu', 'auditwheel')}
    - name: Build
      shell: bash
      run: |
        cd bindings
        {py_cmd} setup.py bdist_wheel
        mv ./dist ../dist
    {only_on('ubuntu', f'''
    - name: Run auditwheel
      run: |
        mkdir dist/wheelhouse
        {py_cmd} -m auditwheel repair -w dist/wheelhouse/ dist/*.whl
        rm dist/*.whl
        mv dist/wheelhouse/* dist/
        rm -rf dist/wheelhouse
    ''')}
    - name: Upload artifacts
      uses: actions/upload-artifact@v1
      with:
        name: build-{platform}-{pyver_str_none}
        path: dist
    """)


def add_test(platform, version):
    pyver_str_dot, pyver_str_none, py_cmd = strings_for(pyver)

    def only_on(platform_2, text):
        return text if (platform == platform_2) else ''

    def only_on_not(platform_2, text):
        return text if (platform != platform_2) else ''

    yml.append(f"""
  test-{platform}-{pyver_str_none}:

    needs: build-{platform}-{pyver_str_none}
    runs-on: {platform}-latest

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python {pyver_str_dot}
      uses: actions/setup-python@v2
      with:
        python-version: {pyver_str_dot}
    - name: Download artifact
      uses: actions/download-artifact@v2
      with:
        name: build-{platform}-{pyver_str_none}
    - name: Install dependencies
      run: |
        {py_cmd} -m pip install --upgrade pip
        {py_cmd} -m pip install pytest
    - name: Install wheel
      shell: bash
      run: |
        {py_cmd} -m pip install *.whl
    - name: Test wheel with pytest
      run: |
        cd tests
        {py_cmd} -m pytest
    """)





for platform in PLATFORMS:
    for pyver in PYTHON_BUILD_VERSIONS:
        add_build(platform, pyver)
    for pyver in PYTHON_TEST_VERSIONS:
        add_test(platform, pyver)



# # Builds

# for platform in ['windows', 'macos']:
#     for pyver in PYTHON_BUILD_VERSIONS:
#         pyver_str_dot, pyver_str_none = strings_for(pyver)

#         is_ubuntu =

#         if platform == 'ubuntu':
#             if pyver >= (3,8):
#                 py_cmd = f'/opt/python/cp{pyver}-cp{pyver}/bin/python'
#             else:
#                 py_cmd = f'/opt/python/cp{pyver}-cp{pyver}m/bin/python'
#         else:
#             py_cmd = 'python'

#         # Build job
#         yml.append(f"""
#   build-{platform}-{pyver_str_none}:

#     runs-on: {platform}-latest
#     {"container: quay.io/pypa/manylinux2014_x86_64" if platform == "ubuntu" else ""}

#     steps:
#     - uses: actions/checkout@v2
#     - uses: ilammy/msvc-dev-cmd@v1
#     - name: Set up Python {pyver_str_dot}
#       uses: actions/setup-python@v2
#       with:
#         python-version: {pyver_str_dot}
#     - name: Install dependencies
#       run: |
#         python -m pip install --upgrade pip
#         pip install --upgrade setuptools wheel cffi>=1.0.0
#         {"pip install auditwheel" if platform == "ubuntu" else ""}
#     - name: Build
#       shell: bash
#       run: |
#         cd bindings
#         python setup.py bdist_wheel
#         mv ./dist ../dist
#     - name: Upload artifacts
#       uses: actions/upload-artifact@v1
#       with:
#         name: build-{platform}-{pyver_str_none}
#         path: dist
# """)


# for platform in ['windows', 'macos']:
#     for pyver in PYTHON_TEST_VERSIONS:
#         pyver_str_dot, pyver_str_none = strings_for(pyver)
#     for pyver in [(3,5), (3,6), (3,7), (3,8), (3,9)]:
#         pyver_str_dot = '.'.join(str(x) for x in pyver)
#         pyver_str_none = ''.join(str(x) for x in pyver)

#         if platform == 'ubuntu':
#             if pyver >= (3,8):
#                 py_cmd = f'/opt/python/cp{pyver}-cp{pyver}/bin/python'
#             else:
#                 py_cmd = f'/opt/python/cp{pyver}-cp{pyver}m/bin/python'
#         else:
#             py_cmd = 'python'

#         # Build job
#         yml.append(f"""
#   build-{platform}-{pyver_str_none}:

#     runs-on: {platform}-latest

#     steps:
#     - uses: actions/checkout@v2
#     - uses: ilammy/msvc-dev-cmd@v1
#     - name: Set up Python {pyver_str_dot}
#       uses: actions/setup-python@v2
#       with:
#         python-version: {pyver_str_dot}
#     - name: Install dependencies
#       run: |
#         python -m pip install --upgrade pip
#         pip install --upgrade setuptools wheel cffi>=1.0.0
#     - name: Build
#       shell: bash
#       run: |
#         cd bindings
#         python setup.py bdist_wheel
#         mv ./dist ../dist
#     - name: Upload artifacts
#       uses: actions/upload-artifact@v1
#       with:
#         name: build-{platform}-{pyver_str_none}
#         path: dist
# """)

#         # Test job
#         yml.append(f"""
#   test-{platform}-{pyver_str_none}:

#     needs: build-{platform}-{pyver_str_none}
#     runs-on: {platform}-latest

#     steps:
#     - uses: actions/checkout@v2
#     - name: Set up Python {pyver_str_dot}
#       uses: actions/setup-python@v2
#       with:
#         python-version: {pyver_str_dot}
#     - name: Download artifact
#       uses: actions/download-artifact@v2
#       with:
#         name: build-{platform}-{pyver_str_none}
#     - name: Install dependencies
#       run: |
#         python -m pip install --upgrade pip
#         python -m pip install pytest
#     - name: Install wheel
#       shell: bash
#       run: |
#         python -m pip install *.whl
#     - name: Test wheel with pytest
#       run: |
#         cd tests
#         python -m pytest
# """)

# # manylinuxes
# for pyver in ['35', '36', '37', '38', '39']:
#     # There seems to be no way (as of 2020-02-13) to accomplish this in the YAML
#     # (unlike in Azure Pipelines)
#     if pyver in ['38', '39']:
#         py_cmd = f'/opt/python/cp{pyver}-cp{pyver}/bin/python'
#     else:
#         py_cmd = f'/opt/python/cp{pyver}-cp{pyver}m/bin/python'

#     yml.append(f"""
#   manylinux_{pyver}_build:

#     runs-on: ubuntu-latest
#     container: quay.io/pypa/manylinux2014_x86_64

#     steps:
#     - uses: actions/checkout@v2
#     - name: Set up Python ${{{{ matrix.python-version }}}}
#       uses: actions/setup-python@v2
#       with:
#         python-version: ${{{{ matrix.python-version }}}}
#     - name: Install dependencies
#       run: |
#         {py_cmd} -m pip install --upgrade pip
#         {py_cmd} -m pip install --upgrade setuptools wheel auditwheel cffi>=1.0.0
#     - name: Build
#       run: |
#         cd bindings
#         {py_cmd} setup.py bdist_wheel
#     - name: Run auditwheel
#       run: |
#         cd bindings
#         mkdir dist/wheelhouse
#         {py_cmd} -m auditwheel repair -w dist/wheelhouse/ dist/*.whl
#         mv dist/wheelhouse ../dist
#         rm -rf dist
#     - name: Upload artifacts
#       uses: actions/upload-artifact@v1
#       with:
#         name: build-manylinux-{pyver}
#         path: dist

#   manylinux_{pyver}_test:

#     needs: manylinux_{pyver}_build
#     runs-on: ubuntu-latest
#     container: quay.io/pypa/manylinux2014_x86_64

#     steps:
#     - uses: actions/checkout@v2
#     - name: Set up Python ${{{{ matrix.python-version }}}}
#       uses: actions/setup-python@v2
#       with:
#         python-version: ${{{{ matrix.python-version }}}}
#     - name: Download artifact
#       uses: actions/download-artifact@v2
#       with:
#         name: build-manylinux-{pyver}
#     - name: Install dependencies
#       run: |
#         {py_cmd} -m pip install --upgrade pip
#         {py_cmd} -m pip install pytest
#     - name: Install wheel
#       run: |
#         {py_cmd} -m pip install *.whl
#     - name: Test wheel with pytest
#       run: |
#         {py_cmd} -m pip install pytest
#         cd tests
#         {py_cmd} -m pytest
# """)

# And finally, write the output file
with open('wheels.yml', 'w', encoding='utf-8') as f:
    f.write("""# THIS FILE IS AUTOGENERATED -- DO NOT EDIT DIRECTLY
# Edit the Python script in this same folder instead, and then run it to
# regenerate this file.
""")
    for line in ''.join(yml).splitlines():
        line = line.rstrip()
        if not line: continue
        f.write(line + '\n')
