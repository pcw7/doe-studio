import sys, re, time, os, urllib.request, hashlib
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'https://support.minitab.com/'
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.out=[]; s.cell=[]; s.row=[]; s.intable=0; s.skip=0
    def handle_starttag(s,t,a):
        a=dict(a)
        if t in('script','style'): s.skip+=1
        if t=='table': s.intable+=1; s.out.append('\n[TABLE]')
        if t=='tr': s.row=[]
        if t in('td','th'): s.cell=[]
        if t in('p','h1','h2','h3','h4','h5','li','div','br','tr'): s.out.append('\n')
        if t=='img' and a.get('alt'):
            (s.cell if s.intable else s.out).append(' {img:'+a['alt'].strip()+'} ')
    def handle_endtag(s,t):
        if t in('script','style'): s.skip-=1
        if t in('td','th'): s.row.append(' '.join(''.join(s.cell).split()))
        if t=='tr': s.out.append('\n'+' | '.join(s.row))
        if t=='table': s.intable-=1; s.out.append('\n[/TABLE]\n')
    def handle_data(s,d):
        if s.skip: return
        (s.cell if s.intable else s.out).append(d)
def to_text(src):
    m = re.search(r'<div class="body taskbody[^"]*">(.*?)<div class="footerContainer"', src, re.S) or re.search(r'<div class="topicContainer">(.*?)<div class="footerContainer"', src, re.S)
    body = m.group(1) if m else src
    t = re.search(r'<title>(.*?)</title>', src, re.S)
    p=P(); p.feed(body)
    txt=re.sub(r'[ \t]+',' ',''.join(p.out)); txt=re.sub(r'\n\s*\n+','\n',txt)
    return ('TITLE: '+(t.group(1).strip() if t else '')+'\n'+txt).strip()
def slug(path):
    s = re.sub(r'^/?(en-us|ko-kr)/minitab/help-and-how-to/statistical-modeling/','',path).strip('/').replace('/','__')
    return s if len(s)<=90 else s[:70]+'_'+hashlib.md5(s.encode()).hexdigest()[:8]
def fetch(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.geturl(), r.read().decode('utf-8','replace')
if __name__=='__main__':
    listfile, outdir = sys.argv[1], sys.argv[2]
    locales = sys.argv[3].split(',') if len(sys.argv)>3 else ['en-us']
    paths = [l.strip() for l in open(listfile, encoding='utf-8') if l.strip() and not l.startswith('#')]
    ok=miss=0
    for loc in locales:
        d = os.path.join(outdir, loc); os.makedirs(d, exist_ok=True)
        for p in paths:
            p = p.lstrip('/')
            url = BASE + loc + '/minitab/help-and-how-to/statistical-modeling/' + p
            name = slug(p)
            if os.path.exists(os.path.join(d, name+'.txt')): ok+=1; continue
            try:
                st, final, html = fetch(url)
                if '404.html' in final or '<title>404' in html:
                    print('MISS', loc, p); miss+=1; continue
                open(os.path.join(d, name+'.html'),'w',encoding='utf-8').write(html)
                open(os.path.join(d, name+'.txt'),'w',encoding='utf-8').write('URL: '+url+'\n'+to_text(html))
                ok+=1; print('OK  ', loc, p)
            except Exception as e:
                print('ERR ', loc, p, e); miss+=1
            time.sleep(0.4)
    print('done ok=%d miss=%d'%(ok,miss))
