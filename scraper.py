import urllib2
import csv
import re
import zipfile
import os.path
import json
import pandas as pd

basepath=os.path.dirname(os.path.abspath(__file__))
cpsloc='http://thedataweb.rm.census.gov/ftp/cps_ftp.html#cpsbasic'
mainloc=basepath+'main.csv'
main2loc=basepath+'main2.csv'
mainpartsloc=basepath+'main_parts.csv'
gdp_loc=basepath+'gdp.csv'
rec_loc=basepath+'recessions.csv'
months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']

filename=scrape_newcps()
data=parse_CPS(filename)
alldata=master_append(data)

formatted=output_for_interactive(alldata)
formatted.to_csv(mainloc,index=False)

formatted2=output_for_interactive2(alldata)
formatted2.to_csv(main2loc,index=False)

scrape_gdp(gdp_loc)
scrape_recessions(rec_loc)


def master_append(data):
	# take data from parse_CPS and append it to the master dataset in main_parts.csv. Load main_parts, write it to disk, and return it.
	df = pd.read_csv(mainpartsloc)
	alldata=data.append(df)
	alldata.to_csv(mainpartsloc,index=False)
	return alldata


def scrape_newcps():
	with open(mainloc,'rU') as csvfile:
		reader=csv.reader(csvfile)
		data=[row for row in reader]

	year=int(data[1][1])
	lastmonth=int(data[1][3])

	if lastmonth==12:
		year=year+1
		month=1

	if lastmonth!=12:
		month=lastmonth+1

	string=months[month-1]+str(year-2000)+'pub.zip'
	newstring='cpsb'+str(year-2000)+'%02d' % (month)

	source=urllib2.urlopen(cpsloc)
	page=source.read()

	newdownfinder=re.compile('(http://thedataweb.rm.census.gov/pub/cps/basic/......./%s)' % string)
	address=newdownfinder.findall(page)[0]

	zipped=urllib2.urlopen(address)
	open(basepath+'/temp.zip',"wb").write(zipped.read())

	with zipfile.ZipFile(basepath+'/temp.zip') as zf:
		for member in zf.infolist():
			words=member.filename.split('/')
			unzipped=words[0]
			path=basepath
			for word in words[:-1]:
				drive,word=os.path.splitdrive(word)
				head,word=os.path.split(word)
				if word in (os.curdir,os.pardir,''): continue
				path=os.path.join(path,word)
			zf.extract(member,path)

	os.remove(basepath+'/temp.zip')
	os.rename(basepath+'/'+unzipped,basepath+'/'+newstring)
	return basepath+'/'+newstring
	# file is now all ready for analysis.


def parse_CPS(file):
	# unlike the algo in making_pemlr, this is just going to parse one month - the most recent, and add it to the
	# main_parts.csv. Then that csv can be passed to format_for_interactive to create the final dataset.
	master_time=pd.DataFrame([],columns=['year','month','age','total_n','b0','b1','b2','b3','b4','b5','b6','b7'])

	try:
		with open(file,'rb') as csvfile:
			reader=csv.reader(csvfile)
			data=[row for row in reader]
	except:
		with open(file,'rb') as csvfile:
			reader = csv.reader(x.replace('\0', '') for x in csvfile)
			data=[row for row in reader]

	name=file.split('/')[-1]
	year=2000+int(name[4:6])
	month=int(name[6:])

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

	pdata['bruenig']=0
	pdata['bruenig'][((pdata['pemlr']==1) | (pdata['pemlr']==2)) & (pdata['pehrsult']<35) & (pdata['pehrftpt']!=1)]=1
	pdata['bruenig'][(pdata['pemlr']==3) | (pdata['pemlr']==4)]=2
	pdata['bruenig'][(pdata['pemlr']==5) | ((pdata['pemlr']==7) & (pdata['penlfact']==5))]=3
	pdata['bruenig'][(pdata['pemlr']==6) | ((pdata['pemlr']==7) & (pdata['penlfact']==1)) | ((pdata['pemlr']==7) & (pdata['penlfact']==2))]=4
	pdata['bruenig'][(pdata['pemlr']==7) & (pdata['penlfact']==4)]=5
	pdata['bruenig'][(pdata['pemlr']==7) & (pdata['penlfact']==3)]=6
	pdata['bruenig'][((pdata['pemlr']==7) & (pdata['penlfact']==6)) | ((pdata['pemlr']==7) & (pdata['penlfact']==-1))]=7

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


def output_for_interactive2(parsed):
	# nick [2:58 PM] yeah, <25, 25 to 34, 35 to 44, 45 to 54, (a prime-age one of 25 to 54 would be nice) and 54 plus would be great
	# this should collapse all months into one year observation but also collapse all ages into 6 age categories:
	#	<25
	#	25-34
	#	35-44
	#	45-54
	#	>54
	#	25-54

	minyear=parsed['year'].min()
	minmonth=parsed[parsed['year']==minyear]['month'].min()
	maxyear=parsed['year'].max()
	maxmonth=parsed[parsed['year']==maxyear]['month'].max()
	startmonth=(maxmonth+12) % 12 + 1

	currentyear=maxyear
	final=[]
	groups=[[0,25],[25,34],[35,44],[45,54],[54,100],[25,54]]
	group_names=['<25','25-35','35-44','45-54','>54','25-54']
	while currentyear>=minyear:
		print currentyear
		if minmonth==1:
			sample=parsed[parsed['year']==currentyear]
		else:
			sample=parsed[((parsed['year']==currentyear) & (parsed['month']<=maxmonth)) | ((parsed['year']==currentyear-1) & (parsed['month']>=startmonth))]

		for i,age_group in enumerate(groups):
			age_sample=sample[(sample['age']>=age_group[0]) & (sample['age']<=age_group[1])]
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

			final.append([group_names[i],currentyear,startmonth,maxmonth,str(int(startmonth))+'/'+str(int(currentyear-1))+'-'+str(int(maxmonth))+'/'+str(int(currentyear)),b0,b1,b2,b3,b4,b5,b6,b7])

		currentyear=currentyear-1

	final=pd.DataFrame(final,columns=['age','year','startmonth','endmonth','string','b0','b1','b2','b3','b4','b5','b6','b7'])
	return final


def scrape_gdp(gdp_loc):
	# get the gdp data from FRED and save out as a csv.
	address='https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&api_key=f9f6a417fc09f41db58b669007db3ba4&file_type=json&observation_start=1976-01-01&units=pch&frequency=q'
	source=urllib2.urlopen(address)
	data=json.load(source)
	data=data['observations']

	output=[['observation_date','GDPC1_PCH']]
	for obs in data:
		output.append([obs['date'],float(obs['value'])])

	with open(gdp_loc,'wb') as csvfile:
		writer=csv.writer(csvfile)
		for row in output:
			writer.writerow(row)


def scrape_recessions(rec_loc):
	# get the recession data from FRED and save out as a csv.
	address='https://api.stlouisfed.org/fred/series/observations?series_id=USREC&api_key=f9f6a417fc09f41db58b669007db3ba4&file_type=json&observation_start=1976-01-01'
	source=urllib2.urlopen(address)
	data=json.load(source)
	data=data['observations']

	output=[['observation_date','USREC']]
	for obs in data:
		output.append([obs['date'],int(obs['value'])])

	with open(rec_loc,'wb') as csvfile:
		writer=csv.writer(csvfile)
		for row in output:
			writer.writerow(row)






