import os
import sys
import json
import jsonpickle
import subprocess
import ast
import glob
import signal
from contextlib import contextmanager
import traceback


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
    # result need be formatted as JSON
    # expected = '{"filename": "file.py",
    #              "message": "message",
    #              "patternId": "id", "line": 80}'
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
        return (self.filename == o.filename,
                self.message == o.message,
                self.patternId == o.patternId,
                self.line == o.line)


def toJson(obj):
    return jsonpickle.encode(obj, unpicklable=False)


def readJsonFile(path):
    with open(path, 'r', encoding='utf-8') as file:
        res = json.loads(file.read())
    return res


def run_ruff(files, cwd=None):
    cmd = ['python', '-m', 'ruff', 'check', '--output-format=json']
    cmd = cmd + files
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
        with open(f, 'r', encoding="utf-8") as stream:
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
    results = []
    res = run_ruff(files, cwd)
    ruff_dicts = json.loads(res)
    # a ruff_dict contains standardized keys:
    # {  'cell': None,
    #    'code': 'F401',
    #    'end_location': {'column': 17, 'row': 3},
    #    'filename': '/home/valeriu/codacy-ruff/src/codacy_ruff.py',
    #    'fix': {'applicability': 'safe', 'edits': [{'content': '',
    #            'end_location': {'column': 1, 'row': 4},
    #            'location': {'column': 1, 'row': 3}}],
    #            'message': 'Remove unused import: `itertools`'},
    #    'location': {'column': 8, 'row': 3},
    #    'message': '`itertools` imported but unused',
    #    'noqa_row': 3,
    #    'url': 'https://docs.astral.sh/ruff/rules/unused-import'
    # }
    for res in ruff_dicts:
        if res['code'] != 'failure' and res['code'] != 'import-error':
            filename = res['filename']
            message = f"{res['message']} ({res['code']})"
            patternId = res['url']
            line = res['end_location']['row']
            results.append(Result(filename, message, patternId, line))

    return results


def run_tool(src_dir):
    files = get_files(src_dir)
    res = []
    files = [os.path.join(src_dir, f) for f in files]
    for chunk in chunks(files, 10):
        fres = run_ruff_parsed(chunk, src_dir)
        res.extend(fres)

    # files: go from fullpath to relpath (needed?)
    for result in res:
        if result.filename.startswith(os.path.abspath(src_dir)):
            result.filename = os.path.relpath(result.filename, src_dir)

    return res


def results_to_json(results):
    return os.linesep.join([toJson(res) for res in results])


if __name__ == '__main__':
    with timeout(getTimeout(os.environ.get('TIMEOUT_SECONDS') or '')):
        try:
            results = run_tool('src')
            results = results_to_json(results)
            print(results)
        except Exception:
            traceback.print_exc()
            sys.exit(1)
