import subprocess
import sys


def test_minimal_call():
    subprocess.call(
        [sys.executable, "TikiToMWiki.py", "https://fb1-7.bs.ptb.de/tiki/",
         "./test/math.tar"], shell=False)


def test_stdout_call():
    subprocess.call(
        [sys.executable, "TikiToMWiki.py",  "-o", "-",
         "https://fb1-7.bs.ptb.de/tiki/", "./test/math.tar"], shell=False)
