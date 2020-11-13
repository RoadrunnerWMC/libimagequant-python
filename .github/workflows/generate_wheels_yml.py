
yml = []

# NOTE:
# The below notice applies to the generated
yml.append("""
name: Build and test
on: [push]

jobs:
""")

PLATFORMS = ['windows', 'macos', 'ubuntu']
PYTHON_TEST_VERSIONS = [(3,5), (3,6), (3,7), (3,8), (3,9)]
PYTHON_BUILD_VERSION = PYTHON_TEST_VERSIONS[-1]
MANYLINUX_CONTAINER = 'quay.io/pypa/manylinux2014_x86_64'


def strings_for(pyver):
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


def add_build(platform, pyver):
    pyver_str_dot, pyver_str_none, py_cmd = strings_for(pyver)

    def only_on(platform_2, text):
        return text if (platform == platform_2) else ''

    def only_on_not(platform_2, text):
        return text if (platform != platform_2) else ''

    interpreter_tags = ' '.join(f'cp{a}{b}' for a, b in PYTHON_TEST_VERSIONS)

    yml.append(f"""
  build-{platform}:

    runs-on: {platform}-latest
    {only_on('ubuntu', f'container: {MANYLINUX_CONTAINER}')}

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
      run: |
        cd dist
        {py_cmd} ../.github/workflows/rename_wheel.py *.whl - {interpreter_tags}
    - name: Upload artifacts
      uses: actions/upload-artifact@v1
      with:
        name: build-{platform}
        path: dist
    """)


def add_test(platform, pyver):
    pyver_str_dot, pyver_str_none, py_cmd = strings_for(pyver)

    def only_on(platform_2, text):
        return text if (platform == platform_2) else ''

    def only_on_not(platform_2, text):
        return text if (platform != platform_2) else ''

    yml.append(f"""
  test-{platform}-{pyver_str_none}:

    needs: build-{platform}
    runs-on: {platform}-latest
    {only_on('ubuntu', f'container: {MANYLINUX_CONTAINER}')}

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python {pyver_str_dot}
      uses: actions/setup-python@v2
      with:
        python-version: {pyver_str_dot}
    - name: Download artifact
      uses: actions/download-artifact@v2
      with:
        name: build-{platform}
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
    add_build(platform, PYTHON_BUILD_VERSION)
    for pyver in PYTHON_TEST_VERSIONS:
        add_test(platform, pyver)



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
