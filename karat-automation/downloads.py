"""Regular HTTP downloads, including APKMirror's public multi-step flow.
No browser automation, challenge-solving or exported browser cookies.
"""
import http.cookiejar
from html.parser import HTMLParser
import urllib.parse
import urllib.request

class DownloadResolutionError(OSError): pass

class APKMirrorLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buttons=[]
        self.files=[]
    def handle_starttag(self,tag,attrs):
        if tag!='a':return
        attrs=dict(attrs)
        href=attrs.get('href','')
        if not href:return
        if 'downloadButton' in attrs.get('class','').split():self.buttons.append(href)
        if '/wp-content/themes/APKMirror/download.php?' in href or attrs.get('id')=='downloadLink':self.files.append(href)


def open_download(url, timeout=60):
    """Return an open binary response. Caller closes it after streaming."""
    host=urllib.parse.urlsplit(url).hostname
    if host not in ('www.apkmirror.com','apkmirror.com'):
        return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FireTV-Setup/1.0'}),timeout=timeout)
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    referer=None
    seen=set()
    for _ in range(5):
        headers={'User-Agent':'FireTV-Setup/1.0','Accept':'*/*'}
        if referer:headers['Referer']=referer
        response=opener.open(urllib.request.Request(url,headers=headers),timeout=timeout)
        current=response.geturl()
        if urllib.parse.urlsplit(current).scheme!='https':
            response.close();raise DownloadResolutionError('Insecure download redirect.')
        kind=response.headers.get('Content-Type','').lower()
        if 'text/html' not in kind:return response
        try:
            html=response.read(4*1024*1024+1)
            if len(html)>4*1024*1024:raise DownloadResolutionError('APKMirror page is unexpectedly large.')
        finally:response.close()
        links=APKMirrorLinks();links.feed(html.decode('utf-8',errors='replace'))
        # Follow only explicit download controls, never arbitrary page/ad links.
        candidates=links.files or links.buttons
        urls=[]
        for href in candidates:
            target=urllib.parse.urljoin(current,href)
            parsed=urllib.parse.urlsplit(target)
            if parsed.scheme=='https' and parsed.hostname in ('www.apkmirror.com','apkmirror.com') and target not in seen:
                urls.append(target)
        if not urls:raise DownloadResolutionError('APKMirror provides no accessible download button. A manual file or another approved source is required.')
        if len(set(urls))!=1:raise DownloadResolutionError('APKMirror download target is ambiguous.')
        referer=current;url=urls[0];seen.add(url)
    raise DownloadResolutionError('APKMirror download still is not available as a file after five steps.')

def copy_with_progress(response, output, label):
    """Stream binary payloads with real byte counts; never buffer an APK in RAM."""
    import terminal_ui as ui
    try: total = int(getattr(response, 'headers', {}).get('Content-Length', 0))
    except (TypeError, ValueError): total = 0
    progress = ui.Progress(label, total=total)
    count = 0
    try:
        while True:
            chunk = response.read(256 * 1024)
            if not chunk: break
            output.write(chunk)
            count += len(chunk)
            progress.update(count)
        if total > 0 and count != total:
            raise OSError(f'Incomplete download: received {count} of {total} bytes.')
        progress.update(count, force=True)
        return count
    finally:
        progress.close()
