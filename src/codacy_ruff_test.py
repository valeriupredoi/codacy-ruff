import tempfile
import numpy as np

from codacy_ruff import (
    toJson, chunks, run_tool, getTimeout,
    DEFAULT_TIMEOUT, Result
)


def assemble_sources(sources):
    with tempfile.TemporaryDirectory() as directory:
        for (name, source) in sources:
            with open(directory + '/' + name, 'w', encoding='utf-8') as f:
                print(source, file=f)
        return run_tool(directory)

def python3_file():
    source ='''
##Patterns: E0102

class Test():
    def dup(self):
        return 1

    ##Err: E0102
    def dup(self):
        return 2

##Err: E0102
class Test():
    def __init__(self):
        return

def dup_function():
    return 1

##Err: E0102
def dup_function():
    return 2
'''
    sources = [('E0102.py', source)]
    return sources

def test_toJson():
    result = Result("file.py", "message", "id", 80)
    res = toJson(result)
    expected = '{"filename": "file.py", "message": "message", "patternId": "id", "line": 80}'
    np.testing.assert_equal(res, expected)


def test_chunks():
    files = ["file1", "file2"]
    expected = [["file1", "file2"]]
    out = chunks(files, 10)
    np.testing.assert_equal(out, expected)

    expected2 = [["file1"], ["file2"]]
    out2 = chunks(files, 1)
    np.testing.assert_equal(expected2, out2)


def test_python3_file():
    sources = python3_file()
    result = assemble_sources(sources)
    np.testing.assert_equal(len(result), 3)


def test_timeout():
    np.testing.assert_equal(getTimeout("60"), 60)
    np.testing.assert_equal(getTimeout("blabla"), DEFAULT_TIMEOUT)
