import setuptools

with open('README.md', 'r') as readme:
    long_description = readme.read()

setuptools.setup(
    name='yang2owl',
    version='0.1',
    scripts=[],
    author='Davide Loconte',
    author_email='davide.loconte@hotmail.it',
    description='Convert yang_modules models to owl ontologies',
    long_description_content_type='text/markdown',
    long_description=long_description,
    url='',
    packages=setuptools.find_packages,
    classifiers=[]
)
