import re,os
paths=['01.txt','02_alternate.txt','03.txt','04.txt','05.txt','06_pdf_extracted.txt','07_alternate.txt','08_merged.txt','09.txt','10_merged.txt','11_merged.txt','12.txt','13.txt','14.txt','15_merged.txt','16_merged.txt','17.txt','18.txt','19.txt','20_merged.txt']
def cv(s):
 d={'零':0,'〇':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'两':2}; n=0;v=0
 for c in s:
  if c=='百': n+=(v or 1)*100;v=0
  elif c=='十': n+=(v or 1)*10;v=0
  else:v=d[c]
 return n+v
for i,p in enumerate(paths,1):
 s=open('railway_sources/snapshots/'+p).read(); nums={cv(x) for x in re.findall(r'第([一二三四五六七八九十百零〇两]+)条',s)}; mx=max(nums or [0]); print(i,p, 'max',mx, 'missing',','.join(map(str,[x for x in range(1,mx+1) if x not in nums])))
