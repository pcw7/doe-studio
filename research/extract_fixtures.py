"""Minitab 예제 페이지(.txt)에서 출력표를 JSON 픽스처로 추출한다.

사용법: python -I extract_fixtures.py <pages_dir/en-us> <out_dir>
각 *example*.txt 에 대해 {slug}.json 을 만든다:
  url, title, steps(예제 절차), tables[{heading, header, rows}], notes(표 밖의 수치 문장)
"""
import sys, os, re, json, glob
sys.stdout.reconfigure(encoding='utf-8')

def parse(txt):
    lines = txt.split('\n')
    url = lines[0][5:].strip() if lines and lines[0].startswith('URL: ') else ''
    title = lines[1][7:].strip() if len(lines) > 1 and lines[1].startswith('TITLE: ') else ''
    body = lines[2:]
    tables, steps, notes = [], [], []
    i = 0
    last_heading = ''
    in_steps = False
    while i < len(body):
        ln = body[i].strip()
        if ln == '[TABLE]':
            rows = []
            i += 1
            while i < len(body) and body[i].strip() != '[/TABLE]':
                r = body[i].strip()
                if r:
                    rows.append([c.strip() for c in r.split('|')])
                i += 1
            if rows:
                header, data = rows[0], rows[1:]
                tables.append({'heading': last_heading, 'header': header, 'rows': data})
            i += 1
            continue
        if ln:
            if re.match(r'^(Open the sample data|Choose |In |Click |Under |From |Select |Check |Use the arrows)', ln):
                in_steps = True
            if ln.startswith('Interpret the results'):
                in_steps = False
            if in_steps:
                steps.append(ln)
            elif re.search(r'\d', ln) and len(ln) < 400:
                notes.append(ln)
            if not ln.startswith(('Open the', 'Choose', 'Click', 'In ', 'Under', 'From', 'Select', 'Check')) and len(ln) < 120 and not ln.endswith('.'):
                last_heading = ln
        i += 1
    return {'url': url, 'title': title, 'steps': steps, 'tables': tables, 'notes': notes}

def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    n = 0
    for f in sorted(glob.glob(os.path.join(src, '*.txt'))):
        base = os.path.basename(f)[:-4]
        raw = open(f, encoding='utf-8').read()
        url = raw.splitlines()[0] if raw else ''
        if not any(k in url for k in ('example', 'display-available-designs', 'available-', 'summary-of', 'design-generators', 'catalogue', 'all-statistics')):
            continue
        data = parse(raw)
        # 파일명 대신 URL 기반의 읽기 쉬운 이름 사용
        base = url.split('statistical-modeling/')[-1].strip('/').replace('/', '__')
        for pre, short in (('doe__how-to__', ''), ('using-fitted-models__how-to__', 'ufm__'), ('doe__supporting-topics__', 'topic__')):
            if base.startswith(pre):
                base = short + base[len(pre):]
        base = base.replace('__before-you-start__', '__').replace('__interpret-the-results__all-statistics-and-graphs__', '__asg__')
        base = base if len(base) <= 110 else base[:110]
        if not data['tables']:
            continue
        json.dump(data, open(os.path.join(out, base + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        n += 1
        print('%-110s tables=%d' % (base[:110], len(data['tables'])))
    print('written', n)

if __name__ == '__main__':
    main()
