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

def render(history,theme='light'):
    import io
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager,dates as mdates,ticker
    import numpy as np
    rows=history['snapshots']
    if not rows:raise ValueError('No real snapshots available')
    font=ROOT/'docs/metrics/fonts/ArchitectsDaughter-Regular.ttf'
    font_manager.fontManager.addfont(str(font))
    family=font_manager.FontProperties(fname=font).get_name()
    dark=theme=='dark';background='#0d1117' if dark else '#ffffff';ink='#e6edf3' if dark else '#24292f'
    blue='#79c0ff' if dark else '#1677d2'
    dates=[datetime.strptime(r['date'],'%Y-%m-%d') for r in rows]
    values=[r['stars'] for r in rows]
    # Preserve caller RNG state and keep repeated renders byte-stable.
    random_state=np.random.get_state();np.random.seed(42)
    try:
        with plt.xkcd(scale=1.1,length=110,randomness=1.5),matplotlib.rc_context({'font.family':family,'svg.fonttype':'path','svg.hashsalt':'codex-garden-star-history','path.effects':[]}):
            fig,ax=plt.subplots(figsize=(9,4.4),dpi=100)
            fig.patch.set_facecolor(background);ax.set_facecolor(background)
            fig.subplots_adjust(left=.11,right=.95,top=.76,bottom=.23)
            ax.spines[['top','right']].set_visible(False)
            for spine in ax.spines.values():spine.set_color(ink);spine.set_linewidth(1.5)
            ax.tick_params(colors=ink,labelsize=11)
            ax.set_title('Star History',fontsize=25,color=ink,pad=40)
            ax.set_ylabel('GitHub Stars',fontsize=14,color=ink,labelpad=12)
            ax.set_xlabel('Date',fontsize=14,color=ink,labelpad=12)
            ax.plot(dates,values,color=blue,linewidth=2.6,marker='o',markersize=5,label=history['repository'])
            ax.legend(loc='upper left',bbox_to_anchor=(0,1.16),frameon=False,fontsize=12,labelcolor=blue)
            ax.set_ylim(-.04*max(1,max(values)),max(1,max(values))*1.2)
            ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True,nbins=5,min_n_ticks=2))
            if len(rows)==1:
                ax.set_xlim(dates[0]-timedelta(hours=12),dates[0]+timedelta(hours=12));ax.set_xticks(dates)
                ax.text(.5,.52,'First snapshot - more days will form the curve',ha='center',transform=ax.transAxes,fontsize=12,color=ink)
            else:
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=2,maxticks=5));ax.margins(x=.04)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d, %Y'))
            ax.annotate(f"{values[-1]} stars",xy=(dates[-1],values[-1]),xytext=(9,14),textcoords='offset points',fontsize=12,color=blue)
            fig.text(.5,.035,f"Daily snapshots since {rows[0]['date']} (UTC+8)",ha='center',fontsize=10,color=ink)
            stream=io.StringIO();fig.savefig(stream,format='svg',facecolor=background,metadata={'Date':None});plt.close(fig)
            svg=stream.getvalue()
    finally:np.random.set_state(random_state)
    title=escape(history['repository']);description=escape(f"{len(rows)} real daily snapshots. Latest: {values[-1]} stars on {rows[-1]['date']}. No earlier history was fabricated.")
    svg=svg.replace('<svg ','<svg role="img" aria-labelledby="star-title star-desc" ',1)
    pos=svg.index('>',svg.index('<svg '))+1
    return svg[:pos]+f'<title id="star-title">Star history - {title}</title><desc id="star-desc">{description}</desc>'+svg[pos:]

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
    (folder/'star-history-dark.svg').write_text(render(history,'dark'),encoding='utf-8')
    print(f"Updated {args.repo}: {source['stargazers_count']} stars; {len(history['snapshots'])} daily observations")
if __name__=='__main__':main()
