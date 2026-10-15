import io
import unittest
from unittest.mock import Mock,patch
import downloads as d

class Response(io.BytesIO):
    def __init__(self,data,url,kind):super().__init__(data);self.url=url;self.headers={'Content-Type':kind}
    def geturl(self):return self.url

class Downloads(unittest.TestCase):
    def test_apkmirror_resolves_public_steps_with_referer(self):
        page='https://www.apkmirror.com/apk/test/'
        step=page+'download/?key=NEW&forcebaseapk=true'
        responses=[Response(b'<a class="downloadButton" href="download/?key=NEW&amp;forcebaseapk=true">download</a>',page,'text/html'),Response(b'<a href="/wp-content/themes/APKMirror/download.php?id=1&amp;key=FILE">file</a>',step,'text/html'),Response(b'PK\x03\x04data','https://download.apkmirror.com/file.apk','application/vnd.android.package-archive')]
        opener=Mock();opener.open.side_effect=responses
        with patch.object(d.urllib.request,'build_opener',return_value=opener):
            response=d.open_download(page)
            self.assertEqual(response.read(),b'PK\x03\x04data');response.close()
        calls=opener.open.call_args_list
        self.assertEqual(calls[1].args[0].get_header('Referer'),page)
        self.assertEqual(calls[2].args[0].get_header('Referer'),step)
        self.assertIn('key=FILE',calls[2].args[0].full_url)
    def test_foreign_ad_link_is_not_followed(self):
        response=Response(b'<a class="downloadButton" href="https://ads.example/file">download</a>','https://www.apkmirror.com/apk/test/','text/html')
        opener=Mock();opener.open.return_value=response
        with patch.object(d.urllib.request,'build_opener',return_value=opener):
            with self.assertRaises(d.DownloadResolutionError):d.open_download(response.url)
        self.assertEqual(opener.open.call_count,1)
    def test_html_without_download_control_fails(self):
        response=Response(b'<html>Please use browser</html>','https://www.apkmirror.com/apk/test/','text/html')
        opener=Mock();opener.open.return_value=response
        with patch.object(d.urllib.request,'build_opener',return_value=opener):
            with self.assertRaises(d.DownloadResolutionError):d.open_download(response.url)
    def test_other_hosts_use_regular_direct_request(self):
        with patch.object(d.urllib.request,'urlopen') as network:
            d.open_download('https://example.org/file.zip')
            self.assertEqual(network.call_args.args[0].full_url,'https://example.org/file.zip')
    def test_parser_unescapes_query_parameters(self):
        parser=d.APKMirrorLinks();parser.feed('<a id="downloadLink" href="/download.php?id=1&amp;key=2">Download</a>')
        self.assertEqual(parser.files,['/download.php?id=1&key=2'])
if __name__=='__main__':unittest.main()
