from reviews import Review
import random
import time
import re
from bs4 import BeautifulSoup as bs
import page_property

class ParentCrawler(object):
    def __init__(self, driver):
        self.driver = driver
        self.pagetype = 'parent_page'
        self.base_url = None
        self.url = None
        self.bookmarker = None
        self.review_list = None
        self.attrs = {}
        self.restart = False

    def update_bookmarker(self, new_pos_dict):
        self.bookmarker.update(new_pos_dict)

    def update_attr(self, new_attrs):
        self.attrs.update(new_attrs)
    
    def init_child(self):
        self.review_crawler = ReviewCrawler(self.driver)
        self.review_crawler.base_url = self.base_url
        self.review_crawler.review_list = self.review_list
        self.review_crawler.bookmarker = self.bookmarker
            
    def listfct(self, soup):
        parent_tags = soup.findAll('div',{'class':'property_title'})
        return [(x.a.text, self.base_url + x.a['href']) for x in parent_tags]

    def restartfct(self, div_list):
        if self.restart == True:
            self.restart = False
            if self.bookmarker.bookmarks.get('review_page', None):
                loc, url = zip(*div_list)
                link = re.sub('-or\d+', '', self.bookmarker.bookmarks['review_page'])                
                link = re.sub('#REVIEWS', '', link)                
                #will throw a value error if link not in url
                idx = url.index(link) if link in url else 0

                div_list = div_list[idx:]
                div_list[0] = (div_list[0][0], self.bookmarker.bookmarks['review_page'])
                return div_list
            return div_list
        else:
            return div_list        
    
    def execfct(self, item):
        self.review_crawler.url = item[1]
        self.review_crawler.update_attr(self.attrs)
        self.review_crawler.update_attr({'item_reviewed':item[0]})
        self.review_crawler.start()

    def nextfct(self, soup):
        tags = soup.find('div',{'id':'pager_top', 'class':'pgLinks'})
        try:
            next_url = tags.find(lambda tag: tag.name=='a' and tag.text == u"\u00BB")['href']
            return self.base_url + next_url
        except (TypeError, AttributeError):
            return None

    def start(self):
        while self.url: 
            self.update_bookmarker({self.pagetype:self.url})
            print 'updated'
            self.driver.get(self.url)
            time.sleep(random.randint(5,10))            
            print 'sleep'
            pdb.set_trace()
            html = self.driver.page_source
            print 'get html'
            soup = bs(html)
            print 'soup'
            div_list = self.listfct(soup)       
            print 'list'     
            div_list = self.restartfct(div_list)
            print 'restart'
            
            for item in div_list:
                self.execfct(item)

            self.url = self.nextfct(soup)

         
class ReviewCrawler(object):
    # Parent sees child and sends review crawler
    def __init__(self, driver):
        self.pagetype = 'review_page'
        self.driver = driver
        self.base_url = None
        self.url = None
        self.bookmarker = None
        self.review_list = None
        self.attrs = {}

    def update_bookmarker(self, new_pos_dict):
        self.bookmarker.update(new_pos_dict)

    def update_attr(self, new_attrs):
        self.attrs.update(new_attrs)
        
    def listfct(self, soup):
        try:        
            tags = soup.find('div',{'id':'REVIEWS'}).findChildren(recursive=False)
            reviews = filter(lambda tag: tag.has_attr('id') and 'review_' in tag['id'], tags)
        except AttributeError:
            reviews = []
        return reviews

    def page_processing(self):
        #trigger popup
        element = self.driver.find_elements_by_xpath("//span[@class='partnerRvw']/child::span")    
        try:
            element[0].click()
        except:
            pass
        time.sleep(3)

        #Close the popup
        html = self.driver.page_source
        soup = bs(html)
        p = soup.find('div',{'class':'xCloseGreen'})
        if p:
            element = self.driver.find_element_by_xpath("//div[@class='xCloseGreen']")    
            element.click()

        #Resume expanding reviews
        element = self.driver.find_elements_by_xpath("//span[@class='partnerRvw']/child::span")    
        for x in element:
            try:
                x.click()
            except:
                pass
        
    def nextfct(self, soup):
        return None
        navbar = soup.find('div',{'class': "unified pagination "})
        try:
            return self.base_url + navbar.find(lambda tag: tag.text == 'Next')['href']
        except:
            return None
        
    def execfct(self, review_soup):        
        review = Review(review_soup, self.attrs)
        self.review_list.append(review)

    def start(self):
        while self.url: 
            self.update_bookmarker({self.pagetype:self.url})
            self.driver.get(self.url)
            time.sleep(random.randint(5,10))            
            self.page_processing()
            html = self.driver.page_source
            soup = bs(html)
            div_list = self.listfct(soup)            
            
            for item in div_list[:3]:
                self.execfct(item)

            self.url = self.nextfct(soup)
