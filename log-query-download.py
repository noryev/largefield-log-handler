import os
import re
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
collection_name = os.getenv('COLLECTION_NAME')
downloads_dir = './analysisCIDs'  # Path for the 'downloads' directory
api_key = os.getenv('R2_API_KEY')
account_id = os.getenv('R2_ACCOUNT_ID')
base_url = 'https://api.cloudflare.com/client/v4/accounts/{}/storage/kv/namespaces'.format(account_id)

if not uri or not db_name or not collection_name or not api_key or not account_id:
    print 'One or more required environment variables are not set'
    exit(1)

def download_file(file_name, local_path='./'):
    """ Downloads a file from Cloudflare R2 and saves it to the local path """
    try:
        response = requests.get('{}/files/{}'.format(base_url, file_name), headers={
            'Authorization': 'Bearer {}'.format(api_key),
            'Content-Type': 'application/json'
        }, stream=True)

        if response.status_code != 200:
            raise Exception("Failed to download {}".format(file_name))

        with open(os.path.join(local_path, file_name), 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print "Downloaded {}".format(file_name)
    except Exception as e:
        print "Error downloading file: {}: {}".format(file_name, e)

def download_from_r2():
    """ Connects to MongoDB and downloads specified files from Cloudflare R2 """
    client = MongoClient(uri)

    try:
        client.connect()
        print 'Connected to MongoDB'

        db = client[db_name]
        collection = db[collection_name]

        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

        # Regex pattern to match files ending with '.csv'
        regex_pattern = re.compile(r'\.csv$')
        cursor = collection.find({'ipfsCID': {'$regex': regex_pattern}})

        for doc in cursor:
            if 'ipfsCID' in doc:
                print "Downloading file: {}".format(doc['ipfsCID'])
                download_file(doc['ipfsCID'], downloads_dir)
    except Exception as e:
        print "An error occurred: {}".format(e)
    finally:
        client.close()
        print 'MongoDB connection closed'

download_from_r2()
