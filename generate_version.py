from setuptools_scm import get_version

print(f"""def get_version() -> str:
    return "{get_version()}"


def get_version_human() -> str:
    return "0.1.0-preview1"
""")
