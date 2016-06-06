asf_releases_aggregator
=======================

Twitter [@asf_releases](http://twitter.com/asf_releases). An automated Twitted bot aggregator.
Retrieves the last releases and tweets them for you.

Uses a simple logger in the server, [Markmail hacky Python API](https://github.com/tupilabs/markmail),
and Tweepy.

## Configuration

The bot is configured through the *aggregator.cfg* file. It is a simple INI file, with field groups.
The following code listing contains an example configuration file.

```
[aggregator]
hour_difference=+12

[markmail]
max_pages=2

[twitter]
tweet_url_length=22
consumer_key=
consumer_secret=
access_key=
access_token=
```

Fields details.

* **hour_difference** UTC time diff in the server
* **max_pages** Maximum of pages to retrieve from Markmail
* **tweet_url_length** URL length to discount from tweet message length
* **consumer_key** Twitter consumer key
* **consumer_secret** Twitter consumer secret
* **access_key** Twitter access key
* **access_token** Twitter access token

## Execution details

1. reads configuration from an INI file with group fields. The file contains settings for
aggregator, Markmail and Twitter
2. reads the last execution time and subject used by the bot
3. retrieves Markmail messages, up to a maximum of pages (step #1)
4. finds messages which title matches to a REGEX, and that are more recent then the
last execution time (step #2)
5. posts a tweet for each message found
6. updates last execution time and subject (used by step #2)

Every step includes logging that can be found in the server.

## License

The code is licensed under the Apache License v2. The Markmail API used by this code, it licensed under
the GPL license. See LICENSE.txt for more.

## Infra

The bot is hosted at TupiLabs VPS servers, and the results can be see at 
[@asf_releases](http://twitter.com/asf_releases).
