# Re-render only the overlay chunks touched by a caption fix; other chunks are reused from the previous parts version.
import subprocess,sys,os,shutil,json,glob,time
ROOT='/Volumes/bguzelassd/edicao-por-ia';J=f'{ROOT}/jobs/{sys.argv[1]}';S=J+'/studio';OLD,NEW,FROM=sys.argv[2],sys.argv[3],int(sys.argv[4])
PY=ROOT+'/.venv/bin/python'
insp=json.loads(subprocess.run([PY,ROOT+'/factory.py','studio','render',S+'/scene/spec.json','--inspect'],capture_output=True,text=True).stdout)
B=insp.get('bundle_sha256') or insp.get('bundle');open(S+'/bundle.txt','w').write(B)
N=json.load(open(S+'/scene/spec.json'))['duration_frames'];CH=240;OUT=f'{S}/parts-{NEW}';os.makedirs(OUT,exist_ok=True)
for c in range(0,N,CH):
    part=f'{OUT}/part_{c:05d}.mov'
    if os.path.exists(part):continue
    if c+CH<=FROM:
        os.link(f'{S}/parts-{OLD}/part_{c:05d}.mov',part);continue
    fr=list(range(c,min(N,c+CH)));d=f'{S}/tmp_chunk';shutil.rmtree(d,ignore_errors=True);t0=time.time()
    r=subprocess.run([PY,ROOT+'/factory.py','studio','render',S+'/scene/spec.json','--approve-bundle',B,'--frames',','.join(map(str,fr)),'--frame-budget',str(N),'--outdir',d],capture_output=True,text=True)
    if r.returncode:print('RENDER FAIL',c,r.stdout[-400:],r.stderr[-400:]);sys.exit(1)
    e=subprocess.run(['ffmpeg','-y','-v','error','-framerate','30','-start_number',str(c),'-i',d+'/%06d.png','-frames:v',str(len(fr)),'-c:v','prores_ks','-profile:v','4444','-pix_fmt','yuva444p10le',part+'.tmp.mov'],capture_output=True,text=True)
    if e.returncode:print('ENC FAIL',c,e.stderr[-400:]);sys.exit(1)
    os.rename(part+'.tmp.mov',part);shutil.rmtree(d,ignore_errors=True);print('rendered',c,len(fr),round(time.time()-t0,1),flush=True)
print('done',sys.argv[1],len(glob.glob(OUT+'/part_*.mov')))
