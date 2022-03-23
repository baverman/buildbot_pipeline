from setuptools import setup

setup(
    name='buildbot_pipeline',
    version='0.9',
    url='https://github.com/baverman/buildbot_pipeline/',
    license='MIT',
    author='Anton Bobrov',
    author_email='baverman@gmail.com',
    description='Pipeline syntax for buildbot',
    long_description=open('README.rst', 'rb').read().decode('utf-8'),
    long_description_content_type='text/x-rst',
    packages=['buildbot_pipeline'],
    install_requires=['covador'],
    python_requires='>=3.6',
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ]
)
