import sys
from subprocess import check_output


class TestMath:

    @classmethod
    def teardown_class(cls):
        """
            This method deletes all files created during the tests with
            filenames './test/math/math_*.xml'.
        """
        from glob import glob
        import os

        for filename in glob("./test/math/math_*.xml"):
            os.remove(filename)

    @staticmethod
    def test_minimal_call():
        check_output(
            [sys.executable, "tikiToMwiki.py",
             "https://fb1-7.bs.ptb.de/tiki/",
             "./test/math/math.tar"])

    @staticmethod
    def test_stdout_call():
        expected = '<mediawiki xml:lang="en">\r\n<siteinfo>\r\n<base>' \
                   'https://fb1-7.bs.ptb.de/tiki/</base>\r\n</siteinfo>' \
                   '\r\n<page>\r\n<title>Math testpage</title>\r\n' \
                   '<revision>\r\n<id>1</id>\r\n<timestamp>' \
                   '2018-03-12T12:38:31Z</timestamp>\r\n<contributor>' \
                   '<username>mustermann</username></contributor>\r\n' \
                   '<text xml:space="preserve">\r\n__TOC__\r\n\r\n' \
                   '{{mathjax}}\r\n\r\na(t) = \\frac{1}{2}\\' \
                   'left[\r\n\r\na_1 sin(\\omega t) + a_2 sin(' \
                   '\\omega t - \\varphi_0)\r\n\r\n\\right]\r\n\r\n{{' \
                   '/mathjax}}\r\n\r\n</text>\r\n</revision>' \
                   '\r\n</page>\r\n</mediawiki>\r\n\r\nnumber of pages ' \
                   '= 1 number of versions = 1\r\nwith contributions by ' \
                   '[\'mustermann\']\r\nand file uploads on these pages:' \
                   ' dict_keys([])\r\n'
        expected_lin = expected.replace('\r\n', '\n').encode()
        expected_win = expected.encode()
        result = check_output(
            [sys.executable, "tikiToMwiki.py", "-o", "-",
             "https://fb1-7.bs.ptb.de/tiki/", "./test/math/math.tar"])
        assert (result == expected_lin or result == expected_win)


class TestImages:

    @classmethod
    def teardown_class(cls):
        """
            This method deletes all files created during the tests with
            filenames './test/images/Image testpage_*.xml'.
        """
        from glob import glob
        import os

        for filename in glob("./test/images/Image testpage_*.xml"):
            os.remove(filename)

    @staticmethod
    def test_minimal_call():
        check_output(
            [sys.executable, "tikiToMwiki.py", "-k",
             "./test/images/testpage_images.xml", "-i", "./test/images/",
             "https://fb1-7.bs.ptb.de/tiki/",
             "./test/images/Image testpage.tar"])

    @staticmethod
    def test_stdout_minimal_call():
        expected = '<mediawiki ' \
                   'xml:lang="en">\r\n<siteinfo>\r\n<base>https://fb1-7.' \
                   'bs.ptb.de/tiki/</base>\r\n</siteinfo>\r\n<page>\r\n' \
                   '<title>Image testpage</title>\r\n<revision>\r\n<id>1' \
                   '</id>\r\n<timestamp>2018-03-12T12:38:31Z</timestamp>' \
                   '\r\n<contributor><username>mustermann</username>' \
                   '</contributor>\r\n<text xml:space="preserve">\r\n' \
                   '__TOC__\r\n\r\n{{File:Xwiki-logo.png#124;}} ' \
                   '</text>\r\n' \
                   '</revision>\r\n</page>\r\n</mediawiki>\r\n\r\n' \
                   'number of pages = 1 number of versions = 1\r\nwith ' \
                   'contributions by [\'mustermann\']\r\nand file uploads' \
                   ' on these pages: dict_keys([])\r\n'
        expected_lin = expected.replace('\r\n', '\n').encode()
        expected_win = expected.encode()
        result = check_output(
            [sys.executable, "tikiToMwiki.py", "-o", "-", "-k",
             "./test/images/testpage_images.xml", "-i", ".",
             "https://fb1-7.bs.ptb.de/tiki/",
             "./test/images/Image testpage.tar"])
        assert (result == expected_lin or result == expected_win)

    @staticmethod
    def test_stdout_with_width_call():
        expected = '<mediawiki ' \
                   'xml:lang="en">\r\n<siteinfo>\r\n<base>https://fb1-7.' \
                   'bs.ptb.de/tiki/</base>\r\n</siteinfo>\r\n<page>\r\n' \
                   '<title>Image testpage</title>\r\n<revision>\r\n<id>1' \
                   '</id>\r\n<timestamp>2018-03-12T12:38:31Z</timestamp>' \
                   '\r\n<contributor><username>mustermann</username>' \
                   '</contributor>\r\n<text xml:space="preserve">\r\n' \
                   '__TOC__\r\n\r\n{{File:Xwiki-logo.png#124;100px#124;}} ' \
                   '</text>\r\n' \
                   '</revision>\r\n</page>\r\n</mediawiki>\r\n\r\n' \
                   'number of pages = 1 number of versions = 1\r\nwith ' \
                   'contributions by [\'mustermann\']\r\nand file uploads' \
                   ' on these pages: dict_keys([])\r\n'
        expected_lin = expected.replace('\r\n', '\n').encode()
        expected_win = expected.encode()
        result = check_output(
            [sys.executable, "tikiToMwiki.py", "-o", "-", "-k",
             "./test/images/testpage_images.xml", "-i", ".",
             "https://fb1-7.bs.ptb.de/tiki/",
             "./test/images/Image testpage_width.tar"])
        assert (result == expected_lin or result == expected_win)

    @staticmethod
    def test_stdout_with_width_px_call():
        expected = '<mediawiki ' \
                   'xml:lang="en">\r\n<siteinfo>\r\n<base>https://fb1-7.' \
                   'bs.ptb.de/tiki/</base>\r\n</siteinfo>\r\n<page>\r\n' \
                   '<title>Image testpage</title>\r\n<revision>\r\n<id>1' \
                   '</id>\r\n<timestamp>2018-03-12T12:38:31Z</timestamp>' \
                   '\r\n<contributor><username>mustermann</username>' \
                   '</contributor>\r\n<text xml:space="preserve">\r\n' \
                   '__TOC__\r\n\r\n{{File:Xwiki-logo.png#124;600px#124;}} ' \
                   '</text>\r\n' \
                   '</revision>\r\n</page>\r\n</mediawiki>\r\n\r\n' \
                   'number of pages = 1 number of versions = 1\r\nwith ' \
                   'contributions by [\'mustermann\']\r\nand file uploads' \
                   ' on these pages: dict_keys([])\r\n'
        expected_lin = expected.replace('\r\n', '\n').encode()
        expected_win = expected.encode()
        result = check_output(
            [sys.executable, "tikiToMwiki.py", "-o", "-", "-k",
             "./test/images/testpage_images.xml", "-i", ".",
             "https://fb1-7.bs.ptb.de/tiki/",
             "./test/images/Image testpage_width_px.tar"])
        assert (result == expected_lin or result == expected_win)

    @staticmethod
    def test_stdout_with_percentage_call():
        expected = '<mediawiki ' \
                   'xml:lang="en">\r\n<siteinfo>\r\n<base>https://fb1-7.' \
                   'bs.ptb.de/tiki/</base>\r\n</siteinfo>\r\n<page>\r\n' \
                   '<title>Image testpage</title>\r\n<revision>\r\n<id>1' \
                   '</id>\r\n<timestamp>2018-03-12T12:38:31Z</timestamp>' \
                   '\r\n<contributor><username>mustermann</username>' \
                   '</contributor>\r\n<text xml:space="preserve">\r\n' \
                   '__TOC__\r\n\r\n{{File:Xwiki-logo.png#124;upright ' \
                   '1.0#124;}} ' \
                   '</text>\r\n' \
                   '</revision>\r\n</page>\r\n</mediawiki>\r\n\r\n' \
                   'number of pages = 1 number of versions = 1\r\nwith ' \
                   'contributions by [\'mustermann\']\r\nand file uploads' \
                   ' on these pages: dict_keys([])\r\n'
        expected_lin = expected.replace('\r\n', '\n').encode()
        expected_win = expected.encode()
        result = check_output(
            [sys.executable, "tikiToMwiki.py", "-o", "-", "-k",
             "./test/images/testpage_images.xml", "-i", ".",
             "https://fb1-7.bs.ptb.de/tiki/",
             "./test/images/Image testpage_width_percentage.tar"])
        assert (result == expected_lin or result == expected_win)

    # noinspection PyPep8Naming
    @classmethod
    def tearDownClass(cls):
        from glob import glob

        for filename in glob("images_*.xml"):
            print(filename)
            # (filename)
