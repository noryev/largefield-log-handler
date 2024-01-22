import os
import re
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
collection_name = os.getenv('COLLECTION_NAME')
downloads_dir = './analysisLogs'  # Path for the 'downloads' directory
cloudflare_worker_auth_key = os.getenv('CLOUDFLARE_WORKER_AUTH_KEY')  # New variable for the custom auth key
base_url = 'https://winter-surf-82a0.deanlaughing.workers.dev'

if not uri or not db_name or not collection_name or not cloudflare_worker_auth_key:
    logging.error('One or more required environment variables are not set')
    exit(1)

def download_file(file_name, local_path='./'):
    """ Downloads a file from Cloudflare R2 and saves it to the local path """
    try:
        logging.info('Attempting to download file: {}'.format(file_name))
        response = requests.get('{}/{}'.format(base_url, file_name), headers={
            'X-Custom-Auth-Key': cloudflare_worker_auth_key  # Using the custom auth header
        }, stream=True)

        if response.status_code != 200:
            logging.error("Failed to download {}. HTTP Status: {}. Response: {}".format(file_name, response.status_code, response.text))
            return

        with open(os.path.join(local_path, file_name), 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info("Successfully downloaded {}".format(file_name))
    except Exception as e:
        logging.exception("Error downloading file: {}".format(file_name))


def download_from_r2():
    """ Connects to MongoDB and downloads specified files from Cloudflare R2 """
    try:
        client = MongoClient(uri)
        logging.info('Connected to MongoDB')

        db = client[db_name]  # Access the database
        collection = db[collection_name]  # Access the collection

        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)
            logging.info('Created directory: {}'.format(downloads_dir))

        # Regex pattern to match files ending with '.csv'
        regex_pattern = re.compile(r'\.csv$')
        cursor = collection.find({'ipfsCID': {'$regex': regex_pattern}})

        for doc in cursor:
            if 'ipfsCID' in doc:
                logging.debug("Found file to download: {}".format(doc['ipfsCID']))
                download_file(doc['ipfsCID'], downloads_dir)
    except Exception as e:
        logging.exception("An error occurred during the MongoDB operation")
    finally:
        client.close()
        logging.info('MongoDB connection closed')

download_from_r2()
