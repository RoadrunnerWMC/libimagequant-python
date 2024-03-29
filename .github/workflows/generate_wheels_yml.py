# Script for auto-generating wheels.yml.

PLATFORMS = ['windows', 'macos', 'ubuntu']
CPYTHON_TEST_VERSIONS = [(3,6), (3,7), (3,8), (3,9), (3,10)]
CPYTHON_BUILD_VERSION = CPYTHON_TEST_VERSIONS[0]
MANYLINUX_CONTAINER = 'quay.io/pypa/manylinux2014_x86_64'


def strings_for(platform: str, pyver: tuple) -> (str, str, str):
    """
    Given a (major, minor) tuple (e.g. (3,7)), return three strings:
    - '3.7'
    - '37'
    - the appropriate command for calling that Python on the specified platform
    """
    pyver_str_dot = '.'.join(str(x) for x in pyver)
    pyver_str_none = ''.join(str(x) for x in pyver)

    if platform == 'ubuntu':
        # Use the Python installations provided by the manylinux container.
        # <3.8 have to be in the form "cpXY-cpXYm"; >=3.8 have to be in the form "cpXY-cpXY"
        if pyver >= (3,8):
            py_cmd = f'/opt/python/cp{pyver_str_none}-cp{pyver_str_none}/bin/python'
        else:
            py_cmd = f'/opt/python/cp{pyver_str_none}-cp{pyver_str_none}m/bin/python'
    else:
        py_cmd = 'python'

    return pyver_str_dot, pyver_str_none, py_cmd


def make_sdist_job(pyver: tuple) -> str:
    """
    Make a job that runs `setup.py sdist`
    """
    pyver_str_dot, pyver_str_none, _ = strings_for('ubuntu', pyver)
    # Ignore strings_for()'s py_cmd, since it gives us the one for the
    # manylinux container but we're just in a regular Ubuntu VM for this job
    py_cmd = 'python'

    return f"""
  sdist:

    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python {pyver_str_dot}
      uses: actions/setup-python@v2
      with:
        python-version: "{pyver_str_dot}"
    - name: Install dependencies
      run: |
        {py_cmd} -m pip install --upgrade pip
        {py_cmd} -m pip install --upgrade setuptools cffi>=1.0.0
    - name: Build
      shell: bash
      run: |
        cd bindings
        {py_cmd} setup.py sdist
        mv ./dist ../dist
    - name: Upload artifacts
      uses: actions/upload-artifact@v1
      with:
        name: sdist
        path: dist
    """


def make_build_job(platform: str, arch: int, pyver: tuple) -> str:
    """
    Make a build job for the specified platform and Python version
    """
    pyver_str_dot, pyver_str_none, py_cmd = strings_for(platform, pyver)

    def only_on(platform_2, text):
        return text if (platform == platform_2) else ''

    def only_on_not(platform_2, text):
        return text if (platform != platform_2) else ''

    interpreter_tags = ' '.join(f'cp{a}{b}' for a, b in CPYTHON_TEST_VERSIONS)

    return f"""
  build-{platform}-{arch}:

    runs-on: {platform}-latest
    {only_on('ubuntu', f'container: {MANYLINUX_CONTAINER}')}

    steps:
    - uses: actions/checkout@v2
    {only_on_not('ubuntu', f'''
    - name: Set up Python {pyver_str_dot}
      uses: actions/setup-python@v2
      with:
        python-version: "{pyver_str_dot}"
        architecture: {'x64' if arch == 64 else 'x86'}
    ''')}
    - name: Install dependencies
      run: |
        {py_cmd} -m pip install --upgrade pip
        {py_cmd} -m pip install --upgrade setuptools wheel packaging cffi>=1.0.0 {only_on('ubuntu', 'auditwheel')}
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
    - name: Rename wheel file
      shell: bash
      run: |
        cd dist
        {py_cmd} ../.github/workflows/rename_wheel.py *.whl - {interpreter_tags}
    - name: Upload artifacts
      uses: actions/upload-artifact@v1
      with:
        name: build-{platform}-{arch}
        path: dist
    """


def make_test_job(platform: str, arch: int, pyver: tuple) -> str:
    """
    Make a test job for the specified platform and Python version
    (tests both the built wheel and the sdist)
    """
    pyver_str_dot, pyver_str_none, py_cmd = strings_for(platform, pyver)

    def only_on(platform_2, text):
        return text if (platform == platform_2) else ''

    def only_on_not(platform_2, text):
        return text if (platform != platform_2) else ''

    return f"""
  test-{platform}-{arch}-{pyver_str_none}:

    needs: [build-{platform}-{arch}, sdist]
    runs-on: {platform}-latest
    {only_on('ubuntu', f'container: {MANYLINUX_CONTAINER}')}

    steps:
    - uses: actions/checkout@v2
    {only_on_not('ubuntu', f'''
    - name: Set up Python {pyver_str_dot}
      uses: actions/setup-python@v2
      with:
        python-version: "{pyver_str_dot}"
        architecture: {'x64' if arch == 64 else 'x86'}
    ''')}
    - name: Download build artifact
      uses: actions/download-artifact@v2
      with:
        name: build-{platform}-{arch}
    - name: Download sdist artifact
      uses: actions/download-artifact@v2
      with:
        name: sdist
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
    - name: Uninstall wheel and install sdist
      shell: bash
      run: |
        {py_cmd} -m pip uninstall -y libimagequant
        {py_cmd} -m pip install *.tar.gz
    - name: Test sdist with pytest
      run: |
        cd tests
        {py_cmd} -m pytest
    """


# YAML header
yml = ["""
name: Build and test
on: [push]

jobs:
"""]


# Make one build per platform (abi3),
# and perform one test per platform / Python version combo
yml.append(make_sdist_job(CPYTHON_BUILD_VERSION))
for arch in [32, 64]:
    for platform in PLATFORMS:
        if arch == 32 and platform != 'windows':
            # GHA actions/setup-python only provides 32-bit Python builds for Windows
            continue
        yml.append(make_build_job(platform, arch, CPYTHON_BUILD_VERSION))
        for pyver in CPYTHON_TEST_VERSIONS:
            yml.append(make_test_job(platform, arch, pyver))


# Write the output file
with open('wheels.yml', 'w', encoding='utf-8') as f:
    f.write("""################################################################
# THIS FILE IS AUTOGENERATED -- DO NOT EDIT DIRECTLY
# Edit the Python script in this same folder instead, and then run it to
# regenerate this file.
################################################################
""")

    for line in ''.join(yml).splitlines():
        line = line.rstrip()
        if not line: continue
        f.write(line + '\n')
