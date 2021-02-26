from setuptools import setup, find_packages

packages = find_packages(where='src',
                         # exclude=['*.tests',
                         #        '*.tests.*']
                         )

print("packages found:", packages)

setup(name='structdbrest',
      version='0.0.1',
      author="Yury Lysogorskiy",
      author_email='yury.lysogorskiy@rub.de',
      description='REST API interface to atomistictools.org website',
      # tell setuptools to look for any packages under 'src'
      packages=packages,

      package_dir={'': 'src'},

      zip_safe=True,
      install_requires=['ase>=3.18', 'pandas', 'requests', 'numpy'],
      )
