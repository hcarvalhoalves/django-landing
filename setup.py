import ez_setup
ez_setup.use_setuptools()
from setuptools import setup

setup(
    name = "django-landing",
    version = "0.1",
    packages = ['landing'],
    author = "Henrique Carvalho Alves",
    author_email = "hcarvalhoalves@gmail.com",
    description = "Landing, a simple A/B testing application for Django",
    url = "http://github.com/hcarvalhoalves/django-landing",
    include_package_data = True,
    package_data = {'landing': ['templates/*']},
)
