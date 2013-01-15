#!/usr/bin/env python

from sys import argv
from os import walk, path
from pkg_resources import resource_string

from bs4 import BeautifulSoup


def get_dir_files(dir, includes=[], excludes=[]):
    results = []
    for root, dirs, files in walk(dir):
        for file in files:
            filepath = path.join(root, file)
            matched_includes = [i for i in includes if i in filepath]
            if not matched_includes:
                continue

            matched_excludes = [e for e in excludes if e in filepath]
            if matched_excludes:
                continue

            results.append(filepath)

    return results


def insert_scripts(soup, placeholder, scripts):
    for s in scripts:
        tag = soup.new_tag('script', src=s)
        placeholder.append(tag)
    placeholder.unwrap()


def main():
    project_path = argv[1]
    soup = BeautifulSoup(resource_string(__name__, 'tests.template.html'))

    scripts_placeholder = soup.find(id='scripts-placeholder')
    scripts = get_dir_files(project_path, ['.js'],
                            ['vendor', '.test.js', '.swp'])
    insert_scripts(soup, scripts_placeholder, scripts)

    tests_placeholder = soup.find(id='tests-placeholder')
    tests = get_dir_files(project_path, ['test.js', '.swp'])
    insert_scripts(soup, tests_placeholder, tests)

    print soup

if __name__ == '__main__':
    main()
