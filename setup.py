from setuptools import setup, find_packages

setup(
    name="ebrains-util",
    version="0.0.1",
    author="Xiao Gui",
    author_email="xgui3783@gmail.com",
    description="ebrains util",
    packages=find_packages(include=["ebrains_util", "ebrains_util.*"]),
    py_modules=['ebrains_util'],
    python_requires=">=3.7",
    install_requires=[
        "ebrains_iam @ git+https://github.com/xgui3783/ebrains-iam-util.git@8411752baeb002535c27aeeb26effa6b9c68f2fe",
        "ebrains-dataproxy-sync @ git+https://github.com/xgui3783/ebrains_dataproxy_sync.git@fa4d741a065e5291ce732d43060fe062f9bfc1dc",
        "ebrains_kg_snap @ git+https://github.com/xgui3783/ebrains-kg-snap.git",
        "ebrains_ingestion @ git+https://github.com/xgui3783/ebrains-ingestion.git",
        "click",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "ebrains_util = ebrains_util:cli"
        ]
    }
)
