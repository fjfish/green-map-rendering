import urllib.request
import xml.etree.ElementTree as ET
import tempfile
import subprocess
import re
import csv
import sys, os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

datasource = """
<Style name="%(name)s" filter-mode="first">
  <Rule>
    <LineSymbolizer stroke-width="%(stroke-width)i" stroke="%(stroke-colour)s" stroke-linejoin="round" stroke-linecap="round" />
  
    
  </Rule>
</Style>
    <Layer name="%(name)s"  srs="+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs">
    <StyleName>%(name)s</StyleName>
    <Datasource>
       <Parameter name="type">ogr</Parameter>
       <Parameter name="file">%(file)s</Parameter>
       <Parameter name="layer">%(layer)s</Parameter>
    </Datasource>
  </Layer>"""
  
points = """
<Style name="points" filter-mode="first">
  <Rule>
    <TextSymbolizer dy="0"  clip="true" fill="#006341" fontset-name="fontset-0" halo-fill="rgba(255, 255, 255, 0.6)" halo-radius="1" size="16" margin="5"><![CDATA[[Name]]]></TextSymbolizer>
  </Rule>
</Style>
    <Layer name="points"  srs="+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs" clear-label-cache="on">
    <StyleName>points</StyleName>
    <Datasource>
       <Parameter name="type">ogr</Parameter>
       <Parameter name="file">%(filepath)s</Parameter>
       <Parameter name="layer">%(layer_name)s</Parameter>
    </Datasource>
  </Layer>"""
  
with open('base.xml') as mapnik_base_file:
    mapnik_base_string = mapnik_base_file.read()
mapnik_no_substitutions = mapnik_base_string
mapnik_no_substitutions = re.sub('{{highway_name_sub}}', "name", mapnik_no_substitutions)
mapnik_no_substitutions = re.sub('{{building_name_subs}}', "name", mapnik_no_substitutions)

highway_name_substitutions = "name"
with open('highway_name_substitutions.csv', 'r') as data: 
    for line in csv.DictReader(data):
        highway_name_substitutions = "replace(" + highway_name_substitutions + ", '" + line['original'] + "', '" + line['substitution'] + "')"   
mapnik_base_string = re.sub('{{highway_name_sub}}', highway_name_substitutions, mapnik_base_string)

building_name_substitutions = "name"
with open('building_name_substitutions.csv', 'r') as data: 
    for line in csv.DictReader(data):
        building_name_substitutions = "replace(" + building_name_substitutions + ", '" + line['original'] + "', '" + line['substitution'] + "')"   
mapnik_base_string = re.sub('{{building_name_subs}}', building_name_substitutions, mapnik_base_string)

def download_kml(id_):
    #url = 'https://www.google.com/maps/d/kml?mid=142MtnYjMIfVGz-tMLbW0E8aG7CP77gw&lid=r6w8Oh_qNq8&forcekml=1&cid=mp&cv=IWoFdyKWGHI.en_GB.'
    url = f'http://www.google.com/maps/d/kml?mid={id_}&forcekml=1'
    print(url)
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    return data
    
def output_map(id_, ward, path):
    data = download_kml(id_)
    root = ET.fromstring(data)
    folders = set([folder.find("{http://www.opengis.net/kml/2.2}name").text 
                   for folder 
                   in root.find("{http://www.opengis.net/kml/2.2}Document").findall('{http://www.opengis.net/kml/2.2}Folder')])
    for folder_name in folders:
        output_folder(root, folder_name, ward, os.path.join(path, folder_name), data)
    
def output_folder(root, folder_name, ward, path, data):
    placemark_names = set()
    for folder in root.find("{http://www.opengis.net/kml/2.2}Document").findall('{http://www.opengis.net/kml/2.2}Folder'):
        if folder.find("{http://www.opengis.net/kml/2.2}name").text == folder_name:
           ns = set([placemark.find("{http://www.opengis.net/kml/2.2}name").text for placemark in folder.findall('{http://www.opengis.net/kml/2.2}Placemark')])
           placemark_names = placemark_names.union(ns)
    root = ET.fromstring(data)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as kml_temp:
        ET.ElementTree(root).write(kml_temp)
        kml_file = kml_temp.name  
    root = ET.fromstring(data)
    doc = root.find("{http://www.opengis.net/kml/2.2}Document")
    for folder in doc.findall('{http://www.opengis.net/kml/2.2}Folder'):
        if  folder.find("{http://www.opengis.net/kml/2.2}name").text != folder_name:
            doc.remove(folder)
        else:
            for placemark in folder.findall('{http://www.opengis.net/kml/2.2}Placemark'):
                if  placemark.find("{http://www.opengis.net/kml/2.2}Polygon") is not None:
                    folder.remove(placemark)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as kml_temp:
        ET.ElementTree(root).write(kml_temp)
        point_kml_file = kml_temp.name    
    make_image(path, folder_name, "Overview", ward, kml_file, points_file = point_kml_file)
    for placemark_name in placemark_names:
        output_placemark(folder_name, placemark_name, ward, path, data)
        
def output_placemark(folder_name, placemark_name, ward, path, data):
    root = ET.fromstring(data)
    doc = root.find("{http://www.opengis.net/kml/2.2}Document")
    for folder in doc.findall('{http://www.opengis.net/kml/2.2}Folder'):
        if  folder.find("{http://www.opengis.net/kml/2.2}name").text != folder_name:
            doc.remove(folder)
        else:
            for placemark in folder.findall('{http://www.opengis.net/kml/2.2}Placemark'):
                if  placemark.find("{http://www.opengis.net/kml/2.2}name").text != placemark_name:
                    folder.remove(placemark)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as kml_temp:
        ET.ElementTree(root).write(kml_temp)
        kml_file = kml_temp.name
    make_image(path, folder_name, placemark_name, ward + " - " + placemark_name, kml_file)
     
def make_image(path, folder_name, name, text, kml_file, points_file = None):
    ds = datasource % {"name": "boundary", 
                       "stroke-width": 4, 
                       "stroke-colour": "#006341", 
                       "file": kml_file,
                       "layer": folder_name}
    if points_file:
        p = points % {"filepath": points_file, "layer_name": folder_name}
        mapnik_string = re.sub('{{extra_data_sources}}', ds + p, mapnik_no_substitutions) 
    else:
        mapnik_string = re.sub('{{extra_data_sources}}', ds, mapnik_no_substitutions) 

    with open("temp.xml", 'w') as mapnik_out:
        mapnik_out.write(mapnik_string)
        mapnik_file = "temp.xml"

    for d, ps in [("A4square", ["-d", "200", "200", "--norotate"]), 
                  ("A5", ["-a", "-5"])]:
        outputjpeg = os.path.join(path, d, f"{name}.jpeg")
        Path(outputjpeg).parent.mkdir(exist_ok=True, parents=True)
        subprocess.run(["nik4", "--fit", "boundary", "-p", "600"] + ps + [mapnik_file, outputjpeg])
        im = Image.open(outputjpeg)
        width, height = im.size
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("/usr/share/fonts/opentype/bebas-neue/BebasNeue-Regular.otf", 256, encoding="unic")
        text_width, text_height = font.getmask(text).size
        draw.text((text_height, height - 2 * text_height), text, '#006341', font)
                
        font = ImageFont.truetype("HelveticaNeueLTStd-Cn.otf", 72, encoding="unic")
        copytext = u"Map data from OpenStreetMap."
        copytext_width, copytext_height = font.getmask(copytext).size
        draw.text((width - text_height - copytext_width, height - text_height - copytext_height), copytext, '#006341', font)
                
        im.save(outputjpeg)

if len(sys.argv) < 2:
    print("Usage: python3 getMaps.py [map id] [Ward Name]")

if len(sys.argv) >= 3:
    id_ = sys.argv[1]
    ward = " ".join(sys.argv[2:])
    output_map(id_, ward, os.path.join(".", ward))



