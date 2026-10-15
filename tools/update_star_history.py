"""Render real daily aggregate snapshots without exposing private repository tokens."""
import argparse,json,os,re,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]

def record_snapshot(history,repo,count,day):
    if type(count) is not int or count<0:raise ValueError('Invalid star count')
    if history.get('repository',repo)!=repo:raise ValueError('Repository mismatch')
    rows={r['date']:r['stars'] for r in history.get('snapshots',[])}
    for date,stars in rows.items():
        datetime.strptime(date,'%Y-%m-%d')
        if type(stars) is not int or stars<0:raise ValueError('Invalid saved count')
    datetime.strptime(day,'%Y-%m-%d');rows[day]=count
    return {'schemaVersion':1,'repository':repo,'timezone':'Asia/Shanghai','snapshots':[{'date':d,'stars':rows[d]} for d in sorted(rows)]}

def render(history):
    rows=history['snapshots']
    if not rows:raise ValueError('No real snapshots available')
    width,height,left,right,top,bottom=900,300,58,860,90,238
    dates=[datetime.strptime(r['date'],'%Y-%m-%d') for r in rows]
    span=max(1,(dates[-1]-dates[0]).days);maximum=max(1,max(r['stars'] for r in rows))
    points=[(left+(right-left)*((d-dates[0]).days/span) if len(rows)>1 else (left+right)/2,bottom-(bottom-top)*r['stars']/maximum) for d,r in zip(dates,rows)]
    elements=[]
    for tick in sorted({0,maximum//2,maximum}):
        fraction=tick/maximum
        y=bottom-(bottom-top)*fraction
        elements.append(f'<path d="M{left} {y}H{right}" stroke="#42544c"/><text x="42" y="{y+4}" text-anchor="end" fill="#b0c9c7" font-size="12">{tick}</text>')
    if len(points)>1:
        elements.append('<polyline fill="none" stroke="#bdd078" stroke-width="3" points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+'"/>')
    else:elements.append('<text x="459" y="148" text-anchor="middle" fill="#c3ba8b" font-size="15">First snapshot · more days will form the curve</text>')
    for x,y in points:elements.append(f'<rect x="{x-3:.2f}" y="{y-3:.2f}" width="6" height="6" fill="#f5c86c"/>')
    labels=((left,rows[0]['date'],'start'),(right,rows[-1]['date'],'end')) if len(rows)>1 else (((left+right)/2,rows[0]['date'],'middle'),)
    for x,label,anchor in labels:
        elements.append(f'<text x="{x}" y="264" text-anchor="{anchor}" fill="#c3ba8b" font-size="12">{label}</text>')
    title=escape(history['repository']);latest=rows[-1]['stars']
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">Star history · {title}</title><desc id="description">{len(rows)} real daily snapshots. Latest: {latest} stars on {rows[-1]['date']}. No earlier history was fabricated.</desc>
<rect width="900" height="300" fill="#25252f"/><rect x="1" y="1" width="898" height="298" fill="none" stroke="#706c55" stroke-width="2"/>
<g font-family="Arial, sans-serif"><text x="30" y="36" fill="#f6eac3" font-size="22" font-weight="bold">Star history</text><text x="30" y="60" fill="#c3ba8b" font-size="13">{title} · daily snapshots (UTC+8)</text><text x="864" y="39" text-anchor="end" fill="#bdd078" font-size="26" font-weight="bold">{latest} Stars</text>{''.join(elements)}<text x="450" y="286" text-anchor="middle" fill="#90879d" font-size="11">Actual observations since {rows[0]['date']} · decreases are preserved</text></g></svg>'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--snapshot',type=Path);parser.add_argument('--repo',default=os.environ.get('GITHUB_REPOSITORY','l1jiewansui/codex-garden'));args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.repo):raise ValueError('Invalid repository')
    if args.snapshot:source=json.loads(args.snapshot.read_text(encoding='utf-8-sig'))
    else:
        headers={'Accept':'application/vnd.github+json','User-Agent':'codex-garden-star-history'}
        if os.environ.get('GH_TOKEN'):headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
        request=urllib.request.Request('https://api.github.com/repos/'+args.repo,headers=headers)
        with urllib.request.urlopen(request,timeout=30) as response:source=json.load(response)
    if source.get('full_name')!=args.repo:raise ValueError('Unexpected API repository')
    folder=ROOT/'docs/metrics';folder.mkdir(parents=True,exist_ok=True);data=folder/'star-history.json'
    previous=json.loads(data.read_text(encoding='utf-8')) if data.exists() else {}
    day=datetime.now(timezone(timedelta(hours=8))).date().isoformat()
    history=record_snapshot(previous,args.repo,source['stargazers_count'],day)
    data.write_text(json.dumps(history,indent=2)+'\n',encoding='utf-8')
    (folder/'star-history.svg').write_text(render(history),encoding='utf-8')
    print(f"Updated {args.repo}: {source['stargazers_count']} stars; {len(history['snapshots'])} daily observations")
if __name__=='__main__':main()
