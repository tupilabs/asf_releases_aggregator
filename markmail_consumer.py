'''
Created on Jul 5, 2013

@author: kinow
'''
from dotenv import load_dotenv
import configparser
import sqlite3
import argparse

from datetime import datetime, timedelta

import logging
import os
import re
import sys

from markmail.markmail import MarkMail

import tweepy

ERROR_EXIT_CODE=1
SUCCESS_EXIT_CODE=0

FORMAT = '%(levelname)s %(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('markmail')
logger.setLevel(logging.DEBUG)


parser = argparse.ArgumentParser(description='markmail_consumer Twitter bot aggregator')
parser.add_argument('--dry-run', dest='dryrun', action='store_true',
                    help='Dry run for experimenting with the script, without updating the Twitter account')

args = parser.parse_args()
# args.dryrun

def set_last_execution_time_and_subject(subject, tweet_counter, conn, hour_difference=-3):
    f = None
    # try: 
    #     f = open('last_execution', 'w+')
    #     f.truncate()
    #     last_execution = datetime.now()
    #     last_execution = last_execution + timedelta(hours=hour_difference)
    #     subject = subject.rstrip()
    #     f.write(str(last_execution)[:19] + subject)
    # finally:
    #     if (f is not None):
    #         f.close()

def get_last_execution_time_and_subject(conn, hour_difference=-3):
    """Get the last execution time and message subject. The hour_difference
    parameter is used to specify the difference between the UTC time and the
    server time. Defaults to returning the current time, and an empty string,
    unless it succeeds to read the values from database, or in case of an
    error, then an exception will be thrown."""
    last_execution = None
    subject = None
    try:
        last_execution = datetime.now()
        last_execution = last_execution + timedelta(hours = hour_difference)
        subject = ''
        c = conn.cursor()
        c.execute('SELECT last_execution AS ["timestamp"], subject, count FROM executions ORDER BY last_execution LIMIT 1')
        row = c.fetchone()
        if row is not None:
            last_execution = row[0]
            subject = row[1].rstrip()
    except Exception as e:
        if conn != None:
            conn.close()
        logger.fatal('Error getting last execution time and subject')
        logger.exception(e)
        sys.exit(ERROR_EXIT_CODE)

    logger.debug('Last execution: ' + str(last_execution))
    logger.debug('Last subject: ' + str(subject))
    return (last_execution, subject)

def initialise_database():
    """Initialised the sqlite database. If non-existent, a new database and the tables will be
    created."""
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'database.sqlite'), detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    c = conn.cursor()
    c.execute('''CREATE TABLE executions
        (last_execution timestamp, subject TEXT, count INTEGER)''')
    return conn

def get_dotenv():
    """Load configuration dotEnv file .env file"""
    try:
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
    except Exception as e:
        logger.fatal('Failed to read dotEnv file')
        logger.exception(e)
        sys.exit(ERROR_EXIT_CODE)

def get_config():
    """Load configuration INI file aggregator.cfg"""
    config = None
    try:
        config = configparser.ConfigParser()
        config_file_path = os.path.join(os.path.dirname(__file__), 'aggregator.cfg')
        with open(config_file_path) as f:
            config.readfp(f)
    except Exception as e:
        logger.fatal('Failed to read configuration file')
        logger.exception(e)
        sys.exit(ERROR_EXIT_CODE)
    return config

def tweet(tweet_message, tweet_url, tweet_tags):
    # shorten message
    remaining_length = 140 - (url_length + len(tweet_tags) -2) # 2 space
    if len(tweet_message) > remaining_length:
        tweet_message = tweet_message[:(remaining_length-3)] + '...' 
    tweet_body = '%s %s %s' % (tweet_message, tweet_url, tweet_tags)
    
    logger.info('Tweeting new release: ' + m.group(2))
    tweet_counter+=1
    if twitter is not None:
        twitter.update_status(tweet_body)

def main():
    """Application entry point"""

    logger.info('MarkMail consumer Twitter bot')

    # config
    logger.info('Reading configuration file')
    config = get_config()

    logger.info('Reading dotEnv file')
    get_dotenv()
    
    logger.info('Reading sqlite database')
    conn = None
    if False == os.path.exists(os.path.join(os.path.dirname(__file__), 'database.sqlite')):
        conn = initialise_database()
    else:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'database.sqlite'), detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

    # last execution
    logger.info('Reading last execution')
    (last_execution, last_subject_used) = get_last_execution_time_and_subject(conn)

    # compile pattern used for finding announcement subjects
    p = re.compile('.*(\[ANN\]|\[ANNOUNCE\]|\[ANNOUNCEMENT\])(.*)\<.*', re.IGNORECASE)
    
    logger.info('Creating MarkMail API')
    # create markmail API
    markmail = MarkMail()
    
    twitter = None
    if args.dryrun == False:
        logger.info('Creating Twitter API')
        # create twitter API
        consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
        consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
        access_key = os.environ.get('TWITTER_ACCESS_KEY')
        access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
        auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_key, access_token)
        twitter = tweepy.API(auth)
    
    max_pages = int(config.get('markmail', 'max_pages'))
    url_length = int(config.get('twitter', 'tweet_url_length')) 
    
    tweet_counter = 0
    
    for i in range(1, max_pages+1):
        logger.info("Search MarkMail. Page: " + str(i))
        try:
            r = markmail.search('list%3Aorg.apache.announce+order%3Adate-backward', i)
    
            numpages = int(r['search']['numpages'])
            if numpages is None or numpages < (max_pages+1): 
                break
            
            results = r['search']['results']['result']
            
            for result in reversed(results):
                subject = result['subject']
                
                # use a regex to find [ANNOUNCE] or [ANN] and extract component/project name
                m = p.match(subject)
                if m:
                    logger.debug('New/old message found: ' + subject)
                    if subject == last_subject_used:
                        logger.debug('Skipping message. Reason: Duplicate subject found: ' + subject)
                        continue
                    
                    try:
                        post_date = markmail.parse_date(result['date'])
                        logger.debug('New/old message date: ' + post_date.strftime("%Y-%m-%d %H:%M:%S"))
                    except Exception as e:
                        logger.fatal('Failed to parse result date: ' + str(result['date']) + '. Reason: ' + e.message)
                        continue
                    print(type(last_execution))
                    if (last_execution - post_date) >= timedelta(0):
                        logger.debug('Skipping message. Reason: too old. Date: ' + str(post_date))
                        continue
                    
                    last_subject_used = subject
                    
                    # extract tweet body
                    tweet_message = m.group(2)
                    tweet_url = markmail.base + result['url']
                    tweet_tags = '#asf #opensource #announce'

                    logger.debug('Composing new tweet for [' + tweet_message + ']')
                    tweet(tweet_message, tweet_url, tweet_tags)
                    
        except Exception as e:
            logger.exception(e)
    
    logger.debug('Updating execution time')
    try:
        set_last_execution_time_and_subject(last_subject_used, tweet_counter, conn)
    except Exception as e:
        logger.fatal('Error setting last execution time and subject')
        logger.exception(e)
        sys.exit(ERROR_EXIT_CODE)
    
    logger.info('Found ' + (str(tweet_counter)) + ' new releases')
    conn.commit()
    conn.close()
    sys.exit(SUCCESS_EXIT_CODE)

if __name__ == '__main__':
    main()
