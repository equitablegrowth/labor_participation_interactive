import urllib2
import csv
import re
import zipfile
import os.path

cpsloc='http://thedataweb.rm.census.gov/ftp/cps_ftp.html#cpsbasic'
mainloc='main.csv'
mainloc='/Users/austinclemens/Desktop/labor_participation_interactive/labor_participation_interactive/Interactive/main.csv'
saveloc='/Users/austinclemens/Desktop/'
months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
basepath=os.path.dirname(os.path.abspath(__file__))

filename=scrape_newcps()
data=parse_CPS(filename)


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

	cpsb8206

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
	master_time=pd.DataFrame([],columns=['year','month','age','total_n','b0','b1','b2','b3','b4','b5','b6','b7'])

	try:
		location=folder_location+file
		with open(location,'rb') as csvfile:
			reader=csv.reader(csvfile)
			data=[row for row in reader]
	except:
		with open(location,'rb') as csvfile:
			reader = csv.reader(x.replace('\0', '') for x in csvfile)
			data=[row for row in reader]

	if int(file[4:6])<50:
		year=2000+int(file[4:6])
	if int(file[4:6])>49:
		year=1900+int(file[4:6])

	month=int(file[6:])

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







