#! /usr/bin/env python3.2
# -*- coding: utf-8 -*-

import sys, os, xml.etree.ElementTree as ET, re

if len(sys.argv)!=2:
    exit()
    
file=sys.argv[1]
xmltree = ET.parse(file)
root = xmltree.getroot()

nstc = '{http://www.dspin.de/data/textcorpus}'
govs={}
for dep in root.iter(nstc+'dependency'):
	govid = dep.attrib['govIDs']
	depid = dep.attrib['depIDs']
	if (depid in govs and govs[depid]!=govid):
		print('Multiply governed token, potential cycle:', depid)
	else:
		govs[depid]=govid


