file='/Users/austinc/Desktop/cps_00005.dat'

with open(file,'rU') as file:
	data=[row for row in file]

import pandas as pd

newdata=[]
for row in data:
	temp=[int(row[0:4]),int(row[9:19]),row[33:35],int(row[61:71]),int(row[71:85]),int(row[85:87]),int(row[87:89]),int(row[89:92]),int(row[92:94])]
	newdata.append(temp)

data=pd.DataFrame(newdata,columns=['year','hwtfinl','month','earnwt','wtfinl','age','empstat','uhrsworkt','whyabsnt'])
iu=data[data['empstat']!=0]

data2007=iu[iu['year']==2007]
data2009=iu[iu['year']==2009]
data2014=iu[iu['year']==2014]

total2007=data2007['wtfinl'].sum()
total2009=data2009['wtfinl'].sum()
total2014=data2014['wtfinl'].sum()

# create a list of employed by age
employedft2007=[]
employedpt2007=[]
unemployed2007=[]
disabled2007=[]
retired2007=[]
student2007=[]
other2007=[]
carer2007=[]

for i in range(15,76,1):
	temp=data2007[(data2007['age']==i)]
	total=temp['wtfinl'].sum()
	temp=data2007[(data2007['age']==i) & (data2007['uhrsworkt']>34)]
	employed=temp[temp['empstat']==10]['wtfinl'].sum()+temp[temp['empstat']==12]['wtfinl'].sum()
	employedft2007.append(float(employed)/float(total))
	temp=data2007[(data2007['age']==i) & (data2007['uhrsworkt']<35)]
	employed=temp[temp['empstat']==10]['wtfinl'].sum()+temp[temp['empstat']==12]['wtfinl'].sum()
	employedpt2007.append(float(employed)/float(total))
	temp=data2007[(data2007['age']==i)]
	employed=temp[temp['empstat']==21]['wtfinl'].sum()+temp[temp['empstat']==22]['wtfinl'].sum()
	unemployed2007.append(float(employed)/float(total))
	temp=data2007[(data2007['age']==i)]
	employed=temp[temp['empstat']==32]['wtfinl'].sum()
	disabled2007.append(float(employed)/float(total))
	temp=data2007[(data2007['age']==i)]
	employed=temp[temp['empstat']==36]['wtfinl'].sum()
	retired2007.append(float(employed)/float(total))
	temp=data2007[(data2007['age']==i)]
	employed=temp[temp['empstat']==33]['wtfinl'].sum()
	student2007.append(float(employed)/float(total))
	temp=data2007[(data2007['age']==i)]
	employed=temp[temp['empstat']==31]['wtfinl'].sum()
	carer2007.append(float(employed)/float(total))
	# other=1-(employedft2007[i-15]+employedpt2007[i-15]+unemployed2007[i-15]+disabled2007[i-15]+retired2007[i-15]+student2007[i-15]+carer2007[i-15])
	# other2007.append(other)

for i in range(15,76,1):
	print i,employedft2007[i-15],employedpt2007[i-15],unemployed2007[i-15],disabled2007[i-15],retired2007[i-15],student2007[i-15],carer2007[i-15]




