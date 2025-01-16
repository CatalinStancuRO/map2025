#testABC
#test2
#import cv2
from flask import Flask, Response, json, jsonify, render_template, stream_template, stream_with_context, redirect
from flask import request

#import imutils

import time
import io
#from PIL import Image
import base64
import numpy as np
import random
import pyodbc

import os
import datetime
import json
import inspect

from math import *

from pyproj import Transformer

from dataclasses import dataclass, field, asdict, is_dataclass
from typing import List, Optional, Union


from flask_login import LoginManager, login_required
from auth.views import auth, login_manager


app = Flask(__name__)

app.secret_key = 'catalin'  # Required for secure forms

# Register authentication blueprint
app.register_blueprint(auth, url_prefix='/auth')

# Initialize Flask-Login
login_manager.init_app(app)

app.config['DEBUG'] = True

app.config['SESSION_TYPE'] = 'filesystem'
#app.config['JSON_AS_ASCII'] = False

transformer = Transformer.from_crs("EPSG:3844", "EPSG:4326", always_xy=True)

class mapSerial(json.JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, np.ndarray): 
                return obj.tolist()   
            if isinstance(obj, np.integer):
                return int(obj)            
            if isinstance(obj, np.float32):
                return float(obj)
            if isinstance(obj, datetime.datetime): 
                return obj.isoformat()  
            
            if isinstance(obj, pyodbc.Row): 
                return tuple(obj)                      
            return json.JSONEncoder.default(self, obj)

        except:
            print()


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return self.default(obj.to_json())
        elif hasattr(obj, "__dict__"):
            d = dict(
                (key, value)
                for key, value in inspect.getmembers(obj)
                if not key.startswith("__")
                and not inspect.isabstract(value)
                and not inspect.isbuiltin(value)
                and not inspect.isfunction(value)
                and not inspect.isgenerator(value)
                and not inspect.isgeneratorfunction(value)
                and not inspect.ismethod(value)
                and not inspect.ismethoddescriptor(value)
                and not inspect.isroutine(value)
            )
            return self.default(d)
        return obj
    
@dataclass
class Geometry:
    type: str
    coordinates: List[Union[List[List[float]], List[List[float]]]]

@dataclass
class Properties:
    amenity: Optional[str] = None
    building: Optional[str] = None
    name: Optional[str] = None

@dataclass
class Feature:    
    type: str = "Feature"
    properties: Properties = field(default_factory=Properties)    
    geometry: Geometry = field(default_factory=Geometry)    

@app.route('/', methods=['POST', 'GET'])
@login_required
def testmap():
    return render_template('index.html')        


@app.route('/submit', methods=['POST'])
def submit():
    # Get the input values from the form
    input1 = request.form.get('input1')
    input2 = request.form.get('input2')
    input3 = request.form.get('input3')
    input4 = request.form.get('input4')

    # Save the inputs to a text file
    with open('inputs.txt', 'a') as file:
        file.write(f"{input1}, {input2}, {input3}, {input4}\n")

    return "Inputs saved successfully!"

@app.route('/map2025/getjson', methods=['POST', 'GET'])
def getjson():
    print("getjson - a inceput")
    conn=DB_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
			"SELECT\
				p.id\
				,p.[name]\
                ,p.Denumire_Strat \
				,pt.x\
				,pt.y\
				,pt.[Index]	\
					from [Giroc_TIMIS_VERIFICAT_06.11.2024.dibalgis].[dbo].[polygons] p\
					left join [Giroc_TIMIS_VERIFICAT_06.11.2024.dibalgis].[dbo].[points] pt on pt.id_Polygon=p.id\
                    where pt.x is not null and pt.y is not null\
                    order by p.id, pt.[Index]"
                )
        
        features_dict = {    "unique_key": Feature  }
        
        for index, row in enumerate(cursor, start=1):
            x_stereo70=row.x
            y_stereo70=row.y
            
            longitude, latitude = transformer.transform(x_stereo70, y_stereo70)
            
 
            if row.id not in features_dict:
               points=[]
               points.append ([longitude, latitude])
               feature = Feature(
                    geometry=Geometry(
                        type="MultiPolygon",
                        coordinates=[
                                        [
                                            points
                                            
                                        ]
                                    ]
                    ),
                    properties=Properties(amenity=None, building="yes", name=row.name)
                )
               features_dict[row.id]=feature
            else:
               feature=features_dict[row.id]
               points=feature.geometry.coordinates[0][0].append([longitude, latitude])

        features_lst=[]
        for key, value in features_dict.items():
            features_lst.append(value)

        final={"type": "FeatureCollection",
            "name": "crisul",
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
            "features":features_lst}
        
        features_json = json.dumps(final, cls=ObjectEncoder, indent=4)

        print("getjson - almost done")
        return features_json
        
        
    finally:

        conn.close()



def DB_conn():
    server = 'WIN-4OR15UPB94G,1433' # to specify an alternate port
    database = 'Log_DibalGis' 
    username = 'catalin' 
    password = '--w9VAZXQbpwvppA--' 
    #conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    return conn

def DB_GetDate():
    conn=DB_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT GetDate() as ts')
        res=list(cursor.fetchall())
        ts=res[0].ts
        return ts
    finally:
        conn.close


# main driver function
if __name__ == '__main__':    
    app.run( port=5000, host='0.0.0.0', use_reloader=False)
    