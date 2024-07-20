"""Bump_build.py"""
import configparser
import os
import shutil
import subprocess
import toml

def main():
    """Main function"""
    # Read the current version from pyproject.toml
    with open('pyproject.toml', 'r', encoding="ascii") as f:
        pyproject = toml.load(f)
        current_version = pyproject['tool']['poetry']['version']

    # Update the current_version in .bumpversion.cfg
    config = configparser.ConfigParser()
    config.read('.bumpversion.cfg')
    config['bumpversion']['current_version'] = current_version

    with open('.bumpversion.cfg', 'w', encoding="ascii") as configfile:
        config.write(configfile)

    # Bump version
    subprocess.check_call(['poetry', 'run', 'bumpversion', 'patch', '--allow-dirty'])

    # Remove the dist directory if it exists
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # Build the package
    subprocess.check_call(['poetry', 'build'])

if __name__ == "__main__":
    main()
