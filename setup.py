import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jeffreyca-xumx",
    version="0.1.0",
    author="JeffreyCA",
    author_email="jeffreyca16@gmail.com",
    description="Unofficial NNabla implementation of CrossNet-Open-Unmix (X-UMX), originally created by Sony Research AI.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JeffreyCA/xumx",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'lameenc==1.2.2',
        'musdb==0.3.1',
        'museval==0.3.0',
        'requests>=2.22',
        'scipy>=1.3.1',
        'setuptools>=41.0.0',
        'norbert>=0.2.1',
        'resampy==0.2.2',
        'nnabla',
        'pydub'
    ],
    python_requires='>=3.6',
)
