'''
Created on Jul 5, 2013

@author: kinow
'''
# markmail client
from markmail.markmail import MarkMail
import re
import sys
from datetime import datetime
import logging
import tweepy
import ConfigParser, os

# for exit code
# regex-matching against the e-mail subject

# constants
MAX_PAGES = 2
TWEET_URL_LENGTH = 22


def get_last_execution_time_and_subject():
    last_execution = datetime.now()
    subject = ''
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
                subject = str(d[20:])
    except:
        print "Error opening last_execution file. Check the folder permissions.:", sys.exc_info()[0]
        sys.exit(1)
    else:
        if (f is not None):
            f.close()
    
    return (last_execution, subject)

def set_last_execution_time_and_subject(subject):
    f = None
    try: 
        f = open('last_execution', 'r+')
        f.truncate()
        f.write(str(datetime.now())[:19] + subject)
    except:
        print "Error opening last_execution file. Check the folder permissions.:", sys.exc_info()[0]
        sys.exit(1)
    else:
        if (f is not None):
            f.close()

if __name__ == '__main__':
    FORMAT = '%(levelname)s %(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger('markmail')
    logger.setLevel(logging.DEBUG)
    # last execution
    (last_execution, last_subject_used) = get_last_execution_time_and_subject()
    logger.debug('Last execution: ' + str(last_execution))
    logger.debug('Last subject: ' + str(last_subject_used))
    
    # compile pattern used
    p = re.compile('.*(\[ANN\]|\[ANNOUNCE\])(.*)\<.*', re.IGNORECASE)
    
    # create markmail API
    markmail = MarkMail()
    
    # create twitter API
    config = ConfigParser.ConfigParser()
    config.readfp(open('twitter.cfg'))
    config.read(['site.cfg', os.path.expanduser('~/.myapp.cfg')])
    consumer_key = config.get('twitter', 'consumer_key')
    consumer_secret = config.get('twitter', 'consumer_secret')
    access_key = config.get('twitter', 'access_key')
    access_token = config.get('twitter', 'access_token')
    auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_token)
    twitter = tweepy.API(auth)
    
    for i in range(1, MAX_PAGES+1):
        logger.debug("Page: " + str(i))
        try:
            r = markmail.search('list%3Aorg.apache.announce+order%3Adate-backward', i)
    
            numpages = r['search']['numpages']
            if (numpages is None or numpages < (MAX_PAGES + 1)): 
                break
            
            results = r['search']['results']['result']
            
            for result in results:
                subject = result['subject']
                
                # use a regex to find [ANNOUNCE] or [ANN] and extract component/project name
                m = p.match(subject)
                if m:
                    logger.debug('New/old message found: ' + subject)
                    post_date = markmail.parse_date(result['date'])

                    if (post_date.date() < last_execution.date()):
                        logger.debug('Skipping message. Reason: too old. Date: ' + str(post_date))
                        continue
                    
                    logger.info('Tweeting ' + subject)
                    last_subject_used = subject
                    
                    # extract tweet body
                    tweet_message = m.group(2)
                    tweet_url = markmail.base + result['url']
                    tweet_tags = '#asf #opensource #announce'
                    # shorten message
                    remaining_length = 140 - (TWEET_URL_LENGTH + len(tweet_tags) -2) # 2 space
                    if len(tweet_message) > remaining_length:
                        tweet_message = tweet_message[:(remaining_length-3)] + '...' 
                    tweet_body = '%s %s %s' % (tweet_message, tweet_url, tweet_tags)
                    #print tweet_body
                    #print str(result['date'])
                    
                    twitter.update_status(tweet_body)
                    
        except:
            print "Unexpected error:", sys.exc_info()[0]
            sys.exit(1)
    
    logger.debug('Updating execution time')
    set_last_execution_time_and_subject(last_subject_used)
    
    sys.exit(0)
