import os, json, subprocess, platform, tempfile, gc, sys

pydir = os.path.abspath(os.path.dirname(__file__))
otfccdump = os.path.join(pydir, 'otfcc/otfccdump')
otfccbuild = os.path.join(pydir, 'otfcc/otfccbuild')
otf2otc = os.path.join(pydir, 'otf2otc.py')
outd=str()
it='a'
rmttf=False
if platform.system() in ('Mac', 'Darwin'):
	otfccdump += '1'
	otfccbuild += '1'
if platform.system() == 'Linux':
	otfccdump += '2'
	otfccbuild += '2'
TG= ('msyh', 'msjh', 'mingliu', 'simsun', 'simhei', 'msgothic', 'msmincho', 'meiryo', 'malgun', 'yugoth', 'yumin', 'batang', 'gulim', 'allsans', 'allserif', 'all', 'mingliub', 'simsunb')
WT=('thin', 'extralight', 'light', 'semilight', 'demilight', 'normal', 'regular', 'medium', 'demibold', 'semibold', 'bold', 'black', 'heavy')
end={'Thin':'th', 'ExtraLight':'xl', 'Light':'l', 'Semilight':'sl', 'DemiLight':'dm', 'Normal':'nm', 'Regular':'', 'Medium':'md', 'Demibold':'db', 'SemiBold':'sb', 'Bold':'bd', 'Black':'bl', 'Heavy':'hv'}

def getwt(font):
	if 'macStyle' in font['head'] and 'bold' in font['head']['macStyle'] and font['head']['macStyle']['bold']:
		return 'Bold'
	wtn={250:'ExtraLight', 300:'Light', 350:'Normal', 400:'Regular', 500:'Medium', 600:'SemiBold', 900:'Heavy'}
	wtc=font['OS_2']['usWeightClass']
	if wtc<300:
		return wtn[250]
	if wtc in wtn:
		return wtn[wtc]
	return 'Regular'

def setuswt(font, wt):
	uswt={'thin':100, 'extralight':250, 'light':300, 'semilight':350, 'demilight':350, 'normal':350, 'regular':400, 'medium':500, 'demibold':600, 'semibold':600, 'bold':700, 'black':900, 'heavy':900}
	font['OS_2']['usWeightClass']=uswt[wt]
	font['OS_2']['fsSelection']['bold']=wt=='bold'
	font['OS_2']['fsSelection']['regular']=(wt=='regular' and it!='y')
	font['head']['macStyle']['bold']=wt=='bold'

def getit(font):
	if 'macStyle' in font['head'] and 'italic' in font['head']['macStyle'] and font['head']['macStyle']['italic']:
		return 'y'
	return 'n'

def setit(font, isit):
	font['OS_2']['fsSelection']['italic']=isit
	if isit:
		font['OS_2']['fsSelection']['regular']=False
	font['head']['macStyle']['italic']=isit

def getver(nmo):
	for n1 in nmo:
		if n1['languageID']==1033 and n1['nameID']==5:
			return n1['nameString'].split(' ')[-1]
	return 1

def mktmp(font):
	tmp = tempfile.mktemp('.json')
	with open(tmp, 'w', encoding='utf-8') as f:
		f.write(json.dumps(font))
	return tmp

def otpth(ftf):
	if outd:
		return os.path.join(outd, ftf)
	return ftf

def svtottf(jsf, ttff):
	subprocess.run((otfccbuild, '--keep-modified-time', '--keep-average-char-width', '-O2', '-q', '-o', ttff, jsf))
	os.remove(jsf)

def wtbuil(nml, wt):
	nwtnm=list()
	for n1 in nml:
		n2=dict(n1)
		if n2['nameID'] in (1, 3, 4, 6, 17):
			n2['nameString']=n2['nameString'].replace('Light', wt)
		nwtnm.append(n2)
	return nwtnm

def itbuil(nms):
	nwtnm=list()
	isbold=False
	for n1 in nms:
		if n1['nameID']==2 and 'Bold' in n1['nameString']:
			isbold=True
			break
	for n1 in nms:
		n2=dict(n1)
		if n2['nameID']==2:
			if 'Italic' in n2['nameString']:
				return nms
			if isbold:
				n2['nameString']='Bold Italic'
			else:
				n2['nameString']='Italic'
		elif n2['nameID'] in (3, 4, 17):
			n2['nameString']+=' Italic'
		elif n2['nameID']==6:
			if '-' in n2['nameString']:
				n2['nameString']+='Italic'
			else:
				n2['nameString']+='-Italic'
		nwtnm.append(n2)
	return nwtnm

def bldttfft(font, tgft, wt):
	ncfg=json.load(open(os.path.join(pydir, f'names/{tgft}.json'), 'r', encoding = 'utf-8'))
	font['OS_2']['ulCodePageRange1']=ncfg['ulCodePageRange1']
	if tgft=='malgun':wts=('Regular', 'Bold', 'Semilight', 'Light')
	elif tgft=='yumin':wts=('Regular', 'Bold', 'Demibold', 'Light')
	else:wts=('Regular', 'Bold', 'Light')
	if wt not in wts: nmslist=wtbuil(ncfg[tgft+'l'], wt)
	else: nmslist=ncfg[tgft+end[wt]]
	ttflist=otpth(tgft+end[wt]+'.ttf')
	if it=='y':
		nmslist=itbuil(nmslist)
		ttflist=otpth(tgft+end[wt]+'It.ttf')
	font['head']['fontRevision']=float(getver(nmslist))
	font['name']=nmslist
	print('正在生成字体...')
	tmpf=mktmp(font)
	del font
	gc.collect()
	print('正在保存TTF...')
	svtottf(tmpf, ttflist)
	print('完成!')

def bldttcft(font, tgft, wt):
	ncfg=json.load(open(os.path.join(pydir, f'names/{tgft}.json'), 'r', encoding = 'utf-8'))
	font['OS_2']['ulCodePageRange1']=ncfg['ulCodePageRange1']
	spwt=dict()
	isit=it=='y'
	if tgft in ('msyh', 'msjh', 'meiryo'):
		if wt not in ('Regular', 'Bold', 'Light'):
			nmslist=[wtbuil(ncfg[tgft+'l'], wt), wtbuil(ncfg[tgft+'ui'+'l'], wt)]
		else:
			nmslist=[ncfg[tgft+end[wt]], ncfg[tgft+'ui'+end[wt]]]
		edl=end[wt]
		if tgft=='meiryo': edl=end[wt].replace('bd', 'b')
		ttflist=[otpth(tgft+edl+'.ttf'), otpth(tgft+'ui'+edl+'.ttf')]
		ttcfil=otpth(tgft+edl+'.ttc')
	elif tgft=='simsun':
		if wt not in ('Regular', 'Bold', 'Light'):
			nmslist=[wtbuil(ncfg[tgft+'l'], wt), wtbuil(ncfg['n'+tgft+'l'], wt)]
		else:
			nmslist=[ncfg[tgft+end[wt]], ncfg['n'+tgft+end[wt]]]
		ttflist=[otpth(tgft+end[wt]+'.ttf'), otpth('p'+tgft+end[wt]+'.ttf')]
		ttcfil=otpth(tgft+end[wt]+'.ttc')
	elif tgft in ('mingliu', 'mingliub'):
		if wt not in ('Regular', 'Bold', 'Light'):
			nmslist=[wtbuil(ncfg[tgft+'l'], wt), wtbuil(ncfg['p'+tgft+'l'], wt), wtbuil(ncfg[tgft+'_hkscsl'], wt)]
		else:
			nmslist=[ncfg[tgft+end[wt]], ncfg['p'+tgft+end[wt]], ncfg[tgft+'_hkscs'+end[wt]]]
		ttflist=[otpth(tgft+end[wt]+'.ttf'), otpth('p'+tgft+end[wt]+'.ttf'), otpth(tgft+'_hkscs'+end[wt]+'.ttf')]
		ttcfil=otpth(tgft+end[wt]+'.ttc')
	elif tgft=='msgothic':
		if wt not in ('Regular', 'Bold', 'Light'):
			nmslist=[wtbuil(ncfg[tgft+'l'], wt), wtbuil(ncfg['msuigothicl'], wt), wtbuil(ncfg['mspgothicl'], wt)]
		else:
			nmslist=[ncfg[tgft+end[wt]], ncfg['msuigothic'+end[wt]], ncfg['mspgothic'+end[wt]]]
		ttflist=[otpth(tgft+end[wt]+'.ttf'), otpth('msuigothic'+end[wt]+'.ttf'), otpth('mspgothic'+end[wt]+'.ttf')]
		ttcfil=otpth(tgft+end[wt]+'.ttc')
	elif tgft=='msmincho':
		if wt not in ('Regular', 'Bold', 'Light'):
			nmslist=[wtbuil(ncfg[tgft+'l'], wt), wtbuil(ncfg['mspminchol'], wt)]
		else:
			nmslist=[ncfg[tgft+end[wt]], ncfg['mspmincho'+end[wt]]]
		ttflist=[otpth(tgft+end[wt]+'.ttf'), otpth('mspmincho'+end[wt]+'.ttf')]
		ttcfil=otpth(tgft+end[wt]+'.ttc')
	elif tgft=='batang':
		if wt not in ('Regular', 'Bold', 'Light'):
			nmslist=[wtbuil(ncfg[tgft+'l'], wt), wtbuil(ncfg['batangchel'], wt), wtbuil(ncfg['gungsuhl'], wt), wtbuil(ncfg['gungsuhchel'], wt)]
		else:
			nmslist=[ncfg[tgft+end[wt]], ncfg['batangche'+end[wt]], ncfg['gungsuh'+end[wt]], ncfg['gungsuhche'+end[wt]]]
		ttflist=[otpth(tgft+end[wt]+'.ttf'), otpth('batangche'+end[wt]+'.ttf'), otpth('gungsuh'+end[wt]+'.ttf'), otpth('gungsuhche'+end[wt]+'.ttf')]
		ttcfil=otpth(tgft+end[wt]+'.ttc')
	elif tgft=='gulim':
		if wt not in ('Regular', 'Bold', 'Light'):
			nmslist=[wtbuil(ncfg[tgft+'l'], wt), wtbuil(ncfg['gulimchel'], wt), wtbuil(ncfg['dotuml'], wt), wtbuil(ncfg['dotumchel'], wt)]
		else:
			nmslist=[ncfg[tgft+end[wt]], ncfg['gulimche'+end[wt]], ncfg['dotum'+end[wt]], ncfg['dotumche'+end[wt]]]
		ttflist=[otpth(tgft+end[wt]+'.ttf'), otpth('gulimche'+end[wt]+'.ttf'), otpth('dotum'+end[wt]+'.ttf'), otpth('dotumche'+end[wt]+'.ttf')]
		ttcfil=otpth(tgft+end[wt]+'.ttc')
	elif tgft=='yugoth':
		if wt =='Regular':
			nmslist=[ncfg['yugoth'], ncfg['yugothuisl']]
			ttflist=[otpth('YuGothR.ttf'), otpth('YuGothuiSL.ttf')]
			spwt[1]='semilight'
			ttcfil=otpth('YuGothR.ttc')
		elif wt =='Bold':
			nmslist=[ncfg['yugothbd'], ncfg['yugothuibd'], ncfg['yugothuisb']]
			ttflist=[otpth('YuGothB.ttf'), otpth('YuGothuiB.ttf'), otpth('YuGothuiSB.ttf')]
			spwt[2]='semibold'
			ttcfil=otpth('YuGothB.ttc')
		elif wt =='Medium':
			nmslist=[ncfg['yugothmd'], ncfg['yugothui']]
			ttflist=[otpth('YuGothM.ttf'), otpth('YuGothuiR.ttf')]
			ttcfil=otpth('YuGothM.ttc')
			spwt[1]='regular'
		elif wt =='Light':
			nmslist=[ncfg['yugothl'], ncfg['yugothuil']]
			ttflist=[otpth('YuGothL.ttf'), otpth('YuGothuiL.ttf')]
			ttcfil=otpth('YuGothL.ttc')
		else:
			nmslist=[wtbuil(ncfg['yugothl'], wt), wtbuil(ncfg['yugothuil'], wt)]
			ttflist=[otpth('YuGoth'+end[wt].upper()+'.ttf'), otpth('YuGothui'+end[wt].upper()+'.ttf')]
			ttcfil=otpth('YuGoth'+end[wt].upper()+'.ttc')
	if isit:
		nmslist=[itbuil(nm) for nm in nmslist]
		ttflist=[ttfl.replace('.ttf', 'It.ttf') for ttfl in ttflist]
		ttcfil=ttcfil.replace('.ttc', 'It.ttc')
	print('正在生成字体...')
	tmpf=list()
	wtcls=font['OS_2']['usWeightClass']
	isbd='fsSelection' in font['OS_2'] and 'bold' in font['OS_2']['fsSelection'] and font['OS_2']['fsSelection']['bold']
	isrg='fsSelection' in font['OS_2'] and 'regular' in font['OS_2']['fsSelection'] and font['OS_2']['fsSelection']['regular']
	for i in range(len(nmslist)):
		font['head']['fontRevision']=float(getver(nmslist[i]))
		font['name']=nmslist[i]
		if i in spwt:
			setuswt(font, spwt[i])
		tmpf.append(mktmp(font))
		font['OS_2']['usWeightClass']=wtcls
		font['OS_2']['fsSelection']['bold']=isbd
		font['OS_2']['fsSelection']['regular']=isrg
		font['head']['macStyle']['bold']=isbd
	del font
	gc.collect()
	print('正在保存TTFs...')
	for i in range(len(nmslist)):
		svtottf(tmpf[i], ttflist[i])
	print('正在生成TTC...')
	ttcarg=['python', otf2otc, '-o', ttcfil]
	ttcarg+=ttflist
	subprocess.run(tuple(ttcarg))
	if rmttf:
		for tpttf in ttflist: os.remove(tpttf)
	print('完成!')

def parseArgs(args):
	global outd, rmttf, it
	inFilePath, outDir, tarGet, weight=(str() for i in range(4))
	i, argn = 0, len(args)
	while i < argn:
		arg  = args[i]
		i += 1
		if arg == "-i":
			inFilePath = args[i]
			i += 1
		elif arg == "-d":
			outDir = args[i]
			i += 1
		elif arg == "-wt":
			weight = args[i]
			i += 1
		elif arg == "-it":
			it = args[i]
			i += 1
		elif arg == "-tg":
			tarGet = args[i].lower()
			i += 1
		elif arg == "-r":
			rmttf = True
		else:
			raise RuntimeError("Unknown option '%s'." % (arg))
	if not inFilePath:
		raise RuntimeError("You must specify one input font.")
	if not os.path.isfile(inFilePath):
		raise FileNotFoundError(f"Can not find file \"{inFilePath}\".\n")
	if not tarGet:
		raise RuntimeError(f"You must specify target.{TG}")
	elif tarGet not in TG:
		raise RuntimeError(f"Unknown target \"{tarGet}\"，please use {TG}.\n")

	if it.lower() not in ('a', 'y', 'n'):
		raise RuntimeError(f'Unknown italic setting "{it}"，please use "y" or "n".\n')
	if weight:
		if weight.lower() not in WT:
			raise RuntimeError(f'Unknown weight "{weight}"，please use {tuple(end.keys())}.\n')
		weight=weight.lower()
		if weight=='extralight': weight='ExtraLight'
		elif weight=='semibold': weight='SemiBold'
		elif weight=='demilight': weight='DemiLight'
		else: weight=weight.capitalize()
	if outDir:
		if not os.path.isdir(outDir):
			raise RuntimeError(f"Can not find directory \"{outDir}\".\n")
		else:
			outd=outDir
	return inFilePath, tarGet, weight

def run(args):
	global it
	ftin, tg, setwt=parseArgs(args)
	print('正在载入字体...')
	font = json.loads(subprocess.check_output((otfccdump, '--no-bom', ftin)).decode("utf-8", "ignore"))
	if it=='a':
		it=getit(font)
	else:
		setit(font, it=='y')
	if not setwt:
		setwt=getwt(font)
	else:
		setuswt(font, setwt.lower())
	if tg in ('malgun', 'all', 'allsans'):
		bldttfft(font, 'malgun', setwt)
	if tg in ('simhei', 'all', 'allsans'):
		bldttfft(font, 'simhei', setwt)
	if tg in ('yumin', 'all', 'allserif'):
		bldttfft(font, 'yumin', setwt)
	if tg=='all':
		for stg in ('msyh', 'msjh', 'mingliu', 'simsun', 'yugoth', 'msgothic', 'msmincho', 'meiryo', 'batang', 'gulim'):
			bldttcft(font, stg, setwt)
	elif tg=='allsans':
		for stg in ('msyh', 'msjh', 'yugoth', 'msgothic', 'meiryo', 'gulim'):
			bldttcft(font, stg, setwt)
	elif tg=='allserif':
		for stg in ('mingliu', 'simsun', 'msmincho', 'batang'):
			bldttcft(font, stg, setwt)
	elif tg=='simsunb':
		bldttfft(font, tg, setwt)
	elif tg not in ('malgun', 'simhei', 'yumin'):
		bldttcft(font, tg, setwt)
	print('结束!')

def main():
	run(sys.argv[1:])

if __name__ == "__main__":
	main()
