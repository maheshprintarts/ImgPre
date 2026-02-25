from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ImgPre",
    version="1.0.0",
    author="maheshprintarts",
    description="Perceptual Image Preprocessor — intelligently resizes images based on sharpness",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/maheshprintarts/ImgPre",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "Pillow>=9.0.0",
        "opencv-python>=4.5.0",
        "numpy>=1.21.0",
    ],
    entry_points={
        "console_scripts": [
            "imgpre=ImgPre.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics",
    ],
)
