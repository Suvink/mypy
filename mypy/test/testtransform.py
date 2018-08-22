"""Identity AST transform test cases"""

import os.path

from mypy import build
from mypy.build import BuildSource
from mypy.test.helpers import (
    assert_string_arrays_equal, testfile_pyversion, normalize_error_messages
)
from mypy.test.data import DataDrivenTestCase, DataSuite
from mypy.test.config import test_temp_dir
from mypy.test.test_visitors import TypeAssertTransformVisitor
from mypy.errors import CompileError
from mypy.options import Options


class TransformSuite(DataSuite):
    required_out_section = True
    # Reuse semantic analysis test cases.
    files = ['semanal-basic.test',
             'semanal-expressions.test',
             'semanal-classes.test',
             'semanal-types.test',
             'semanal-modules.test',
             'semanal-statements.test',
             'semanal-abstractclasses.test',
             'semanal-python2.test']
    native_sep = True

    def run_case(self, testcase: DataDrivenTestCase) -> None:
        test_transform(testcase)


def test_transform(testcase: DataDrivenTestCase) -> None:
    """Perform an identity transform test case."""

    try:
        src = '\n'.join(testcase.input)
        options = Options()
        options.use_builtins_fixtures = True
        options.semantic_analysis_only = True
        options.show_traceback = True
        options.python_version = testfile_pyversion(testcase.file)
        result = build.build(sources=[BuildSource('main', None, src)],
                             options=options,
                             alt_lib_path=test_temp_dir)
        a = result.errors
        if a:
            raise CompileError(a)
        # Include string representations of the source files in the actual
        # output.
        for fnam in sorted(result.files.keys()):
            f = result.files[fnam]

            # Omit the builtins module and files with a special marker in the
            # path.
            # TODO the test is not reliable
            if (not f.path.endswith((os.sep + 'builtins.pyi',
                                     'typing.pyi',
                                     'abc.pyi'))
                    and not os.path.basename(f.path).startswith('_')
                    and not os.path.splitext(
                        os.path.basename(f.path))[0].endswith('_')):
                t = TypeAssertTransformVisitor()
                f = t.mypyfile(f)
                a += str(f).split('\n')
    except CompileError as e:
        a = e.messages
    a = normalize_error_messages(a)
    assert_string_arrays_equal(
        testcase.output, a,
        'Invalid semantic analyzer output ({}, line {})'.format(testcase.file,
                                                                testcase.line))
