from setuptools import setup, find_packages

setup(
    name="watchdog-tui",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "watchdog_tui.ui": ["styles.tcss"],
    },
    install_requires=[
        "textual>=0.70.0",
        "docker>=7.0.0",
        "psutil>=5.9.0",
        "rich>=13.0.0",
        "humanize>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "watchdog = watchdog_tui.cli:main",
            "watchdog-tui = watchdog_tui.cli:main",
        ],
    },
)
