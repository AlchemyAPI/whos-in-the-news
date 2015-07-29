import requests
import os
from multiprocessing import Pool, Queue, Manager
from flask import Flask, url_for, render_template, json


app = Flask(__name__)

API_KEY=YOUR_API_KEY

def get_image(resource, entity, article, queue):
    try: 
        i_get_url = 'http://dbpedia.org/sparql?default-graph-uri=http%3A%2F%2Fdbpedia.org&query=select+%3Fthumbnail+where+{+<'+resource+'>+dbo%3Athumbnail+%3Fthumbnail}&format=json&timeout=1000' 
        i_results = requests.get(url=i_get_url) 
        i_response = i_results.json()
        if i_response['results']['bindings']:
            picture = i_response['results']['bindings'][0]['thumbnail']['value']   
            
            queue.put('<div class="Image_Wrapper" data-caption="'+entity['disambiguated']['name']+'"><a href="'+article['source']['enriched']['url']['url']+'" target="_blank"><img src="'+ picture+'" onerror="imgError(this);"/></a></div>')
    except Exception as e:
        print e    


@app.route('/images')
def images():
    imgTags=[]

    
    try:
        

        get_url="https://access.alchemyapi.com/calls/data/GetNews?outputMode=json&start=now-1h&end=now&count=25&q.enriched.url.enrichedTitle.entities.entity=|type=person,disambiguated.dbpedia=dbpedia|&return=enriched.url.enrichedTitle.entities.entity.disambiguated%2Cenriched.url.title%2Cenriched.url.url%2Cenriched.url.enrichedTitle.entities.entity.type&apikey="+API_KEY
        results = requests.get(url=get_url) 
        response = results.json()
        
    except Exception as e:
        print e
       
    
    entityList=[]
        
    l_pool = Pool(processes = 30)
    l_mgr  = Manager()
    l_resultQueue = l_mgr.Queue()
 
    for article in response['result']['docs']:
            for entity in article['source']['enriched']['url']['enrichedTitle']['entities']:
                if entity['type']=="Person" and entity['disambiguated']:
                    if entity['disambiguated']['dbpedia']:
                        resource=entity['disambiguated']['dbpedia']
                        if resource not in entityList:
                            entityList.append(resource)
                            l_pool.apply_async(get_image, (resource, entity, article, l_resultQueue))  
    
    l_pool.close()
    l_pool.join()    
    
    while not l_resultQueue.empty():
        imgTags.append(l_resultQueue.get())
    
    images =  ''.join(imgTags)
    return images


@app.route('/')
def main():
    return render_template('index.html')



port = os.getenv('VCAP_APP_PORT', '8000')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(port), debug=True)

