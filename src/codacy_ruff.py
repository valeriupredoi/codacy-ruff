import os
import sys
import itertools
import json
import jsonpickle
import subprocess
import ast
import glob
import signal
from contextlib import contextmanager
import traceback
import django
import re

@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, lambda: sys.exit(2))
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)
    yield

DEFAULT_TIMEOUT = 15 * 60
def getTimeout(timeoutString):
    if not timeoutString.isdigit():
        return DEFAULT_TIMEOUT
    return int(timeoutString)

class Result:
    def __init__(self, filename, message, patternId, line):
        self.filename = filename
        self.message = message
        self.patternId = patternId
        self.line = line
    def __str__(self):
        return f'Result({self.filename},{self.message},{self.patternId},{self.line})'
    def __repr__(self):
        return self.__str__()
    def __eq__(self, o):
        return self.filename == o.filename and self.message == o.message and self.patternId == o.patternId and self.line == o.line

def toJson(obj): return jsonpickle.encode(obj, unpicklable=False)

def readJsonFile(path):
    with open(path, 'r') as file:
        res = json.loads(file.read())
    return res


def run_ruff(files, cwd=None):
    cmd = ['python', '-m', 'ruff', 'check']
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        cwd=cwd
    )
    stdout = process.communicate()[0]
    result = stdout.decode('utf-8')

    return result

def is_python3(f):
    try:
        with open(f, 'r') as stream:
            try:
                ast.parse(stream.read())
            except (ValueError, TypeError, UnicodeError):
                # Assume it's the current interpreter.
                return True
            except SyntaxError:
                # the other version or an actual syntax error on current interpreter
                return False
            else:
                return True
    except Exception:
        # Shouldn't happen, but if it does, just assume there's
        # something inherently wrong with the file.
        return True


def parse_result(output_text):
    """Set a parser ofr ruff output."""
    return


def get_files(src_dir):
    files = []
    for filename in glob.iglob(os.path.join(src_dir, '**/*.py'),
                                            recursive=True):
        res = os.path.abspath(filename)
        files.append(res)
    all_files = [f for f in files if is_python3(f)]

    return all_files


def chunks(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def run_ruff_parsed(files, cwd):
    res = run_ruff(files, cwd)

    # these need be parsed in a way
    # res = parse_result(res)

    return res


def run_tool(src_dir):
    files = get_files(src_dir)
    res = []
    results = []
    files = [os.path.join(src_dir, f) for f in files]
    for chunk in chunks(files, 10):
        fres = run_ruff_parsed(chunk, src_dir)
        fres = "".join([str(r) for r in fres])
        res.append(fres)

    res = [r.split("\n") for r in res]
    res = list(itertools.chain.from_iterable(res))

    for result in res:
        # obj_result = Result()
        if result.startswith(src_dir):
            result.filename = os.path.relpath(result.filename, src_dir)

    return res


def results_to_json(results):
    return os.linesep.join([toJson(res) for res in results])

if __name__ == '__main__':
    with timeout(getTimeout(os.environ.get('TIMEOUT_SECONDS') or '')):
        try:
            results = run_tool('src')
            results = results_to_json(results)
            print("Ruff results", results)
        except Exception:
            traceback.print_exc()
            sys.exit(1)
