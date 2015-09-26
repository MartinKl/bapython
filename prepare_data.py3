#! /usr/bin/env python3.2
# -*- coding: utf-8 -*-

import sys, os, xml.etree.ElementTree as ET, re

if len(sys.argv)<2:
    exit()

all = len(sys.argv)>2 and sys.argv[2]=="all"

edgetypes = re.compile('C?(COR)?X?OBJC|C?(COR)?X?SUBJC|C?(COR)?X?NEB|C?(COR)?X?REL|C?(COR)?X?OBJI|C(COR)?X?S')
conclauseedges = re.compile('C(COR)?X?NEB|C(COR)?X?OBJC|C(COR)?X?SUBJC|C(COR)?X?REL|C(COR)?X?RES|C(COR)?X?OBJI|C(COR)?X?S')

nppattern = re.compile('(COR)?X?C?VOK|(COR)?X?C?ZEIT|RES|(COR)?X?C?ATTR|(COR)?X?C?GRAD|(COR)?X?C?SUBJ|(COR)?X?C?OBJA|(COR)?X?C?OBJD|(COR)?X?C?PN|(COR)?X?C?PRED|(COR)?X?C?GMOD|(COR)?X?C?OBJG|(COR)?X?C?APP|(COR)?X?C?MOD|(COR)?X?CJ|(COR)?X?EXPL')#took out |(COR)?C?KOMP
nkpattern = re.compile('N.|PPER|PRF|PIS|PDS|PPOSS|PWS')#PRELS bleibt draußen

#ppconda = re.compile('(COR)?C?OBJP|(COR)?C?MOD|APP|C?PRED|C?PN|(COR)?X.*/') #import after this node, a PN-node musst follow! Otherwise we get too much crap
pptagpattern = re.compile('APP(R?ART|O)')
pnlabelpattern = re.compile('C?(COR)?X?C?PN')
ppkonlabelpattern = re.compile('(C(COR)?X?PN)|KON|C?S') #everything else = corner cases

modpattern = re.compile('(COR)?X?(G?MOD|ATTR|REL)')#we leave appositions out

argpattern = re.compile('(COR)?X?(OBJ(A|D|G|P)|PRED)')

sbjpattern = re.compile('(COR)?X?SUBJ')

mdpattern = re.compile('(COR)?X?(G?MOD|ATTR)')

prtpattern = re.compile('(COR)?X?(AVZ|PART)')

parpattern = re.compile('C?(COR)?X?(PAR[^T]?|PRES|DR.*)')

ppnpattern = re.compile('(COR)?X?PN')

def rec_eval_embedding(tokenid, parentlevel, depth, absdepth, npsensitive, modsensitive):			
	if (not parpattern.match(funcs[tokenid])): #PRES and DR also out!
		slevels[tokenid]= parentlevel
		depths[tokenid]= str(depth)
		absdepths[tokenid]= str(absdepth)
		if (tokenid not in nprootids and nkpattern.match(postags[tokenid])):
			nprootids[tokenid]= 'N/A'	
		children = root.findall(".//*[@govIDs='"+tokenid+"']")
		edgeload[tokenid]= str(len(children))
		subj=0
		args=0#
		mods=0#
		dete=0
		mdfs=0#rest
		clse=0#
		cooe=0#
		auxe=0#	
		prte=0#
		corx=0#
		obji=0
		ppne=0
		descs=len(children)
		for child in children:				
			sensitive=npsensitive
			ms = modsensitive
			id = child.attrib['depIDs']
			func=funcs[id]			
			coord= func=='KON' or (func[0]=='C' and func[1:3]!='OR')
			mdfs+=1					
			if (func=='OBJI'):
				obji+=1 ##objis are counted twice	
			elif (coord):
				cooe+=1
				mdfs-=1
				descs-=1 #coordinating nodes do not count as descendant				
			elif (argpattern.match(func)):
				args+=1
				mdfs-=1
			elif (sbjpattern.match(func)):
				subj+=1
				mdfs-=1
			elif (mdpattern.match(func)):
				mods+=1
				mdfs-=1
			elif (func=='DET'):
				dete+=1
				mdfs-=1
			elif (ppnpattern.match(func)):
				ppne+=1
				mdfs-=1			
			elif (func=='AUX'):
				auxe+=1	
				mdfs-=1
			elif (prtpattern.match(func)):
				prte+=1
				mdfs-=1
			if (func[0:3]=='COR'):
				corx+=1
			if (sensitive and nppattern.match(func) and nkpattern.match(postags[id])):
				sensitive=0
				rootnps.append(id)								
				nprootids[node]=tokenid
			if (pnlabelpattern.match(func)):#no elif!			
				pproots.append(tokenid)
			elif (ms and modpattern.match(func)):
				rootmods.append(id)
				modgovtags[id] = postags[tokenid]
				ms= 0
			if (edgetypes.match(func)):								
				if (not coord):
					mdfs-=1
					clse+=1
				descs+=rec_eval_embedding(id, func, depth+(0 if conclauseedges.match(func) else 1), (absdepth if coord else absdepth+1), sensitive, ms)
			else:
				descs+=rec_eval_embedding(id, parentlevel, depth, (absdepth if coord else absdepth+1), sensitive, ms)
				
		sbjedges[tokenid]= str(subj)
		argedges[tokenid]= str(args)
		modedges[tokenid]= str(mods)
		mdfedges[tokenid]= str(mdfs)
		clsedges[tokenid]= str(clse)
		crdedges[tokenid]= str(cooe)
		auxedges[tokenid]= str(auxe)
		prtedges[tokenid]= str(prte)
		coredges[tokenid]= str(corx)
		detedges[tokenid]= str(dete)
		iobedges[tokenid]= str(obji)
		ppnedges[tokenid]= str(ppne)
		#TEST:
		if (ppne+subj+dete+args+mods+mdfs+clse+cooe+auxe+prte!=len(children)):
			print('error with edgeload splitting',tokenid,':')
			print(' ',str(subj),'subj')
			print('+',str(args),'args')
			print('+',str(mods),'mods')
			print('+',str(mdfs),'mdfs')
			print('+',str(clse),'clse')
			print('+',str(cooe),'cooe')
			print('+',str(auxe),'auxe')
			print('+',str(prte),'prte')
			print('+',str(dete),'dete')
			print('+',str(ppne),'ppne')
			print('----')
			print('?',edgeload[tokenid])
			exit()
		descendants[tokenid]=str(descs)
		return descs
	else:
		print(funcs[tokenid],'ignored')
		write_to_blacklist(tokenid)
		gid=govs[tokenid]
		if (gid in edgeload):
			e = int(edgeload[gid])
			edgeload[gid]= str(e-1)
		if (gid in mdfedges):
			m = int(mdfedges[gid])
			mdfedges[gid] = str(m-1)
		return -1
		
def write_to_blacklist(tokenid):
	blacklist.append(tokenid)
	children = root.findall(".//*[@govIDs='"+tokenid+"']")
	for child in children:
		write_to_blacklist(child.attrib['depIDs'])

def rec_eval_nps(tokenid, gov, root_id, depth, absdepth):
	if (not parpattern.match(funcs[tokenid])):
		npdepths[tokenid]= str(depth)
		npabsdepths[tokenid]= str(absdepth)
		nplevels[tokenid]= gov
		nprootids[tokenid]= root_id
		children = root.findall(".//*[@govIDs='"+tokenid+"']")
		for child in children:
			id = child.attrib['depIDs']
			func = funcs[id]
			coord= func=='KON' or (func[0]=='C' and func[1:3]!='OR')
			if (nppattern.match(func) and nkpattern.match(postags[id])):			
				rec_eval_nps(id, func, tokenid, (depth if coord else depth+1), (absdepth if coord else absdepths[id]))
			else:
				rec_eval_nps(id, gov, root_id, depth, absdepth)
	
def rec_eval_pps(startid, func, ppgovtag, depth, absdepth): #func is the function of the whole pp, highest priority has the embedded pp
	if (not parpattern.match(funcs[startid])):
		ppdepths[startid]= str(depth)
		ppabsdepths[startid]= str(absdepth)
		ppfuncs[startid]= func
		ppgovtags[startid]= ppgovtag
		children = root.findall(".//*[@govIDs='"+startid+"']")
		for child in children:
			id = child.attrib['depIDs']		
			newfunc = funcs[id]
			newpp = (pptagpattern.match(postags[id]) and not ppkonlabelpattern.match(newfunc))
			rec_eval_pps(id, (newfunc if newpp else func), (postags[startid] if newpp else ppgovtag), (depth+1 if newpp else depth), (absdepths[id] if newpp else absdepth))
		
def rec_eval_mods(startid, func, govtag, depth, absdepth):
	if (not parpattern.match(funcs[startid])):
		moddepths[startid]= str(depth)
		modabsdepths[startid]= str(absdepth)
		modfuncs[startid]= func
		modgovtags[startid]= govtag
		children = root.findall(".//*[@govIDs='"+startid+"']")
		for child in children:
			id= child.attrib['depIDs']
			newfunc=funcs[id]
			newmod= modpattern.match(funcs[id])
			cmod= newfunc[0]=='C' and newfunc[1:3]!='OR'
			rec_eval_mods(id, (newfunc if newmod else (newfunc if cmod else func)), (postags[startid] if newmod else govtag), (depth+1 if newmod else depth), (absdepths[id] if newmod else absdepth))



i=0
file=sys.argv[1]
xmltree = ET.parse(file)
root = xmltree.getroot()
nstc = '{http://www.dspin.de/data/textcorpus}'
print('parsed file=',file,'root=',root)
tokens={}
govs={}#I'm really happy to have this dict
funcs={}
#now we can work
for token in root.iter(nstc+'token'):
	tokens[token.attrib['ID']]=token.text
	govs[token.attrib['ID']]='N/A'
	funcs[token.attrib['ID']]=('ROOT' if token.text=='_' else 'N/A')

lemmas={}
for lemma in root.iter(nstc+'lemma'):
	lemmas[lemma.attrib['tokenIDs']]=lemma.text

postags={}
for postag in root.iter(nstc+'tag'):
	postags[postag.attrib['tokenIDs']]=postag.text

for dependency in root.iter(nstc+'dependency'):	
	gov=dependency.attrib['govIDs']
	dep=dependency.attrib['depIDs']
	if (len(gov.split(' '))>1):
		print('Error: Multigovs!')
		exit()
	#tcf from standalone webanno: no root dependencies -> actually not all nostad files use root either
	govs[dep]= (gov if gov!=dep else 'N/A')
	funcs[dep]=dependency.attrib['func']



#todo: skip PTKANT-sentences for bematac -> we can simple skip all sentences ending with the sequence POS="PTKANT" . POS="$.", there's only
#one occurence in TuebaDZ, but this one has no dependency annotation -> do it afterwards?

print('collecting nodes by function')

#embedding
##collect roots
roots=[]
rootnps=[]
pproots=[]
rootmods=[]

blacklist=[] #we introduce a blacklist, to FINALLY keep parentheses out (blacklist is faster)

slevels={}
depths={}
absdepths={}
npdepths={}
npabsdepths={}
nplevels={}
nprootids={}
edgeload={}
descendants={}
sbjedges={}
argedges={}
modedges={}
mdfedges={}
clsedges={}
crdedges={}
auxedges={}
prtedges={}
coredges={}
detedges={}
iobedges={}
ppnedges={}
ppgovtags={}
ppfuncs={}
ppdepths={}
ppabsdepths={}
modgovtags={}
modfuncs={}
moddepths={}
modabsdepths={}
for node in funcs.keys():	
	func=funcs[node]			
	if (func=='S'):
		roots.append(node)
		slevels[node]='S'
		depths[node]='0'
	elif (func=='CS'):
		domid=root.find(".//*[@depIDs='"+node+"'][@func='CS']").attrib['govIDs']
		domdom= root.find(".//*[@depIDs='"+domid+"']")
		if (not domdom is None):
			domdomid= domdom.attrib['govIDs']
			if (funcs[domid]=='KON' and tokens[domdomid]=='_'):
				roots.append(node)
				slevels[node]='S'
				slevels[domid]='S'
				depths[node]='0'	
				depths[domid]='0'		
	#else:
	#	slevels[node]=('S' if func!='N/A' else 'N/A')
	#	depths[node]=('0' if func!='N/A' else 'N/A')		
		#if (ppconda.match(func) and not root.find(".//[@govIDs='"+node+"'][@func='PN'") is None):
		#	#jippy, we found a PP -> maybe we should simply mark it, attention: coordinated PNs
		#	print('')
		#else:
		
		
print('evaluating (embedded) clauses and collecting root-nps, all pps and root-modifiers')

count = 1
l=len(roots)
for rt in roots:
	print('\tevaluating S-Node',count,'of',l)
	count+=1
	descendants[rt] = str(rec_eval_embedding(rt, 'S', 0, 0, 1, 1))

if (all):
	print('evaluating NPs')

	count = 1
	l=len(rootnps)
	for np in rootnps:
		print('\tevaluating root-np',count,'of',l,'(',np,')')
		count+=1
		rec_eval_nps(np, funcs[np], root.find(".//*[@depIDs='"+np+"']").attrib['govIDs'], 0, absdepths[np])

	count = 1
	l=len(pproots)
	print('evaluating',len(pproots),'PPs')
	for pp in pproots:#this is buggy ... it assumes that the first element in the list is not already embedded which cannot be assured with python (maybe it's not buggy, but redundant, since it will overwrite things already done... check it
		if (not pp in ppfuncs):
			print('\tevaluating pp',count,'of',l,'(',pp,')')				
			govtag = postags[ govs[pp] ]
			startfunc = funcs[pp]
			con = startfunc[0]=='C' and not (startfunc[1:3]=='OR')
			rec_eval_pps(pp, (startfunc if not con else funcs[govs[pp]]), (govtag if not con else postags[ govs[govs[pp]]]), 0, absdepths[pp])
		count+=1
		
	count = 1
	l=len(rootmods)
	print('evaluating',len(rootmods),'modifiers')
	for mod in rootmods:
		print('\tevaluating modifier',count,'of',l,'(',mod,')')
		count+= 1
		rec_eval_mods(mod, funcs[mod], postags[govs[mod]], 0, absdepths[mod])



basedata = 'sentence\tsrun\ttoken\ttext\tlemma\tpos\tgov\tfunc\tgovpos\tgovfunc\tabs_depth\tedgeload\tdescendants\tsbj_edges\targ_edges\tmod_edges\tdet_edges\tpn_edges\tmdf_edges\tclause_edges\tcoord_edges\taux_edges\tpart_edges\tcorrections\tobji\ts_parent\tdepth'+('\tpp_func\tpp_gov\tpp_depth\tpp_absdepth\tnp_root\tnp_root_id\tnp_depth\tnp_absdepth\tmod_func\tmod_govtag\tmod_depth\tmod_absdepth' if all else '')
nl = '\n'
tab = '\t'


print('creating output')
for sentence in root.iter(nstc+'sentence'):	
	sid = 's'+sentence.attrib['tokenIDs'].split(' ')[0][1:]
	srun=0
	for tid in sentence.attrib['tokenIDs'].split(' '):
		if (not tid in blacklist): #and tid in slevels or (tokens[tid]=='_') or (tid in postags and postags[tid][0]=='$')): 
			srun+=1
			basedata+= nl+sid[1:]#the s blocks a lot
			basedata+= str(srun)
			basedata+= tab+tid
			basedata+= tab+tokens[tid]
			basedata+= tab+('N/A' if not tid in lemmas else lemmas[tid])
			basedata+= tab+('N/A' if not tid in postags else postags[tid])
			g=govs[tid]
			basedata+= tab+g
			basedata+= tab+funcs[tid]
			basedata+= tab+('N/A' if not g in postags else postags[g])			
			basedata+= tab+('N/A' if not g in funcs else funcs[g])			
			basedata+= tab+('N/A' if not tid in absdepths else absdepths[tid])
			basedata+= tab+('N/A' if not tid in edgeload else edgeload[tid])			
			basedata+= tab+('N/A' if not tid in descendants else descendants[tid])			
			basedata+= tab+('N/A' if not tid in sbjedges else sbjedges[tid])
			basedata+= tab+('N/A' if not tid in argedges else argedges[tid])
			basedata+= tab+('N/A' if not tid in modedges else modedges[tid])
			basedata+= tab+('N/A' if not tid in detedges else detedges[tid])
			basedata+= tab+('N/A' if not tid in ppnedges else ppnedges[tid])
			basedata+= tab+('N/A' if not tid in mdfedges else mdfedges[tid])
			basedata+= tab+('N/A' if not tid in clsedges else clsedges[tid])
			basedata+= tab+('N/A' if not tid in crdedges else crdedges[tid])
			basedata+= tab+('N/A' if not tid in auxedges else auxedges[tid])
			basedata+= tab+('N/A' if not tid in prtedges else prtedges[tid])
			basedata+= tab+('N/A' if not tid in coredges else coredges[tid])			
			basedata+= tab+('N/A' if not tid in iobedges else iobedges[tid])	
			basedata+= tab+('N/A' if not tid in slevels else slevels[tid])			
			basedata+= tab+('N/A' if not tid in depths else depths[tid])	
			if (all):	
				basedata+= tab+('N/A' if not tid in ppfuncs else ppfuncs[tid])
				basedata+= tab+('N/A' if not tid in ppgovtags else ppgovtags[tid])
				basedata+= tab+('N/A' if not tid in ppdepths else ppdepths[tid])		
				basedata+= tab+('N/A' if not tid in ppabsdepths else ppabsdepths[tid])
				basedata+= tab+('N/A' if not tid in nplevels else nplevels[tid])
				basedata+= tab+('N/A' if not tid in nprootids else nprootids[tid])
				basedata+= tab+('N/A' if not tid in npdepths else npdepths[tid])			
				basedata+= tab+('N/A' if not tid in npabsdepths else npabsdepths[tid])
				basedata+= tab+('N/A' if not tid in modfuncs else modfuncs[tid])
				basedata+= tab+('N/A' if not tid in modgovtags else modgovtags[tid])
				basedata+= tab+('N/A' if not tid in moddepths else moddepths[tid])
				basedata+= tab+('N/A' if not tid in moddepths else modabsdepths[tid])
			

print('done')

#write a tsv
rslash= file[0:file.rfind('/')].rfind('/')
f = open(file[0:rslash]+'/tsv/'+file[file.rfind('/')+1:file.rfind('.')]+'_basedata.tsv','w')
f.write(basedata)
f.close()			

#TESTS:
##did I forget something?
print('TESTS:')
wordpattern = re.compile('.*[a-z].*|.*[A-Z].*')
for tid in tokens:
	if (funcs[tid]=='N/A' and wordpattern.match(tokens[tid])):
		print('[',tokens[tid],'] has no incoming edge (id=',tid,')')
