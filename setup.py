from setuptools import setup, find_packages

requires = [
    'coverage==4.0',
    'PyYAML==3.12',
    'unittest2==1.1.0',
    'six==1.10.0',
    'traceback2==1.4.0',
    'linecache2==1.0.0',
    'nose==1.3.7',
    'requests-futures==0.9.7',
    'requests==2.11.1',
    'futures==3.0.5',
    'parsel==1.0.3',
    'regex==2016.10.22'
]

tests_require = requires

setup(name='philcrawler',
      version='0.1',
      description='philosophy crawler app for moat interview',
      classifiers=[
          "Programming Language :: Python",
      ],
      author='Ven Karri',
      author_email='karri.ven@gmail.com',
      url='',
      keywords='moat coding exercise',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      install_requires=requires,
      tests_require=tests_require,
      )
