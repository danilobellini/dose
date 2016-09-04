"""Dose GUI for TDD: test module for the shared resources module."""
import pkg_resources, pytest
from dose import __version__, __author__
from dose.shared import get_shared, README, CHANGES, CONTRIBUTORS, LICENSE


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
            raise Exception("Attempt to call pkg_resources.resource_string")

        # Ensure the setuptools "pkg_resources.resource_string" isn't used,
        # given that tox always installs Dose via pip
        monkeypatch.setattr(pkg_resources, "resource_string", raiser)

        assert get_shared("README.rst").splitlines() == README
        assert get_shared("CHANGES.rst").splitlines() == CHANGES
        assert get_shared("CONTRIBUTORS.txt").splitlines() == CONTRIBUTORS
        assert get_shared("COPYING.txt").splitlines() == LICENSE.splitlines()

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


def test_first_contributor_is_author():
    assert isinstance(CONTRIBUTORS, list)
    assert CONTRIBUTORS[0].startswith(__author__)
