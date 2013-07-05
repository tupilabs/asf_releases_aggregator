'''
Created on Jul 5, 2013

@author: kinow
'''
# markmail client
from markmail.markmail import MarkMail
# for exit code
import sys
# regex-matching against the e-mail subject
import re

# constants
MAX_PAGES = 2
TWEET_URL_LENGTH = 22

if __name__ == '__main__':
    # compile pattern used
    p = re.compile('.*(\[ANN\]|\[ANNOUNCE\])(.*)\<.*', re.IGNORECASE)
    
    # create markmail API
    markmail = MarkMail()
    
    for i in range(1, MAX_PAGES+1):
        print "Page: " + str(i)
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
                # TODO: extract component name
                if m:
                    tweet_message = m.group(2)
                    tweet_url = markmail.base + result['url']
                    tweet_tags = '#asf #opensource #announce'
                    # shorten message
                    remaining_length = 140 - (TWEET_URL_LENGTH + len(tweet_tags) -2) # 2 space
                    if len(tweet_message) > remaining_length:
                        tweet_message = tweet_message[:(remaining_length-3)] + '...' 
                    tweet_body = '%s %s %s' % (tweet_message, tweet_url, tweet_tags)
                    print tweet_body
        except:
            pass
            sys.exit(1)
    
    sys.exit(0)
