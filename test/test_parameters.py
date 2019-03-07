import sys
from subprocess import call


def test_minimal_call():
    call(
        [sys.executable, "TikiToMWiki.py", "https://fb1-7.bs.ptb.de/tiki/",
         "./test/math.tar"], shell=True)


def test_stdout_call():
    call(
        [sys.executable, "TikiToMWiki.py",  "-o", "-",
         "https://fb1-7.bs.ptb.de/tiki/", "./test/math.tar"], shell=True)
