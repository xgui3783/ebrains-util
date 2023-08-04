from setuptools import setup, find_packages

setup(
    name="ebrains-dataproxy-sync",
    version="0.0.1",
    author="Xiao Gui",
    author_email="xgui3783@gmail.com",
    description="ebrains util",
    packages=find_packages(include=["ebrains_util"]),
    python_requires=">=3.7",
    install_requires=[
        "ebrains_iam",
        "ebrains_dataproxy_sync",
        "ebrains-kg-snap",
    ],
    dependency_links=[
        "git+https://github.com/xgui3783/ebrains-kg-snap.git#egg=ebrains-kg-snap",
        "git+https://github.com/xgui3783/ebrains_dataproxy_sync.git#egg=ebrains_dataproxy_sync",
        "git+https://github.com/xgui3783/ebrains-iam-util.git#egg=ebrains_iam"
    ]
)
