from typing import Final

from setuptools_scm import get_version

HUMAN_VERSION: Final = "0.1.0rc1"

print(f"""def get_version() -> str:
    return "{get_version()}"


def get_version_human() -> str:
    return "{HUMAN_VERSION}"


if __name__ == "__main__":
    print(get_version_human())
""")
