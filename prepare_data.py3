#! /usr/bin/env python3.2
# -*- coding: utf-8 -*-

import sys, os, xml.etree.ElementTree as ET, re

if len(sys.argv)!=2:
    exit()

edgetypes = re.compile('C?OBJC|C?SUBJC|C?NEB|C?REL|C?OBJI|CS')
conclauseedges = re.compile('CNEB|COBJC|CSUBJC|CREL|CRES|CS')

nppattern = re.compile('(COR)?C?VOK|(COR)?C?ZEIT|RES|(COR)?C?ATTR|(COR)?C?GRAD|(COR)?C?SUBJ|(COR)?C?OBJA|(COR)?C?OBJD|(COR)?C?PN|(COR)?C?PRED|(COR)?C?GMOD|(COR)?C?OBJG|(COR)?C?APP|(COR)?C?MOD|(COR)?CJ|(COR)?EXPL')#took out |(COR)?C?KOMP
nkpattern = re.compile('N.|PPER|PRF|PIS|PDS|PPOSS|PWS')#PRELS bleibt draußen

#ppconda = re.compile('(COR)?C?OBJP|(COR)?C?MOD|APP|C?PRED|C?PN|(COR)?X.*/') #import after this node, a PN-node musst follow! Otherwise we get too much crap
pptagpattern = re.compile('APP(R?ART|O)')
pnlabelpattern = re.compile('C?(CORX?)?C?PN')
ppkonlabelpattern = re.compile('(C(CORX?)?PN)|KON|C?S') #everything else = corner cases

modpattern = re.compile('(CORX?)?(G?MOD|ATTR|REL)')

parpattern = re.compile('C?(CORX?)?PAR[^T]')

def rec_eval_embedding(tokenid, parentlevel, depth, absdepth, npsensitive, modsensitive):	
	if (not parpattern.match(funcs[tokenid])):
		slevels[tokenid]= parentlevel
		depths[tokenid]= str(depth)
		absdepths[tokenid]= str(absdepth+1)
		if (tokenid not in nprootids and nkpattern.match(postags[tokenid])):
			nprootids[tokenid]= 'N/A'	
		children = root.findall(".//*[@govIDs='"+tokenid+"']")
		edgeload[tokenid]= str(len(children))	
		for child in children:				
			sensitive=npsensitive
			ms = modsensitive
			id = child.attrib['depIDs']
			func=funcs[id]			
			coord= func=='KON' or (func[0]=='C' and func[1:2]!='OR')
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
				rec_eval_embedding(id, func, depth+(0 if conclauseedges.match(func) else 1), (absdepth if coord else absdepth+1), sensitive, ms)
			else:
				rec_eval_embedding(id, parentlevel, depth, (absdepth if coord else absdepth+1), sensitive, ms)
		

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
			coord= func=='KON' or (func[0]=='C' and func[1:2]!='OR')
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
			cmod= newfunc[0]=='C' and newfunc[1:2]!='OR'
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

slevels={}
depths={}
absdepths={}
npdepths={}
npabsdepths={}
nplevels={}
nprootids={}
edgeload={}
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
		domdomid=root.find(".//*[@depIDs='"+domid+"']").attrib['govIDs']
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
	rec_eval_embedding(rt, 'S', 0, 0, 1, 1)

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
		con = startfunc[0]=='C' and not (startfunc[1:2]=='OR')
		rec_eval_pps(pp, (startfunc if not con else funcs[govs[pp]]), (govtag if not con else postags[ govs[govs[pp]]]), 0, absdepths[pp])
	count+=1
	
count = 1
l=len(rootmods)
print('evaluating',len(rootmods),'modifiers')
for mod in rootmods:
	print('\tevaluating modifier',count,'of',l,'(',mod,')')
	count+= 1
	rec_eval_mods(mod, funcs[mod], postags[govs[mod]], 0, absdepths[mod])

basedata = 'sentence\ttoken\ttext\tlemma\tpos\tgov\tfunc\tabs_depth\tedgeload\ts_parent\tdepth\tpp_func\tpp_gov\tpp_depth\tpp_absdepth\tnp_root\tnp_root_id\tnp_depth\tnp_absdepth\tmod_func\tmod_govtag\tmod_depth\tmod_absdepth'
nl = '\n'
tab = '\t'

print('creating output')
for sentence in root.iter(nstc+'sentence'):	
	sid = 's'+sentence.attrib['tokenIDs'].split(' ')[0][1:]
	for tid in sentence.attrib['tokenIDs'].split(' '):
		if (tid in slevels or (tokens[tid]=='_') or (tid in postags and postags[tid][0]=='$')): #"_"-Elements are right now not in the exported data
			basedata+= nl+sid[1:]#the s blocks a lot
			basedata+= tab+tid
			basedata+= tab+tokens[tid]
			basedata+= tab+('N/A' if not tid in lemmas else lemmas[tid])
			basedata+= tab+('N/A' if not tid in postags else postags[tid])
			basedata+= tab+govs[tid]
			basedata+= tab+funcs[tid]
			basedata+= tab+('N/A' if not tid in absdepths else absdepths[tid])
			basedata+= tab+('N/A' if not tid in edgeload else edgeload[tid])
			basedata+= tab+('N/A' if not tid in slevels else slevels[tid])
			basedata+= tab+('N/A' if not tid in depths else depths[tid])		
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
