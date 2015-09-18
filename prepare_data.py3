#! /usr/bin/env python3.2
# -*- coding: utf-8 -*-

import sys, os, xml.etree.ElementTree as ET, re

if len(sys.argv)!=2:
    exit()

edgetypes = re.compile('C?OBJC|C?SUBJC|C?NEB|C?REL|C?OBJI|C?RES|CS')
conclauseedges = re.compile('CNEB|COBJC|CSUBJC|CREL|CRES|CS')

nppattern = re.compile('(COR)?C?VOK|(COR)?C?ZEIT|RES|(COR)?C?ATTR|(COR)?C?GRAD|(COR)?C?SUBJ|(COR)?C?OBJA|(COR)?C?OBJD|(COR)?C?PN|(COR)?C?PRED|(COR)?C?GMOD|(COR)?C?OBJG|(COR)?C?APP|(COR)?C?MOD|(COR)?CJ|(COR)?EXPL')#took out |(COR)?C?KOMP
nkpattern = re.compile('N.|PPER')

ppconda = re.compile('(COR)?C?OBJP|(COR)?C?MOD|APP|C?PRED|C?PN|(COR)?X.*/') #import after this node, a PN-node musst follow! Otherwise we get too much crap

def rec_eval_embedding(tokenid, parentlevel, depth, npsensitive):		
	slevels[tokenid]= parentlevel
	depths[tokenid]= str(depth)
	if (tokenid not in nprootids):
		nprootids[tokenid]= 'N/A'	
	children = root.findall(".//*[@govIDs='"+tokenid+"']")
	edgeload[tokenid]= str(len(children))	
	for child in children:				
		sensitive=npsensitive
		id = child.attrib['depIDs']
		func=funcs[id]			
		if (sensitive and nppattern.match(func) and nkpattern.match(postags[id])):
			sensitive=0
			rootnps.append(id)								
			nprootids[node]=tokenid
		if (edgetypes.match(func)):			
			rec_eval_embedding(id, func, depth+(0 if conclauseedges.match(func) else 1), sensitive)
		else:
			rec_eval_embedding(id, parentlevel, depth, sensitive)
		

def rec_eval_nps(tokenid, gov, root_id, depth):
	npdepths[tokenid]= str(depth)
	nplevels[tokenid]= gov
	nprootids[tokenid]= root_id
	children = root.findall(".//*[@govIDs='"+tokenid+"']")
	for child in children:
		id = child.attrib['depIDs']
		func = funcs[id]
		if (nppattern.match(func) and nkpattern.match(postags[id])):
			
			rec_eval_nps(id, func, id, (depth if func[0]=='C' else depth+1))#errors with COR?
		else:
			rec_eval_nps(id, gov, root_id, depth)
	
	

i=0
file=sys.argv[1]
xmltree = ET.parse(file)
root = xmltree.getroot()
nstc = '{http://www.dspin.de/data/textcorpus}'
print('parsed file=',file,'root=',root)
tokens={}
govs={}
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
	#tcf from standalone webanno: no root dependencies
	govs[dep]= (gov if gov!=dep else 'N/A')
	funcs[dep]=dependency.attrib['func']



#todo: skip PTKANT-sentences for bematac -> we can simple skip all sentences ending with the sequence POS="PTKANT" . POS="$.", there's only
#one occurence in TuebaDZ, but this one has no dependency annotation -> do it afterwards?

print('collecting nodes by function')

#embedding
##collect roots
roots=[]
rootnps=[]

slevels={}
depths={}
npdepths={}
nplevels={}
nprootids={}
edgeload={}
pplevels={}
ppdepths={}
for node in funcs.keys():	
	edgeload[node]= str(0)
	func=funcs[node]			
	if (func=='S'):
		roots.append(node)
		slevels[node]='S'
		depths[node]='0'
	elif (func=='CS'):
		domid=root.find(".//*[@depIDs='"+node+"'][@func='CS']").attrib['govIDs']
		domdomid=root.find(".//*[@depIDs='"+domid+"'][@func='CS']").attrib['govIDs']
		if (funcs[domid]=='KON' and tokens[domdomid]=='_'):
			roots.append(node)
			slevels[node]='S'
			slevels[domid]='S'
			depths[node]='0'	
			depths[domid]='0'		
	else:
		slevels[node]=('S' if func!='N/A' else 'N/A')
		depths[node]=('0' if func!='N/A' else 'N/A')		
		#if (ppconda.match(func) and not root.find(".//[@govIDs='"+node+"'][@func='PN'") is None):
		#	#jippy, we found a PP -> maybe we should simply mark it, attention: coordinated PNs
		#	print('')
		#else:
		
		
print('evaluating (embedded) clauses and collecting root-nps')

kcount = 1
l=len(roots)
for rt in roots:
	print('\tevaluating S-Node',kcount,'of',l)
	kcount+=1
	rec_eval_embedding(rt, 'S', 0, 1)

#DEBUG
#for rnp in rootnps:
#	print(rnp,tokens[rnp],funcs[rnp])
#exit()
#END OF DEBUG
print('evaluating NPs')

npcount = 1
l=len(rootnps)
for np in rootnps:
	print('\tevaluating root-np',npcount,'of',l,'(',np,')')
	npcount+=1
	rec_eval_nps(np, 'N/A', root.find(".//*[@depIDs='"+np+"']").attrib['govIDs'], 0)

basedata = 'sentence\ttoken\ttext\tlemma\tpos\tgov\tfunc\tedgeload\ts_parent\tdepth\tnp_root\tnp_root_id\tnp_depth'
nl = '\n'
tab = '\t'

print('creating output')
for sentence in root.iter(nstc+'sentence'):	
	sid = 's'+sentence.attrib['tokenIDs'].split(' ')[0][1:]
	for tid in sentence.attrib['tokenIDs'].split(' '):
		basedata+= nl+sid
		basedata+= tab+tid
		basedata+= tab+tokens[tid]
		basedata+= tab+('N/A' if not tid in lemmas else lemmas[tid])
		basedata+= tab+('N/A' if not tid in postags else postags[tid])
		basedata+= tab+govs[tid]
		basedata+= tab+funcs[tid]
		basedata+= tab+edgeload[tid]
		basedata+= tab+slevels[tid]
		basedata+= tab+depths[tid]
		basedata+= tab+('N/A' if not tid in nplevels else nplevels[tid])
		basedata+= tab+('N/A' if not tid in nprootids else nprootids[tid])
		basedata+= tab+('N/A' if not tid in npdepths else npdepths[tid])
		

print('done')

#write a tsv
f = open(file[0:file.rfind('.')]+'_basedata.tsv','w')
f.write(basedata)
f.close()			

#TESTS:
##did I forget something?
print('TESTS:')
wordpattern = re.compile('.*[a-z].*|.*[A-Z].*')
for tid in tokens:
	if (funcs[tid]=='N/A' and wordpattern.match(tokens[tid])):
		print('[',tokens[tid],'] has no incoming edge (id=',tid,')')
