# Philosophy Crawler
simple wiki crawler application

## Setup Environment:

1. Create a virtual env (let's call it 'philcrawl') on your machine with Python 2.7.x
2. switch to your 'philcrawl' virtual env
3. Untar the tar.gz file and cd /path/to/philcrawl
4. Then run 
		
      pip install -r requirements.txt
      python setup.py develop


## Usage
After setting up your environment and dependencies,

1. cd /path/to/philcrawl/philcrawl, run this:

	     python philcrawler.py

      This will spit messages on stdout that look something like this:


      2016-11-07 20:36:44,939 - philcrawl.py - DEBUG - crawl of https://en.wikipedia.org/wiki/Charlie_Johnston lead to philosophy after 13 hops
      2016-11-07 20:36:45,869 - philcrawl.py - DEBUG - crawl of https://en.wikipedia.org/wiki/Alexandr_Tarabrin lead to philosophy after 15 hops
      2016-11-07 20:36:46,213 - philcrawl.py - DEBUG - crawl of https://en.wikipedia.org/wiki/Paccha lead to philosophy after 8 hops
      2016-11-07 20:36:46,213 - philcrawl.py - DEBUG - percentage pages leading to philosophy - 100.0
      2016-11-07 20:36:46,213 - philcrawl.py - DEBUG - path length distribution of 50 pages - {6: 1, 7: 6, 8: 6, 9: 8, 10: 1, 11: 7, 12: 4, 13: 7, 14: 4, 15: 2, 17: 2, 20: 1, 22: 1}
      2016-11-07 20:36:46,213 - philcrawl.py - DEBUG - this run is already optimized to reduce the number of http requests
      Philosophy Crawler took 30.2132 secs


## Notes
1. There's a config.yaml file holding different configurable variables. The 'article_limit' sets the number of pages to process. All pages are randomly selected using wikipedia's random article link;

2. To reduce the number of http requests, I setup a python dictionary datastore called 'url_depth_map' that holds the url and it's depth to the philosophy page. During the course of crawling, if any of the urls is already available in the 'url_depth_map', then, we stop the recursion right there and simply add the depth from the map to the running depth. To enable this feature, set the 'optimized' flag to true in config.yaml file. There is a significant increase in performance.
