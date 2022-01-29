"""Dose GUI for TDD: test module for the shared resources module."""
from shutil import copytree, rmtree
from subprocess import Popen
import pkg_resources, pytest, sys, io
import setuptools

import dose
from dose import __version__, __author__
from dose.shared import get_shared, README, CHANGES, CONTRIBUTORS, LICENSE


# Workaround for old pytest (should only happen in Python 3.3 nowadays)
if pytest.__version__ < "3.9":
    from pathlib import Path
    @pytest.yield_fixture
    def tmp_path(tmpdir):
        yield Path(str(tmpdir))


class RaiserCall(Exception):
    pass


class TestGetShared(object):

    def test_get_setuptools_file_not_found_fallback(self, monkeypatch):
        prefix = "/tmp/tox_dose/some_path_that_doesnt_exist/"

        def put_prefix(requirement, relative_path):
            assert requirement.name == "dose"
            assert isinstance(requirement, pkg_resources.Requirement)
            return prefix + relative_path

        monkeypatch.setattr(pkg_resources, "resource_string", put_prefix)

        for name in ["subdir_doesnt_exist/README.rst",
                     "a file", ".something_hidden"]:
            assert get_shared(name) == "".join([prefix, "share/dose/v",
                                                __version__, "/", name])

    def test_get_without_setuptools(self, monkeypatch):
        def raiser(requirement, relative_path):
            raise RaiserCall("Attempt to call pkg_resources.resource_string")

        # Ensure the setuptools "pkg_resources.resource_string" isn't used,
        # given that tox always installs Dose via pip
        monkeypatch.setattr(pkg_resources, "resource_string", raiser)

        assert get_shared("README.rst").splitlines() == README
        assert get_shared("CHANGES.rst").splitlines() == CHANGES
        assert get_shared("CONTRIBUTORS.txt").splitlines() == CONTRIBUTORS
        assert get_shared("COPYING.txt").splitlines() == LICENSE.splitlines()

    def test_homebrew_shared_outside_cellar(self, monkeypatch):
        cellar_prefix = "/anywhere/in/Cellar/a/path/that/doesnt/exist"
        fake_prefix = "/anywhere/in"
        sys_prefix = sys.prefix
        monkeypatch.setattr(sys, "prefix", cellar_prefix)

        def fake_open(fname, mode="r", encoding="utf-8"):
            if fname.startswith(fake_prefix) and "Cellar" not in fname:
                fname = sys_prefix + fname[len(fake_prefix):]
                fake_open.was_called = True
            return io_open(fname, mode, encoding=encoding)

        fake_open.was_called = False
        io_open = io.open
        monkeypatch.setattr(io, "open", fake_open)

        self.test_get_without_setuptools(monkeypatch)
        assert fake_open.was_called # Ensure it tried to open outside Cellar

        with pytest.raises(RaiserCall): # Fallback: setuptools
            get_shared("This file doesn't exist.rst")

    def test_file_doesnt_exist(self, monkeypatch):
        resource_string_bkp = pkg_resources.resource_string

        def flag(requirement, relative_path):
            flag.was_called = True
            return resource_string_bkp(requirement, relative_path)

        flag.was_called = False
        monkeypatch.setattr(pkg_resources, "resource_string", flag)

        with pytest.raises(IOError):
            get_shared("a_file_that_doesnt_exist.txt")

        # Ensure the setuptools "pkg_resources.resource_string" is used
        assert flag.was_called

    def test_last_resort_get_source(self):
        dunder_init = get_shared("dose/__init__.py")
        assert '__version__ = "%s"' % __version__ in dunder_init

    def test_setup_py_wont_use_installed_readme(self, tmp_path):
        Path = type(tmp_path)
        dose_path = tmp_path / "rewritten-readme"
        copytree(str(Path(dose.__file__).parent.parent), str(dose_path))

        readme_filename = str(dose_path / "README.rst")
        with io.open(readme_filename, "w", encoding="utf-8") as readme:
            readme.write("\n".join([
                u"A title",
                u".. summary",
                u"A fake egg for testing Dose!",
                u".. summary end",
                u"An extra line just to TEST it!",
            ]))

        command = ["python", "setup.py", "egg_info"]
        Popen(command, cwd=str(dose_path)).communicate()
        pkg_info_filename = str(dose_path / "dose.egg-info" / "PKG-INFO")
        with io.open(pkg_info_filename, encoding="utf-8") as pkg_info:
            pkg_info_data = pkg_info.read()
        rmtree(str(dose_path))

        assert u"Summary: A fake egg for testing Dose!" in pkg_info_data
        if setuptools.__version__ >= "57":
            assert pkg_info_data.rstrip().endswith(
                u"A title\nAn extra line just to TEST it!"
            )
        else:
            assert (
                u"Description: A title\n        An extra line just to TEST it!"
                in pkg_info_data
            )


def test_first_contributor_is_author():
    assert isinstance(CONTRIBUTORS, list)
    assert CONTRIBUTORS[0].startswith(__author__)
