"""Run the existing offline suite against a clean, installed wheel."""

import os
import shutil
import subprocess
import tempfile
import venv
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    wheels = list((root / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("Build exactly one SDK wheel in dist before checking it")

    with tempfile.TemporaryDirectory(prefix="connectedpapers-wheel-") as temporary:
        directory = Path(temporary)
        environment = directory / "venv"
        venv.create(environment, with_pip=True)
        python = environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env["PYTHONNOUSERSITE"] = "1"

        def run(*arguments: str) -> None:
            subprocess.run(
                [str(python), *arguments], cwd=directory, env=env, check=True
            )

        run("-m", "pip", "install", "--upgrade", "pip")
        run(
            "-m",
            "pip",
            "install",
            str(wheels[0]),
            "--group",
            f"{root / 'pyproject.toml'}:test",
        )
        run("-m", "pip", "check")
        run(
            "-c",
            "from importlib import metadata, resources; "
            "from pathlib import Path; import sysconfig; import connectedpapers; "
            "package = Path(connectedpapers.__file__).resolve(); "
            "assert package.is_relative_to(Path(sysconfig.get_path('purelib')).resolve()); "
            "assert resources.files('connectedpapers').joinpath('py.typed').is_file(); "
            "dist = metadata.distribution('connectedpapers-py'); "
            "assert dist.metadata['Requires-Python'] == '>=3.11'; "
            "assert not any(r.lower().startswith('requests') for r in dist.requires or [])",
        )
        shutil.copytree(
            root / "tests",
            directory / "tests",
            ignore=shutil.ignore_patterns("__pycache__", "check_wheel.py"),
        )
        shutil.copyfile(root / "pyproject.toml", directory / "pyproject.toml")
        run("-m", "pytest", "-q", "tests")


if __name__ == "__main__":
    main()
