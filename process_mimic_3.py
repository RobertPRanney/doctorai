# This script processes MIMIC-III dataset and builds longitudinal diagnosis records for patients with at least two visits.
# The output data are cPickled, and suitable for training Doctor AI or RETAIN
# Written by Edward Choi (mp2893@gatech.edu)
# Usage: Put this script to the foler where MIMIC-III CSV files are located. Then execute the below command.
# python process_mimic.py ADMISSIONS.csv DIAGNOSES_ICD.csv <output file>

# Output files
# <output file>.pids: List of unique Patient IDs. Used for intermediate processing
# <output file>.dates: List of List of Python datetime objects. The outer List is for each patient. The inner List is for each visit made by each patient
# <output file>.seqs: List of List of List of integer diagnosis codes. The outer List is for each patient. The middle List contains visits made by each patient. The inner List contains the integer diagnosis codes that occurred in each visit
# <output file>.types: Python dictionary that maps string diagnosis codes to integer diagnosis codes.

import sys
import pickle
from datetime import datetime



def convert_to_icd9(dxStr):
	if dxStr.startswith('E'):
		if len(dxStr) > 4: return dxStr[:4] + '.' + dxStr[4:]
		else: return dxStr
	else:
		if len(dxStr) > 3: return dxStr[:3] + '.' + dxStr[3:]
		else: return dxStr

def convert_to_3digit_icd9(dxStr):
	if dxStr.startswith('E'):
		if len(dxStr) > 4: return dxStr[:4]
		else: return dxStr
	else:
		if len(dxStr) > 3: return dxStr[:3]
		else: return dxStr

if __name__ == '__main__':
	admissionFile = sys.argv[1]
	diagnosisFile = sys.argv[2]
	outFile = sys.argv[3]

	print('Building pid-admission mapping, admission-date mapping')
	pidAdmMap = {}
	admDateMap = {}
	infd = open(admissionFile, 'r')
	infd.readline()
	for line in infd:
		tokens = line.strip().split(',')
		pid = int(tokens[1])
		admId = int(tokens[2])
		admTime = datetime.strptime(tokens[3], '%Y-%m-%d %H:%M:%S')
		admDateMap[admId] = admTime
		if pid in pidAdmMap: pidAdmMap[pid].append(admId)
		else: pidAdmMap[pid] = [admId]
	infd.close()

	print('Building admission-dxList mapping')
	admDxMap = {}
	infd = open(diagnosisFile, 'r')
	infd.readline()
	for line in infd:
		tokens = line.strip().split(',')
		admId = int(tokens[2])
		dxStr = 'D_' + convert_to_icd9(tokens[4][1:-1]) ############## Uncomment this line and comment the line below, if you want to use the entire ICD9 digits.
		#dxStr = 'D_' + convert_to_3digit_icd9(tokens[4][1:-1])
		if admId in admDxMap: admDxMap[admId].append(dxStr)
		else: admDxMap[admId] = [dxStr]
	infd.close()

	print('Building pid-sortedVisits mapping')
	pidSeqMap = {}
	for pid, admIdList in pidAdmMap.items():
		if len(admIdList) < 2: continue
		sortedList = sorted([(admDateMap[admId], admDxMap[admId]) for admId in admIdList])
		pidSeqMap[pid] = sortedList

	print('Building pids, dates, strSeqs')
	pids = []
	dates = []
	seqs = []
	for pid, visits in pidSeqMap.items():
		pids.append(pid)
		seq = []
		date = []
		for visit in visits:
			date.append(visit[0])
			seq.append(visit[1])
		dates.append(date)
		seqs.append(seq)

	print('Converting strSeqs to intSeqs, and making types')
	types = {}
	newSeqs = []
	for patient in seqs:
		newPatient = []
		for visit in patient:
			newVisit = []
			for code in visit:
				if code in types:
					newVisit.append(types[code])
				else:
					types[code] = len(types)
					newVisit.append(types[code])
			newPatient.append(newVisit)
		newSeqs.append(newPatient)


	num_pts = len(pids)


	train_size = 0.7
	test_size = 0.2
	valid_size = 0.1

	pids_train = pids[:int(num_pts * train_size)]
	pids_test = pids[int(num_pts * train_size): int(num_pts * (train_size + test_size))]
	pids_valid = pids[int(num_pts * (train_size + test_size)):]
	pickle.dump(pids_train, open(outFile+'_pids.train', 'wb'), -1)
	pickle.dump(pids_test, open(outFile+'_pids.test', 'wb'), -1)
	pickle.dump(pids_valid, open(outFile+'_pids.valid', 'wb'), -1)


	dates_train = dates[:int(num_pts * train_size)]
	dates_test = dates[int(num_pts * train_size): int(num_pts * (train_size + test_size))]
	dates_valid = dates[int(num_pts * (train_size + test_size)):]
	pickle.dump(dates_train, open(outFile+'_dates.train', 'wb'), -1)
	pickle.dump(dates_test, open(outFile+'_dates.test', 'wb'), -1)
	pickle.dump(dates_valid, open(outFile+'_dates.valid', 'wb'), -1)

	seqs_train = newSeqs[:int(num_pts * train_size)]
	seqs_test = newSeqs[int(num_pts * train_size): int(num_pts * (train_size + test_size))]
	seqs_valid = newSeqs[int(num_pts * (train_size + test_size)):]
	pickle.dump(seqs_train, open(outFile+'_seq.train', 'wb'), -1)
	pickle.dump(seqs_test, open(outFile+'_seq.test', 'wb'), -1)
	pickle.dump(seqs_valid, open(outFile+'_seq.valid', 'wb'), -1)


	pickle.dump(types, open(outFile+'.types', 'wb'), -1)
