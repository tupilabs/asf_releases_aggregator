'''
Created on Jul 5, 2013

@author: kinow
'''
from datetime import datetime, timedelta
from markmail.markmail import MarkMail
import ConfigParser
import logging
import os
import re
import sys
import tweepy

FORMAT = '%(levelname)s %(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('markmail')
logger.setLevel(logging.DEBUG)

def get_last_execution_time_and_subject(hour_difference=-3):
    last_execution = datetime.now()
    last_execution = last_execution + timedelta(hours = hour_difference)
    subject = ''
    if (not os.path.exists('last_execution')):
        return (last_execution, subject)
    f = None
    try: 
        f = open('last_execution', 'r+')
        d = f.readline()
        if (d is None or d is ''):
            f.truncate()
            f.write(str(last_execution))
        elif len(d) >= 19:
            date_token = str(d[:19])
            last_execution = datetime.strptime(date_token, '%Y-%m-%d %H:%M:%S')
            if (len(d) > 19):
                subject = str(d[19:])
    finally:
        if (f is not None):
            f.close()
    subject = subject.rstrip()
    return (last_execution, subject)

def set_last_execution_time_and_subject(subject,hour_difference=-3):
    f = None
    try: 
        f = open('last_execution', 'w+')
        f.truncate()
        last_execution = datetime.now()
        last_execution = last_execution + timedelta(hours=hour_difference)
        subject = subject.rstrip()
        f.write(str(last_execution)[:19] + subject)
    finally:
        if (f is not None):
            f.close()

def get_config():
    config = ConfigParser.ConfigParser()
    config.readfp(open('aggregator.cfg'))
    return config

if __name__ == '__main__':
    logger.info('MarkMail consumer Twitter bot')
    # config
    logger.info('Reading configuration file')
    try:
        config = get_config()
    except Exception, e:
        logger.fatal('Failed to read configuration file')
        logger.exception(e)
        sys.exit(1)
    
    # last execution
    logger.info('Reading last execution')
    try:
        (last_execution, last_subject_used) = get_last_execution_time_and_subject()
        logger.debug('Last execution: ' + str(last_execution))
        logger.debug('Last subject: ' + str(last_subject_used))
    except Exception, e:
        logger.fatal('Error getting last execution time and subject')
        logger.exception(e)
        sys.exit(1)
        
    # compile pattern used for finding announcement subjects
    p = re.compile('.*(\[ANN\]|\[ANNOUNCE\]|\[ANNOUNCEMENT\])(.*)\<.*', re.IGNORECASE)
    
    logger.info('Creating MarkMail API')
    # create markmail API
    markmail = MarkMail()
    
    logger.info('Creating Twitter API')
    # create twitter API
    consumer_key = config.get('twitter', 'consumer_key')
    consumer_secret = config.get('twitter', 'consumer_secret')
    access_key = config.get('twitter', 'access_key')
    access_token = config.get('twitter', 'access_token')
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
    
            numpages = r['search']['numpages']
            if (numpages is None or numpages < (max_pages+1)): 
                break
            
            results = r['search']['results']['result']
            
            for result in reversed(results):
                subject = result['subject']
                
                # use a regex to find [ANNOUNCE] or [ANN] and extract component/project name
                m = p.match(subject)
                if m:
                    logger.debug('New/old message found: ' + subject)
                    if (subject == last_subject_used):
                        logger.debug('Skipping message. Reason: Duplicate subject found: ' + subject)
                        continue
                    
                    try:
                        post_date = markmail.parse_date(result['date'])
                        logger.debug('New/old message date: ' + post_date.strftime("%Y-%m-%d %H:%M:%S"))
                    except Exception, e:
                        logger.fatal('Failed to parse result date: ' + str(result['date']) + '. Reason: ' + e.message)
                        continue

                    if ((last_execution - post_date) >= timedelta(0)):
                        logger.debug('Skipping message. Reason: too old. Date: ' + str(post_date))
                        continue
                    
                    last_subject_used = subject
                    
                    logger.debug('Composing new tweet for ' + m.group(2))
                    # extract tweet body
                    tweet_message = m.group(2)
                    tweet_url = markmail.base + result['url']
                    tweet_tags = '#asf #opensource #announce'
                    # shorten message
                    remaining_length = 140 - (url_length + len(tweet_tags) -2) # 2 space
                    if len(tweet_message) > remaining_length:
                        tweet_message = tweet_message[:(remaining_length-3)] + '...' 
                    tweet_body = '%s %s %s' % (tweet_message, tweet_url, tweet_tags)
                    
                    logger.info('Tweeting new release: ' + m.group(2))
                    tweet_counter+=1
                    #twitter.update_status(tweet_body)
                    
        except Exception, e:
            logger.exception(e)
    
    logger.debug('Updating execution time')
    try:
        set_last_execution_time_and_subject(last_subject_used)
    except Exception, e:
        logger.fatal('Error setting last execution time and subject')
        logger.exception(e)
        sys.exit(1)
    
    logger.info('Found ' + (str(tweet_counter)) + ' new releases')
    sys.exit(0)
