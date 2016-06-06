asf_releases_aggregator
=======================

Twitter [@asf_releases](http://twitter.com/asf_releases). An automated Twitted bot aggregator.
Retrieves the last releases and tweets them for you.

Uses a simple logger in the server, [Markmail hacky Python API](https://github.com/tupilabs/markmail),
and Tweepy. Data is stored in a local SQLite database.

## Configuration

The bot is configured through the *aggregator.cfg* file. It is a simple INI file, with field groups.
The following code listing contains an example *aggregator.cfg* configuration file.

```
[markmail]
max_pages=2

[twitter]
tweet_url_length=22
```

Fields details.

* **hour_difference** UTC time diff in the server
* **max_pages** Maximum of pages to retrieve from Markmail
* **tweet_url_length** URL length to discount from tweet message length
* **database** SQLite database connection

The Twitter credentials are stored in a *.env* [dotEnv](https://pypi.python.org/pypi/python-dotenv) file.

```
TWITTER_CONSUMER_KEY=
TWITTER_CONSUMER_SECRET=
TWITTER_ACCESS_KEY=
TWITTER_ACCESS_TOKEN=
```

This file is also in .gitignore, so that it does not get committed by accident.

The entry point script *markmail_consumer.py* accepts one parameter, *--dry-run* to
allow you running the script and inspect the would-be output. This way you do not need
the Twitter credentials, and can check if there is anything wrong with the data or
with the script.

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

## Dependencies

For a complete list, see requirements.txt. You can install them all with pip by running
`pip install -r requirements.txt`, or use *conda* to manually install them with
[Anaconda](https://www.continuum.io/).

There is one dependency that is not a PIP package, but a Git submodule. You can initialise
it by running the following set of commands.

```
git submodule init
git submodule update
```

# Maintenance

You can change values in the sqlite database. As in the following example, where we set the
last execution date manually.

```
import sqlite3
conn = sqlite3.connect('database.sqlite', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
import datetime
date = datetime.datetime(2016, 1, 1, 0, 0, 0)
c = conn.cursor()
c.execute('INSERT INTO executions(last_execution, subject, count) VALUES(?, "", 0)', (date,))
conn.commit()
conn.close()
```

## License

The code is licensed under the Apache License v2. The Markmail API used by this code, it licensed under
the GPL license. See LICENSE.txt for more.

## Infra

The bot is hosted at TupiLabs VPS servers, and the results can be see at 
[@asf_releases](http://twitter.com/asf_releases).
