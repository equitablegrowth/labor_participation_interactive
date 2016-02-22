from __future__ import division
import csv
import pandas as pd
import os
import sys
import codecs

# this code was used to create the original main.csv but that file should be updated via scraper.py going forward

# PEMLR
	# 1	EMPLOYED-AT WORK
	# 2	EMPLOYED-ABSENT
	# 3	UNEMPLOYED-ON LAYOFF
	# 4	UNEMPLOYED-LOOKING
	# 5	NOT IN LABOR FORCE-RETIRED
	# 6	NOT IN LABOR FORCE-DISABLED
	# 7	NOT IN LABOR FORCE-OTHER

# A-MAJACT     CHARACTER*001 .    (0281:0281)
	# ITEM 19 - WHAT WAS ... DOING MOST OF LAST WEEK    ALL
	# 1 = WORKING
	# 2 = WITH JOB BUT NOT AT WORK
	# 3 = LOOKING FOR WORK
	# 4 = KEEPING HOUSE
	# 5 = GOING TO SCHOOL
	# 6 = UNABLE TO WORK
	# 7 = RETIRED
	# 8 = OTHER

# ESR, 1976-1986 (employment status recode) - word 19, char 1, basically like majact but no retired category (8 is other including retired)
	# 1 = Working
	# 2 = with job, not at work
	# 3 = Unemployed, looking
	# 4 = Keeping House
	# 5 = School
	# 6 = Unable
	# 7 = Other (includes retired)

# Bruenig
	# 0 Full-time: PEMLR == 1 or PEMLR == 2 and PEHRUSLT > 34 or PEHRFTPT == 1
	# 1 Part-time: PEMLR == 1 or PEMLR == 2 and PEHRUSLT < 35 and PEHRFTPT != 1
	# 2 Unemployed: PEMLR == 3 or PEMLR == 4
	# 3 Retired: PEMLR == 5 or (PEMLR == 7 and PENLFACT == 5)
	# 4 Disabled: PEMLR == 6 or (PEMLR == 7 and PENLFACT == 1) or (PEMLR == 7 and PENLFACT == 2)
	# 5 Carer: (PEMLR == 7 and PENLFACT == 4)
	# 6 Student: (PEMLR == 7 and PENLFACT == 3)
	# 7 Other: (PEMLR == 7 and PENLFACT = 6) or (PEMLR == 7 and PENLFACT == -1)

folder_location='/Users/austinclemens/Desktop/labor_participation_interactive/CPS datasets/'

def parse_CPS(folder_location=folder_location):
	files=os.listdir(folder_location)
	files=[file for file in files if file[0:3]=='cps']
	# files=[file for file in files if int(file[4:6])==78]

	master_time=pd.DataFrame([],columns=['year','month','age','total_n','b0','b1','b2','b3','b4','b5','b6','b7'])

	for file in files:
		print file
		location=folder_location+file
		try:
			with open(location,'rb') as csvfile:
				reader=csv.reader(csvfile)
				data=[row for row in reader]

		except:
			print 'probably a null byte'
			with open(location,'rb') as csvfile:
				reader = csv.reader(x.replace('\0', '') for x in csvfile)
				data=[row for row in reader]

		if int(file[4:6])<50:
			year=2000+int(file[4:6])
		if int(file[4:6])>49:
			year=1900+int(file[4:6])

		month=int(file[6:])

		if year>1993:
			# PEMLR at 180:181, PEHRSULT at 224:226, PEHRFTPT at 222-223, PENLFACT at 569-570, PWSSWGT at 613-622, PRTAGE at 122-123, stop at 75
			# When PEMLR is not in universe it is always 1, universe is PRPERTYP = 2, PRPERTYP is 161-162
			pdata=[]
			for row in data:
				pdata.append([row[0][179:181],row[0][223:226],row[0][221:223],row[0][568:570],row[0][612:622],row[0][160:162],row[0][121:123]])

			adata=[]
			for row in pdata:
				try:
					adata.append([int(row[0]),int(row[1]),int(row[2]),int(row[3]),float(row[4]),int(row[5]),int(row[6])])
				except:
					pass

			pdata=pd.DataFrame(adata,columns=['pemlr','pehrsult','pehrftpt','penlfact','weight','prpertyp','age'])
			pdata['weight']=pdata['weight']/10000
			pdata=pdata[pdata['prpertyp']==2]

			# initial pandas object is set up. Create Bruenig and recode 
			pdata['bruenig']=0
			# 1 Part-time: PEMLR == 1 or 2 and PEHRSULT<35 and PEHRFTPT!=1
			pdata['bruenig'][((pdata['pemlr']==1) | (pdata['pemlr']==2)) & (pdata['pehrsult']<35) & (pdata['pehrftpt']!=1)]=1
			# 2 Unemployed: PEMLR == 3 or PEMLR == 4
			pdata['bruenig'][(pdata['pemlr']==3) | (pdata['pemlr']==4)]=2
			# 3 Retired: PEMLR == 5 or (PEMLR == 7 and PENLFACT == 5)
			pdata['bruenig'][(pdata['pemlr']==5) | ((pdata['pemlr']==7) & (pdata['penlfact']==5))]=3
			# 4 Disabled: PEMLR == 6 or (PEMLR == 7 and PENLFACT == 1) or (PEMLR == 7 and PENLFACT == 2)
			pdata['bruenig'][(pdata['pemlr']==6) | ((pdata['pemlr']==7) & (pdata['penlfact']==1)) | ((pdata['pemlr']==7) & (pdata['penlfact']==2))]=4
			# 5 Carer: (PEMLR == 7 and PENLFACT == 4)
			pdata['bruenig'][(pdata['pemlr']==7) & (pdata['penlfact']==4)]=5
			# 6 Student: (PEMLR == 7 and PENLFACT == 3)
			pdata['bruenig'][(pdata['pemlr']==7) & (pdata['penlfact']==3)]=6
			# 7 Other: (PEMLR == 7 and PENLFACT = 6) or (PEMLR == 7 and PENLFACT == -1)
			pdata['bruenig'][((pdata['pemlr']==7) & (pdata['penlfact']==6)) | ((pdata['pemlr']==7) & (pdata['penlfact']==-1))]=7


		elif year>1988:
			# -LFSR at 347:348, -EMPHRS at 356:358, -FTABS at 293:294, -NLFREA at 349:351, -FNLWGT at 397:405, -AGEDG at 168:170, -HRS1 at 282:284,
			# -USLFT at 285:286, -MAJACT at 280:281, -MIS at 69:70
			pdata=[]
			for row in data:
				pdata.append([row[0][347:348],row[0][356:358],row[0][293:294],row[0][349:351],row[0][397:405],row[0][168:170],row[0][282:284],row[0][285:286],row[0][280:281],row[0][69:70]])

			adata=[]
			for i,row in enumerate(pdata):
				for j,column in enumerate(row):
					if column.strip()=='':
						pdata[i][j]=0

				try:
					adata.append([int(row[0]),int(row[1]),int(row[2]),int(row[3]),float(row[4]),int(row[5]),int(row[6]),int(row[7]),int(row[8]),int(row[9])])
				except:
					pass

			pdata=pd.DataFrame(adata,columns=['lfsr','emphrs','ftabs','nlfrea','weight','age','hrs1','uslft','majact','mis'])
			pdata['weight']=pdata['weight']/100

			# initial pandas object is set up. Create Bruenig and recode
			# this is the recode using nlfrea. This method is pretty jumpy. There are large breaks especially in the employment
			# data between this series and the >1993 series. Carer is relatively stable as are some of the other misc categories,
			# but the jump in the employment series is pretty ugly.
			# pdata=pdata[(pdata['mis']==4) | (pdata['mis']==8)]
			# pdata['bruenig']=0
			# pdata['bruenig'][((pdata['lfsr']==1) | (pdata['lfsr']==2)) & (pdata['hrs1']<35) & (pdata['hrs1']>0) & (pdata['uslft']!=1)]=1
			# pdata['bruenig'][(pdata['lfsr']==3) | (pdata['lfsr']==4)]=2
			# pdata['bruenig'][(pdata['lfsr']>4) & (pdata['nlfrea']==4)]=3
			# pdata['bruenig'][(pdata['lfsr']>4) & (pdata['nlfrea']==2)]=4
			# pdata['bruenig'][(pdata['lfsr']>4) & (pdata['nlfrea']==3)]=5
			# pdata['bruenig'][(pdata['lfsr']>4) & (pdata['nlfrea']==1)]=6
			# pdata['bruenig'][(pdata['lfsr']>4) & ((pdata['nlfrea']==11) | (pdata['nlfrea']==-1))]=7

			# this is the recode using majact
			# these series are *much* smoother for the first 3 categories at the 93/94 break with the exception of some misc
			# categories that go crazy - disabled shoots up and this appears to be coming out of the 'other' category entirely.
			pdata['bruenig']=0
			pdata['bruenig'][((pdata['lfsr']==1) | (pdata['lfsr']==2)) & (pdata['hrs1']<35) & (pdata['hrs1']>0) & (pdata['uslft']!=1)]=1
			pdata['bruenig'][(pdata['lfsr']==3) | (pdata['lfsr']==4)]=2
			pdata['bruenig'][(pdata['lfsr']>4) & (pdata['majact']==7)]=3
			pdata['bruenig'][(pdata['lfsr']>4) & (pdata['majact']==6)]=4
			pdata['bruenig'][(pdata['lfsr']>4) & (pdata['majact']==4)]=5
			pdata['bruenig'][(pdata['lfsr']>4) & (pdata['majact']==5)]=6
			pdata['bruenig'][(pdata['lfsr']>4) & (pdata['majact']==8)]=7

			# experimenting with some other options for disabled
			# pdata['bruenig']=0
			# pdata['bruenig'][((pdata['lfsr']==1) | (pdata['lfsr']==2)) & (pdata['hrs1']<35) & (pdata['hrs1']>0) & (pdata['uslft']!=1)]=1
			# pdata['bruenig'][(pdata['lfsr']==3) | (pdata['lfsr']==4)]=2
			# pdata['bruenig'][((pdata['lfsr']==5) | (pdata['lfsr']==7)) & (pdata['majact']==7)]=3
			# pdata['bruenig'][(pdata['lfsr']==6) | (((pdata['mis']==4) | (pdata['mis']==8)) & (pdata['nlfrea']==2))]=4
			# pdata['bruenig'][((pdata['lfsr']==5) | (pdata['lfsr']==7)) & (pdata['majact']==4)]=5
			# pdata['bruenig'][((pdata['lfsr']==5) | (pdata['lfsr']==7)) & (pdata['majact']==5)]=6
			# pdata['bruenig'][((pdata['lfsr']==5) | (pdata['lfsr']==7)) & (pdata['majact']==8)]=7

		elif year<1989:
			pdata=[]
			for row in data:
				pdata.append([row[0][48],row[0][49:51],row[0][51],row[0][62],row[0][96:98],row[0][108],row[0][120:132]])

			adata=[]
			for i,row in enumerate(pdata):
				for j,column in enumerate(row):
					if column.strip()=='' or column.strip()=='-' or column.strip()=='--':
						pdata[i][j]=0

			for row in pdata:
				try:
					adata.append([int(row[0]),int(row[1]),int(row[2]),int(row[3]),int(row[4]),int(row[5]),float(row[6])])
				except:
					print 'except: ',row

			pdata=pd.DataFrame(adata,columns=['majactish','emphrs','ftpt1','ftpt2','age','esr','weight'])
			pdata=pdata[pdata['esr']!=0]
			pdata['weight']=pdata['weight']/100

			pdata['bruenig']=0
			pdata['bruenig'][((pdata['esr']==1) | (pdata['esr']==2)) & (pdata['emphrs']<35) & ((pdata['ftpt1']!=1) & (pdata['ftpt2']!=1))]=1
			pdata['bruenig'][(pdata['esr']==3)]=2
			# no retired for these years - it was not differentiated from other
			pdata['bruenig'][(pdata['esr']==6) | ((pdata['esr']==7) & (pdata['majactish']==6))]=4
			pdata['bruenig'][(pdata['esr']==4) | ((pdata['esr']==7) & (pdata['majactish']==4))]=5
			pdata['bruenig'][(pdata['esr']==5) | ((pdata['esr']==7) & (pdata['majactish']==5))]=6
			pdata['bruenig'][((pdata['esr']==7) & (pdata['majactish']==7))]=7

		# now for each age create a summary bracket
		for age in range(15,76,1):
			temp=pdata[pdata['age']==age]
			totaln=temp['weight'].sum()
			b0=temp[temp['bruenig']==0]['weight'].sum()/totaln
			b1=temp[temp['bruenig']==1]['weight'].sum()/totaln
			b2=temp[temp['bruenig']==2]['weight'].sum()/totaln
			b3=temp[temp['bruenig']==3]['weight'].sum()/totaln
			b4=temp[temp['bruenig']==4]['weight'].sum()/totaln
			b5=temp[temp['bruenig']==5]['weight'].sum()/totaln
			b6=temp[temp['bruenig']==6]['weight'].sum()/totaln
			b7=temp[temp['bruenig']==7]['weight'].sum()/totaln

			mtemp=pd.DataFrame([[year,month,age,totaln,b0,b1,b2,b3,b4,b5,b6,b7]],columns=['year','month','age','total_n','b0','b1','b2','b3','b4','b5','b6','b7'])
			master_time=master_time.append(mtemp)

	return master_time


def output_for_interactive(parsed):
	# this should collapse all months into one year observation. The months to be combined needs to be calculated
	# using the latest month. So if the last month was March 2015, then collapse to April 2014 - March 2015, April
	# 2013 - March 2014, etc...

	# In the end we should have 61 observations for each year - ages 15 through 75 * number of years

	minyear=parsed['year'].min()
	minmonth=parsed[parsed['year']==minyear]['month'].min()
	maxyear=parsed['year'].max()
	maxmonth=parsed[parsed['year']==maxyear]['month'].max()
	startmonth=(maxmonth+12) % 12 + 1

	currentyear=maxyear
	final=[]
	while currentyear>=minyear:
		print currentyear
		if minmonth==1:
			sample=parsed[parsed['year']==currentyear]
		else:
			sample=parsed[((parsed['year']==currentyear) & (parsed['month']<=maxmonth)) | ((parsed['year']==currentyear-1) & (parsed['month']>=startmonth))]

		for age in range(15,76,1):
			age_sample=sample[sample['age']==age]
			age_sample['weighted0']=age_sample['b0']*age_sample['total_n']
			age_sample['weighted1']=age_sample['b1']*age_sample['total_n']
			age_sample['weighted2']=age_sample['b2']*age_sample['total_n']
			age_sample['weighted3']=age_sample['b3']*age_sample['total_n']
			age_sample['weighted4']=age_sample['b4']*age_sample['total_n']
			age_sample['weighted5']=age_sample['b5']*age_sample['total_n']
			age_sample['weighted6']=age_sample['b6']*age_sample['total_n']
			age_sample['weighted7']=age_sample['b7']*age_sample['total_n']

			total=age_sample['total_n'].sum()

			b0=age_sample['weighted0'].sum()/total
			b1=age_sample['weighted1'].sum()/total
			b2=age_sample['weighted2'].sum()/total
			b3=age_sample['weighted3'].sum()/total
			b4=age_sample['weighted4'].sum()/total
			b5=age_sample['weighted5'].sum()/total
			b6=age_sample['weighted6'].sum()/total
			b7=age_sample['weighted7'].sum()/total

			final.append([age,currentyear,startmonth,maxmonth,str(int(startmonth))+'/'+str(int(currentyear-1))+'-'+str(int(maxmonth))+'/'+str(int(currentyear)),b0,b1,b2,b3,b4,b5,b6,b7])

		currentyear=currentyear-1

	final=pd.DataFrame(final,columns=['age','year','startmonth','endmonth','string','b0','b1','b2','b3','b4','b5','b6','b7'])
	return final


# with open('/Users/austinclemens/Desktop/out4.csv','rU') as csvfile:
# 	reader=csv.reader(csvfile)
# 	data=[row for row in reader]
# data=data[1:]
# data=[[float(row[0]),float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]),float(row[7]),float(row[8]),float(row[9]),float(row[10]),float(row[11]),float(row[12])] for row in data]

# data=pd.DataFrame(data,columns=['','year','month','age','total_n','b0','b1','b2','b3','b4','b5','b6','b7'])

# df.to_csv('out.csv')

































