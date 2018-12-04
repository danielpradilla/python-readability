#general
from pprint import pprint
from itertools import repeat
import time

#natural language
from readability_score.calculators.fleschkincaid import *
from readability_score.calculators.flesch import *
from readability_score.calculators.dalechall import *
from readability_score.calculators.colemanliau import *
from readability_score.calculators.linsearwrite import *
from readability_score.calculators.smog import *
from readability_score.calculators.ari import *
import nltk
import string

#reading/writing files
import os
import xml.etree.ElementTree as ET
import csv

#aws
import boto3
import json
import decimal

#multiprocessing
import multiprocessing as mp


####CONFIGURE HERE
ORGAN_SYMBOL_PATH = './organ_symbol.csv'
SIMPLE_WORDS_PATH = './DaleChallEasyWordList.txt'
FILES_PATH = './files/UNv1.0-TEI/en'
#####


def get_text_from_file(path):
    rtn = open(path).read()
    return rtn

def get_xml_tree(path):
    rtn = ET.ElementTree()
    try:
        rtn = ET.parse(path)
    except:
        print ("error parsing - %s" % (path) )

    return rtn

def parse_xml(path):
    print ("parsing - %s" % (path) )
    rtn = dict()

    tree = get_xml_tree(path)
    root = tree.getroot()
    
    rtn['path'] = path
    body = ''

    #find symbol and jobno
    if root is not None:
        for idno in root.findall(".//idno"):
            if idno.text is not None:
                rtn[idno.get('type')] = idno.text

        rtn['root'] = ''
        if rtn['symbol'] is not None:
            rtn['root'] = rtn['symbol'].split("/")[0]
            rtn['organ'] = get_organ(ORGAN_SYMBOL, rtn['symbol'], 2)

        rtn['keywords'] = list()
        for keyword in root.findall(".//keywords"):
            if keyword.text is not None:
                rtn['keywords'].append(keyword.text)
        
        for date in tree.findall(".//publicationStmt/date"):
            if date.text is not None:
                rtn['date'] = date.text
        
        for paragraph in tree.findall(".//body/p"):
            for sentence in paragraph.findall("s"):
                if sentence.text is not None:
                    body += sentence.text
                    if sentence.text[-1:] not in string.punctuation:
                        body += '. '
                    elif sentence == paragraph.findall("s")[-1]:
                        #if it's the last sentence in a paragraph
                        if sentence.text[-1:] in string.punctuation:
                            #replace last element for a period
                            body = body[:-1]
                        body += '. '
                    else:
                        body += ' '

    rtn['body'] = body
        
    return rtn


def get_file_list(root_dir, extension, batch_size):
    rtn = []
    i=0
    #rtn = [os.path.join(root, filename) for root, dirs, files in os.walk(root_dir, topdown=False) for filename in files ]
    for root, dirs, files in os.walk(root_dir,topdown=False):
        for filename in files:
            if not filename.startswith(".") and filename.endswith(extension): 
                path = os.path.join(root,filename)
                rtn.append(path)
                i+=1
                if i % batch_size == 0:
                    print ("%s - %s" % (i, path) )
    return rtn

def get_grades(text, locale):
    rtn=dict()
    results = FleschKincaid(text, locale=locale)
    rtn['FleschKincaid'] = {"score": results.us_grade, "min_age": results.min_age}

    results = Flesch(text, locale=locale)
    rtn['FleschReading'] = {"score": results.reading_ease, "min_age": 0}
    
    #TODO: check usage of simplewordlist
    results = DaleChall(text, simplewordlist=SIMPLE_WORDS_LIST, locale=locale)
    rtn['DaleChall'] = {"score": results.us_grade, "min_age": results.min_age}
    
    results = ColemanLiau(text, locale=locale)
    rtn['ColemanLiau'] = {"score": results.us_grade, "min_age": results.min_age}
    
    results = LinsearWrite(text, locale=locale)
    rtn['LinsearWrite'] = {"score": results.us_grade, "min_age": results.min_age}
    
    results = SMOG(text, locale=locale)
    rtn['SMOG'] = {"score": results.us_grade, "min_age": results.min_age}
    
    results = ARI(text, locale=locale)
    rtn['ARI'] = {"score": results.us_grade, "min_age": results.min_age}

    #convert to decimal
    for key, scores in rtn.items():
        for score, value in scores.items():
            rtn[key][score] = decimal.Decimal(str(value))
    
    return rtn
    
def process_file(file_path, locale):
    rtn = parse_xml(file_path)
    rtn["grades"] = get_grades(rtn["body"], locale)
    return rtn

def get_meta_of_file_index(file_list, locale, index):
    file_path = file_list[index]
    rtn = process_file(file_path, locale)
    return rtn

def process_files(file_list, locale, batch_size):
    rtn = []
    i=0
    for file_path in file_list:
        doc_meta = process_file(file_path, locale)
        rtn.append(doc_meta)
        i+=1
        if i % batch_size == 0:
            print("adding item %s - %s" % (i, item['symbol']) )
            
    return rtn

def process_files_mp(file_list, locale, processes, batch_size):
    rtn = []
    pool = mp.Pool(processes=processes)
    #rtn = pool.starmap(process_file, file_list) #previous map without locale
    rtn = pool.starmap(process_file, zip(file_list, repeat(locale)), chunksize=100) #map with more than one parameter

    return rtn
        
def process_files_write_to_db(file_list, locale, table):
    for file_path in file_list:
        doc_meta = process_file(file_path, locale)
        write_to_db(table, doc_meta)

    return True

        
def write_to_db(table, item):
    print("adding item:", item['symbol'])
    table.put_item(Item = item)



def load_organ_symbol_file(path):
    rtn = {}
    with open(path, 'r') as csvfile:
        for row in csv.DictReader(csvfile, delimiter=';'):
            rtn[row['symbol_series']] = row['body_organ']
    return rtn
    
def load_simple_words_file(path):
    rtn = []
    with open(path, 'r') as txtfile:
        for line in txtfile: 
            line = line.strip()
            rtn.append(line)     
    return rtn

def get_organ(organ_symbol, symbol, start_by=2):
    #attempt to find first by the start_by slash, moving down to first slash
    #return other if not found
    rtn = None
    for i in range(start_by, 0, -1):
        parts = symbol.split('/')
        if len(parts) >= start_by:
            lookup_by = '/'.join(parts[:i])            
            rtn = organ_symbol.get(lookup_by, None)
            if rtn is not None:
                break
    if rtn is None:
        rtn = 'Other'
    return rtn


def write_to_csv(docs_meta, path):
    with open(path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        
        #header row
        row = ["path","symbol","root","organ","date"]
        for key, scores in docs_meta[1]['grades'].items():
            for score, value in scores.items():
                row.append("%s_%s" % (key, score))
        csvwriter.writerow(row)
        
        #rest of the rows
        for doc_meta in docs_meta:
            if 'path' in doc_meta and 'symbol' in doc_meta:
                row = [doc_meta['path'], doc_meta['symbol'], doc_meta['root'], doc_meta['organ'], doc_meta['date'] ]
                for key, scores in doc_meta['grades'].items():
                    for score, value in scores.items():
                        row.append(value)
                csvwriter.writerow(row)

def main():
    #file_path = './test2.txt'
    #text = get_text_from_file(file_path)
    #print(text)

    start_time = time.time()

    global ORGAN_SYMBOL
    ORGAN_SYMBOL = load_organ_symbol_file(ORGAN_SYMBOL_PATH)
    global SIMPLE_WORDS_LIST
    SIMPLE_WORDS_LIST = load_simple_words_file(SIMPLE_WORDS_PATH)

    batch_size = 5000
    locale = 'en_US'
    
    file_list = get_file_list(FILES_PATH, '.xml', batch_size)




    #process with dynamodb
    #dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    #table = dynamodb.Table('readabilityScores')
    #write_to_db(table, doc_meta)
    #process_files_write_to_db(file_list, locale, table)
    
    #score one file    
    #doc_meta = get_meta_of_file_index(file_list, locale, 5)
    #pprint (vars(FleschKincaid(doc_meta['body'])) )
    
    #process batch of files
    cores = mp.cpu_count()
    docs_meta = process_files_mp(file_list, locale, (cores-2), 100)
    write_to_csv(docs_meta, './readability_results.csv')
    print(docs_meta[1000])

    print("--- %s seconds ---" % (time.time() - start_time))
    
    
#on first run we have to download the nltk dictionary
#nltk.download('punkt')
main()


