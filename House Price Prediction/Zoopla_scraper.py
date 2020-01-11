from bs4 import BeautifulSoup #import beatiful soup to parse the websites
import numpy as np
import pandas as pd 
import requests 
import matplotlib.pyplot as plt 
import time
import geopandas
from geopandas.tools import geocode
import fiona
%matplotlib inline
# important libraries


zoopla = 'https://www.zoopla.co.uk'
website = 'https://www.zoopla.co.uk/for-sale/property/london/?page_size=100&q=London&radius=0&results_sort=newest_listings&search_source=refine'
number_of_pages = range(1, 100) #all pages we want from 1 to the last page wanted
all_properties = [] #empty list to append lists with all the values


for page_counter in number_of_pages: #iterate through all available pages
    r = requests.get(website + str(page_counter)) #find website
    soup = BeautifulSoup(r.content, 'html5lib') #parse through bs4
    properties_from_current_page = soup.select('li[class*="srp clearfix"]') #get all properties from this page in a list
    
    for idx in range(len(properties_from_current_page)): 
        indv_listing = [] 
        current_listing = properties_from_current_page[idx] 
    
        href = current_listing.select('a[class*="listing-results-price text-price"]')[0]['href']
        indv_listing.append(zoopla + href)
    
        try:
            indv_listing.append(current_listing.select('span[class*="num-icon num-beds"]')[0].text)
        except:
            indv_listing.append(0)
        
        
        try:
            indv_listing.append(current_listing.select('span[class*="num-icon num-baths"]')[0].text)
        except:
            indv_listing.append(0)
        
        
        try:
            indv_listing.append(current_listing.select('span[class*="num-icon num-reception"]')[0].text)
        except:
            indv_listing.append(0)
        
        
        try:
            indv_listing.append(' '.join(current_listing.select('div[class*="listing-results-footer clearfix"]')[0].small.text.split()))
        except:
            indv_listing.append(np.nan)

        
        try:
            indv_listing.append(current_listing.select('div[class*="listing-results-footer clearfix"]')[0].span.text)
        except:
            indv_listing.append(np.nan)
        
        
        try:
            indv_listing.append(current_listing.select('a[class*="listing-results-price text-price"]')[0].text.replace('\n','').replace(' ', ''))
        except:
            indv_listing.append(np.nan)
     
    
    
        temp_r = requests.get(zoopla + href)
        temp_soup = BeautifulSoup(temp_r.content, 'html5lib')
        temp_list = []

        
        
        try:
            indv_listing.append(temp_soup.select('h2[class*="ui-property-summary__address"]')[0].text)
        except:
            indv_listing.append(np.nan)
        
        
        try:
            for floorplan_image in temp_soup.select('ul[class*="dp-floorplan-assets__no-js-links"]')[0].find_all('a'):
                temp_list.append(floorplan_image)
        except:
            temp_list.append(np.nan)                     

            
        indv_listing.append(temp_list)
    
        all_properties.append(indv_listing) 
        time.sleep(5)



labels = ['website', 'bedrooms', 'bathrooms', 'other_rooms', 'date_listed', 'listed_by', 'price', 'address', 'floorplan']

df = pd.DataFrame.from_records(all_properties, columns=labels)

df['price'] = df['price'].str.replace(r'\D', '')

def get_day(row):
    x = row.split()
    y = re.match('\d+', x[2])
    return y.group()


def get_month(row):
    x = row.split()
    return x[3]


def get_year(row):
    x = row.split()
    return x[4]


def get_website(row):
    if row == '[nan]':
        return 0
    else:
        x = row.split()[2][6:-1]
        return x


df['day_listed'] = df['date_listed'].apply(get_day)
df['month_listed'] = df['date_listed'].apply(get_month)
df['year_listed'] = df['date_listed'].apply(get_year)
df['floorplan_website'] = df['floorplan'].apply(get_website)

df = df.drop(['floorplan', 'date_listed'], axis=1)
gdf = geopandas.GeoDataFrame(df)

def my_geocoder(row):
    try:
        point = geocode(row, provider='nominatim').geometry.iloc[0]
        return pd.Series({'Latitude': point.y, 'Longitude': point.x, 'geometry': point})
    except:
        return None

gdf[['Latitude', 'Longitude', 'geometry']] = gdf.apply(lambda x: my_geocoder(x['address']), axis=1)

gdf.to_file('C:\\Users\\Jan\\Desktop\\Python\\Zoopla_edinburgh.shp')