This is the further development of the script found [here](
https://www.mediawiki.org/wiki/Manual:TikiWiki_Conversion). First we 
transformed the history of the linked wiki page into the history of a source 
code repository and afterwards continued the development by adapting the 
script to the current versions of the applications.

The result is a Python3 script which takes a TikiWiki exported .tar-file and a 
TikiWiki URL as input and delivers an XML-file to import into a MediaWiki 
instance or an XWiki instance using the Filter Streams Converter Application 
and following the procedure to import MediaWiki content as described [here](
https://extensions.xwiki.org/xwiki/bin/view/Extension/MediaWiki/MediaWiki%20XML/
).
