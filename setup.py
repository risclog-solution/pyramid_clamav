import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

install_requires = [
    'pyramid>=1.3',
    'mock',
    'clamd'
    ]

setup(name='pyramid_clamav',
      version='0.9',
      description=('A tween checking file uploads for viruses using clamav.'),
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: Repoze Public License",
        ],
      keywords='wsgi pylons pyramid clamav virus',
      author=("RiscLOG Solution Gmbh",),
      author_email="info@risclog.de",
      url="https://github.com/risclog-solution/pyramid_clamav",
      license="BSD",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require={
        'test': [
          'pytest',
          'pytest-platform-markers',
        ]
      },
      entry_points='',
      )
