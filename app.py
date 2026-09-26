from flask import Flask,request,render_template_string,send_file
import requests,re,csv,io
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse,quote_plus
app=Flask(__name__)
H={'User-Agent':'Mozilla/5.0 (compatible; CardiologyVALeadFinder/3.0)'}
E=re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
P=re.compile(r'(?<!\d)(?:\+?1[\s.-]?)?\(?[2-9]\d{2}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)')
FREE={'gmail.com','outlook.com','hotmail.com','yahoo.com','icloud.com','aol.com','proton.me','protonmail.com','live.com','msn.com'}
PRE=['cardiology practice "virtual assistant" USA','cardiology "medical virtual assistant" USA','cardiologist "virtual assistant" remote USA','cardiology practice hiring virtual assistant USA','medical practice "virtual assistant" cardiology USA']
HTML='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cardiology VA Lead Finder</title><style>body{font-family:system-ui;margin:0;background:#f4f7fb;color:#172033}.wrap{max-width:900px;margin:auto;padding:16px}.card{background:#fff;border-radius:16px;padding:16px;margin:12px 0;box-shadow:0 2px 12px #0001}input,select,button{width:100%;box-sizing:border-box;padding:13px;margin:6px 0;border-radius:10px;border:1px solid #ccd4df;font-size:16px}button{background:#1769d1;color:#fff;border:0;font-weight:700}a{color:#1261b5;word-break:break-word}.pill{display:inline-block;background:#eaf2ff;padding:5px 9px;border-radius:20px;margin:3px;font-size:13px}.muted{color:#657184;font-size:14px}</style></head><body><div class="wrap"><div class="card"><h1>🇺🇸 Cardiology VA Lead Finder</h1><p class="muted">Find public U.S. cardiology/medical practices with VA or hiring signals.</p><form method="post"><select onchange="this.form.q.value=this.value">{% for p in presets %}<option>{{p}}</option>{% endfor %}</select><input name="q" value="{{q}}"><button>Find public leads</button></form></div>{% if error %}<div class="card">{{error}}</div>{% endif %}{% if rows %}<div class="card"><b>{{rows|length}} leads found</b><form method="post" action="/csv"><input type="hidden" name="data" value="{{csv_data}}"><button>Download CSV</button></form></div>{% for r in rows %}<div class="card"><h3>{{r.name}}</h3><span class="pill">Signal {{r.score}}/100</span>{% if r.signal %}<span class="pill">{{r.signal}}</span>{% endif %}<p>🌐 <a href="{{r.website}}" target="_blank">{{r.website}}</a></p>{% if r.email %}<p>📧 <a href="mailto:{{r.email}}">{{r.email}}</a></p>{% endif %}{% if r.phone %}<p>☎️ {{r.phone}}</p>{% endif %}{% if r.instagram %}<p>📸 <a href="{{r.instagram}}" target="_blank">Instagram</a></p>{% endif %}{% if r.linkedin %}<p>💼 <a href="{{r.linkedin}}" target="_blank">LinkedIn</a></p>{% endif %}<div class="muted">Public-web information; verify before outreach.</div></div>{% endfor %}{% endif %}<div class="card muted">Only public business information is processed. No private-email discovery or login/anti-bot bypass.</div></div></body></html>'''
def get(u,t=10): return requests.get(u,headers=H,timeout=t,allow_redirects=True)
def dom(u): return urlparse(u).netloc.lower().replace('www.','')
def info(u):
 try:
  r=get(u);s=BeautifulSoup(r.text,'html.parser');text=s.get_text(' ',strip=True);ig=li=''
  for a in s.find_all('a',href=True):
   x=urljoin(r.url,a['href'])
   if 'instagram.com/' in x.lower() and not ig:ig=x.split('?')[0]
   if 'linkedin.com/' in x.lower() and not li:li=x.split('?')[0]
  return {'url':r.url,'title':s.title.get_text(' ',strip=True) if s.title else '','text':text,'emails':sorted(set(E.findall(r.text))),'phones':sorted(set(P.findall(text))),'instagram':ig,'linkedin':li}
 except:return {}
def search(q):
 try:
  s=BeautifulSoup(get('https://www.bing.com/search?q='+quote_plus(q)+'&count=10',12).text,'html.parser');out=[]
  for x in s.select('li.b_algo')[:10]:
   a=x.select_one('h2 a')
   if a and a.get('href'):out.append((a.get_text(' ',strip=True),a['href']))
  return out
 except:return []
def score(t,x,u):
 s=(t+' '+x+' '+u).lower();n=0
 if 'cardiolog' in s or 'cardiac' in s or 'heart' in s:n+=40
 if 'medical' in s or 'clinic' in s or 'practice' in s:n+=20
 if 'virtual assistant' in s or 'medical va' in s or 'remote assistant' in s:n+=25
 if 'hiring' in s or 'careers' in s or 'job' in s or 'apply' in s:n+=15
 return min(n,100)
def find(q):
 seen={}
 for title,u in search(q):
  d=dom(u)
  if not d or 'bing.com' in d:continue
  p=info(u);x=p.get('text','');r=seen.setdefault(d,{'name':title,'website':u,'email':'','phone':'','instagram':'','linkedin':'','signal':'','score':0})
  r['name']=p.get('title') or title;r['website']=p.get('url') or u;r['score']=max(r['score'],score(title,x,u))
  be=[e.lower() for e in p.get('emails',[]) if e.lower().split('@')[-1] not in FREE]
  if be and not r['email']:r['email']='; '.join(be[:3])
  if p.get('phones') and not r['phone']:r['phone']='; '.join(p['phones'][:2])
  r['instagram']=r['instagram'] or p.get('instagram','');r['linkedin']=r['linkedin'] or p.get('linkedin','')
  low=x.lower();sig=[]
  if 'virtual assistant' in low:sig.append('Virtual Assistant')
  if 'medical va' in low:sig.append('Medical VA')
  if 'hiring' in low or 'careers' in low:sig.append('Hiring/Careers')
  if 'cardiology' in low:sig.append('Cardiology')
  r['signal']=', '.join(dict.fromkeys(sig))
 return sorted(seen.values(),key=lambda z:z['score'],reverse=True)[:20]
@app.route('/',methods=['GET','POST'])
def home():
 q=request.form.get('q',PRE[0]);rows=[];err=''
 if request.method=='POST':
  try:rows=find(q)
  except Exception as e:err=str(e)
 s=io.StringIO()
 if rows:
  w=csv.DictWriter(s,fieldnames=['name','website','email','phone','instagram','linkedin','signal','score']);w.writeheader();w.writerows(rows)
 return render_template_string(HTML,presets=PRE,q=q,rows=rows,error=err,csv_data=s.getvalue())
@app.route('/csv',methods=['POST'])
def csv_download():return send_file(io.BytesIO(request.form.get('data','').encode()),mimetype='text/csv',as_attachment=True,download_name='cardiology_va_leads.csv')
if __name__=='__main__':app.run(host='0.0.0.0',port=7860)
