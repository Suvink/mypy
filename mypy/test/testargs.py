"""Ensure the argparse parser and Options class are in sync.

In particular, verify that the argparse defaults are the same as the Options
defaults, and that argparse doesn't assign any new members to the Options
object it creates.
"""
import argparse
import sys

import pytest  # type: ignore

from mypy.test.helpers import Suite, assert_equal
from mypy.options import Options
from mypy.main import (process_options, PythonExecutableInferenceError,
                       infer_python_version_and_executable)


class ArgSuite(Suite):
    def test_coherence(self) -> None:
        options = Options()
        _, parsed_options = process_options([], require_targets=False)
        # FIX: test this too. Requires changing working dir to avoid finding 'setup.cfg'
        options.config_file = parsed_options.config_file
        assert_equal(options.snapshot(), parsed_options.snapshot())

    def test_executable_inference(self) -> None:
        """Test the --python-executable flag with --python-version"""
        sys_ver_str = '{ver.major}.{ver.minor}'.format(ver=sys.version_info)

        base = ['file.py']  # dummy file

        # test inference given one (infer the other)
        matching_version = base + ['--python-version={}'.format(sys_ver_str)]
        _, options = process_options(matching_version)
        assert options.python_version == sys.version_info[:2]
        assert options.python_executable == sys.executable

        matching_version = base + ['--python-executable={}'.format(sys.executable)]
        _, options = process_options(matching_version)
        assert options.python_version == sys.version_info[:2]
        assert options.python_executable == sys.executable

        # test inference given both
        matching_version = base + ['--python-version={}'.format(sys_ver_str),
                                   '--python-executable={}'.format(sys.executable)]
        _, options = process_options(matching_version)
        assert options.python_version == sys.version_info[:2]
        assert options.python_executable == sys.executable

        # test that we error if the version mismatch
        # argparse sys.exits on a parser.error, we need to check the raw inference function
        options = Options()

        special_opts = argparse.Namespace()
        special_opts.python_executable = sys.executable
        special_opts.python_version = (2, 10)  # obviously wrong
        special_opts.no_executable = None
        with pytest.raises(PythonExecutableInferenceError) as e:
            infer_python_version_and_executable(options, special_opts)
        assert str(e.value) == 'Python version (2, 10) did not match executable {}, got' \
                               ' version {}.'.format(sys.executable, sys.version_info[:2])

        # test that --no-site-packages will disable executable inference
        matching_version = base + ['--python-version={}'.format(sys_ver_str),
                                   '--no-site-packages']
        _, options = process_options(matching_version)
        assert options.python_version == sys.version_info[:2]
        assert options.python_executable is None
