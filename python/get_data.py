import numpy as np
import pandas as pd
from scipy import interpolate

import json

from datetime import datetime, timedelta

import requests

import io

print("RUNNING!")
print(datetime.now())

def myconverter(o):
    if isinstance(o, datetime):
        return o.__str__()


url = "https://coronavirus.data.gov.uk/downloads/csv/coronavirus-cases_latest.csv"
s = requests.get(url).content
df = pd.read_csv(io.StringIO(s.decode('utf-8')))



df = df[df['Area type'] == 'ltla']
df['Specimen date'] = pd.to_datetime(df['Specimen date'])

names = df['Area name'].unique()

t = np.arange(df['Specimen date'].min(), df['Specimen date'].max() + timedelta(days=1), timedelta(days=1)).astype(datetime)

roll = 19 ## median duration of viral shedding was 19 days -- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7289725/

data = {}
for i,name in enumerate(names):
    place = df[df['Area name'] == name].set_index('Specimen date')
    
    for day in t:
        if day not in place.index:
            place.loc[day,'Daily lab-confirmed cases'] = 0
            place.loc[day,'Area name'] = name
        
    place = place[~place.index.duplicated(keep='first')]
    place = place.iloc[::-1]

    data[name] = place['Daily lab-confirmed cases'].rolling(roll, min_periods=0).sum().astype(int).values.tolist()

coords = pd.read_csv('area_pos_ltla_England.csv',index_col=0)
pop = pd.read_csv('population.csv',delimiter=";",index_col="local_authority")

final_data = []

for i,coord in coords.iterrows():
    y = data[i]
    y = y/np.max(y[0:120])
    x = np.arange(0,len(y),1)
    spl = interpolate.UnivariateSpline(x, y, s=0.5)
    g = np.round(1000*np.gradient(spl(x))).astype(int)
    dat = {
        "name": i,
        "lat" : coord['lat'],
        "lng" : coord['lng'],
        "data": data[i],
        "rate": g.tolist(),
        "population": int(pop.loc[i]['population']),
    }
    final_data.append(dat)

with open('datetime.json', 'w') as fp:
    json.dump(t.tolist(), fp, default = myconverter)

with open('data.json', 'w') as fp:
    json.dump(final_data, fp, default = myconverter)