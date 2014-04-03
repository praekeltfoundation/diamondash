from setuptools import setup, find_packages

from os import walk, path


def listify(filename):
    return filter(None, open(filename, 'r').read().split('\n'))


def files_in_dir(package, rootdir):
    """Lists the files in `package/rootdir` recursively"""
    list = []
    rootdir = path.join(package, rootdir)
    for root, subdirs, files in walk(rootdir):
        for file in files:
            filepath = path.relpath(path.join(root, file), package)
            list.append(filepath)
    return list


def parse_requirements(filename):
    install_requires = []
    dependency_links = []
    for requirement in listify(filename):
        if requirement.startswith("https:") or requirement.startswith("http:"):
            (_, _, name) = requirement.partition('#egg=')
            install_requires.append(name)
            dependency_links.append(requirement)
        else:
            install_requires.append(requirement)
    return install_requires, dependency_links


install_requires, dependency_links = parse_requirements(
    "requirements.pip")

setup(
    name="diamondash",
    version="0.3.5",
    url='https://github.com/praekelt/diamondash',
    license='BSD',
    description="A dashboard frontend for Graphite",
    long_description=open('README.md', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekeltfoundation.org',
    packages=find_packages() + ['twisted.plugins'],
    package_data={
        'diamondash': [
            'templates/*.xml',
        ] + files_in_dir('diamondash', 'static'),
        'twisted.plugins': ['twisted/plugins/*.py'],
    },
    install_requires=install_requires,
    #dependency_links=dependency_links,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
    ],
)
