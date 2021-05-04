# TikiToMediaWikiXML

[![CircleCI](https://circleci.com/gh/PTB-PSt1/TikiToMediaWikiXML.svg?style=shield)](https://circleci.com/gh/PTB-PSt1/TikiToMediaWikiXML)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/08ba4bc84fae4829a0ed74d3e70b6df8)](https://www.codacy.com/app/PTB-PSt1/TikiToMediaWikiXML?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=PTB-PSt1/TikiToMediaWikiXML&amp;utm_campaign=Badge_Grade)

This is the further development of the script found [here](
https://www.mediawiki.org/wiki/Manual:TikiWiki_Conversion). First we 
transformed the history of the linked wiki page into the history of a source 
code repository and afterwards continued the development by adapting the 
script to the current versions of the applications.

The result is a Python3 script which takes a TikiWiki exported .tar-file, and a 
TikiWiki URL as input and delivers an XML-file to import into a MediaWiki 
instance, or an XWiki instance using the Filter Streams Converter Application 
and following the procedure to import MediaWiki content as described [here](
https://extensions.xwiki.org/xwiki/bin/view/Extension/MediaWiki/MediaWiki%20XML/
).

## How to use it?

First you should create a virtual environment based on a recent Python version (the 
provided [requirements.txt](./requirements/requirements.txt) file was compiled for
Python 3.9 using [pip-tools](https://github.com/jazzband/pip-tools)).

To accomplish the environment setup just execute the following in bash oder Windows 
command prompt:

```shell
$ python -m venv tiki2mediawiki_conversion_venv
$ source tiki2mediawiki_conversion_venv/bin/activate
(tiki2mediawiki_conversion_venv) $ pip install --upgrade pip setuptools pip-tools
Collecting pip
[...]
Successfully installed click-7.1.2 pep517-0.10.0 pip-21.1.1 pip-tools-6.1.0 setuptools-56.0.0 toml-0.10.2
(tiki2mediawiki_conversion_venv) $ python -m piptools sync requirements/requirements.txt
Collecting defusedxml==0.7.1
  Using cached defusedxml-0.7.1-py2.py3-none-any.whl (25 kB)
Installing collected packages: defusedxml
Successfully installed defusedxml-0.7.1
(tiki2mediawiki_conversion_venv) $
```

A detailed description how to use the script you can find in the
[MediaWiki documentation
](https://www.mediawiki.org/wiki/Manual:TikiWiki_Conversion).
