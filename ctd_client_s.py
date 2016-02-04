#!/usr/bin/python


import os
import time
import urllib2
import Queue

import logging
import thread

from pyinotify import WatchManager, Notifier, ProcessEvent, IN_CREATE, IN_MODIFY, IN_MOVED_TO, IN_CLOSE_WRITE, IN_CLOSE_NOWRITE

try:
        import xml.etree.cElementTree as ET
except ImportError:
        import xml.etree.ElementTree as ET


LOG_PATH = "/var/log/ctd_client_log"

logger = logging.getLogger("client log")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(LOG_PATH)
fh.setLevel(logging.DEBUG)

formatter =  logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') 

fh.setFormatter(formatter)

logger.addHandler(fh)

import thread

from http_send import HttpClient

class ParseConfig():
	def __init__(self, filepath="./config.xml"):
		if( os.path.isfile(filepath) == False):
			print "error config file path"
			global logger
			logger.info("error config file path")
			exit(0)
		self.filepath = filepath
		self.conf = {}
		self.conf["ip"] = "0.0.0.0"
		self.conf["port"] = 0
		self.conf["path"] = []
		self.conf["whitepath"] = []
		self.conf["sn"]="0000-0000-0000-0000"	
	def parse_conf(self):
		try:
			tree = ET.ElementTree(file=self.filepath)
			root = tree.getroot()
			
			for node in root:
				if node.tag == "server":
					self.conf["ip"] = node.attrib["ip"]
					self.conf["port"] = int(node.attrib["port"])
					print self.conf["ip"]
					print self.conf["port"]
				elif node.tag == "auth":
					self.conf["sn"] = node.attrib["sn"]
				elif node.tag == "workpath":
					for child in node:
						if child.tag == "path":
							self.conf["path"].insert(len(self.conf["path"]), child.text)
							print self.conf["path"]
						elif child.tag == "whitepath" :
							self.conf["whitepath"].insert(len(self.conf["whitepath"]), child.text)
							print self.conf["whitepath"]
						else:
							pass
				else:
					pass
		except Exception,msg:
			print msg
			global logger
			logger.info("error reading config file")
			print "error reading config file"
			exit(0)
		print self.conf
		return True
			

def is_tmp_file(f):
	if os.path.isfile(f):
		if f[-4:] == ".swp" or f[-5:] == ".swpx":
			return True
	return False


class EventHandler(ProcessEvent):
	def __init__(self):
		self.openset = set()
		#self.sendset = set()

	def process_IN_CREATE(self, event):
		print "create"
		self.openset.add(os.path.join(event.path, event.name))
		#print os.path.join(event.path, event.name)
	def process_IN_MODIFY(self, event):
		print "modify"
		self.openset.add(os.path.join(event.path, event.name))
		#print os.path.join(event.path, event.name)
	def process_IN_MOVED_TO(self, event):
		print "moved_to"
		#print os.path.join(event.path, event.name)
		self.openset.add(os.path.join(event.path, event.name))
	def process_IN_CLOSE(self, event):
		#print "close"

		filepath = os.path.join(event.path, event.name)
		##print filepath
		if os.path.join(event.path, event.name) in self.openset:
			
			#self.sendset.add(filepath)
			global my_queue
			print filepath
			if is_tmp_file(filepath) == False:
				my_queue.put(filepath)
			self.openset.discard(filepath)




class MyQueue():
	def __init__(self, threshold = 100, maxsize = 1000):
		self.q = Queue.Queue(maxsize)
	def put(self, msg):
		self.q.put(msg)
	def get(self):
		return self.q.get()


def get_file_list(filepath):
	fileset = set()
	list_dirs=os.walk(filepath)
	for root, dirs, files in list_dirs:
		for f in files:
			fileset.add(os.path.join(root,f))
	return fileset

conf = ParseConfig()
conf.parse_conf()
my_queue = MyQueue() 

def my_inotify():
	vm = WatchManager()
	mask = IN_CREATE | IN_MODIFY | IN_MOVED_TO | IN_CLOSE_WRITE | IN_CLOSE_NOWRITE
	notifier = Notifier(vm, EventHandler())
	global conf
	for filepath in conf.conf["path"]:
		if filepath == None:
			continue
		vm.add_watch(filepath, mask, auto_add = True, rec=True)
	while True:
		try:
			notifier.process_events()
			if notifier.check_events():
				notifier.read_events()
		except Exception, msg:
			print msg
			notifier.stop()
			exit(0)

		

def main():
	global conf
	global my_queue
	http_client = HttpClient(conf.conf["ip"], conf.conf["port"], conf.conf["sn"])	
	for filepath in conf.conf["path"]:
		if filepath is None:
			continue
		
		fileset = get_file_list(filepath)
		for f in fileset:
			print f
			http_client.post_filemd5(f)
	
			
	thread.start_new_thread(my_inotify, tuple())
	while True:
		
		filepath = my_queue.get()
		http_client.upload_file(filepath)							
	
	
				
	
if __name__=="__main__":
	main()	
