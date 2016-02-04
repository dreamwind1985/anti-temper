#!/usr/bin/python

import os
import time
import httplib,urllib2,urllib
import ssl
import socket
import json

#import poster
import requests

import hashlib



def get_file_md5(filepath):
	#md5 = os.popen("md5sum "+filepath).readline().split(" ")[0].strip()
	#return md5
	with open(filepath,'rb') as f:
		md5obj = hashlib.md5()
		md5obj.update(f.read())
		md5 = md5obj.hexdigest()
		return md5



#file type
WEB_PAGE = 1
SYS_LOG = 2

class HttpClient():
	def __init__(self, host, port ,sn):
		self.host = host
		self.port = port
		self.sn = sn
	
		self.pkey="wzb"
		pass
	
	def __get_salt(self, key):
		key = str(key)+self.pkey
		ret = hashlib.md5(key)
		return ret.hexdigest()

	def post_filemd5(self, filepath):
		if os.path.isfile(filepath):
			md5 = get_file_md5(filepath)
		else:
			return
		
		filetype = WEB_PAGE
		key = self.__get_salt(md5)
		try:
			params = urllib.urlencode({"sn":self.sn, "filetype":filetype, "filepath":filepath, "md5":md5, "key":key})
			#s_params="?sn="+self.sn+"&filetype="+filetype+"&filepath="+filepath+"&md5="+md5	
			print params
			headers = {"Content-type": "application/x-www-form-urlencoded", "Accept":"text/plain"}
			hClient = httplib.HTTPSConnection(self.host, self.port, timeout=15)
			#print self.host,self.port
			sock = socket.create_connection((hClient.host, hClient.port))
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			hClient.sock = ssl.wrap_socket(sock, hClient.key_file, hClient.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)
			hClient.request("POST", "/test.php", params, headers)
			#hClient.request("POST", "/ctd/metadata", params)
			response = hClient.getresponse()
			status = response.status
			#print status	
			if( status != 200):
				print status
				read = response.read()
				print read
				print "error connection with server while post file md5"
				return
			
			read = response.read()
			print read

			self.upload_file(filepath)
			#soup = BeautifulSoup(response)
			#data = json.loads(soup.html.body.text)
			data = json.loads(read)
			print data
			
			hClient.close()
			#if(data[filepath] == 0):
			#	self.upload_file(filepath)
			#else:
			#	pass
		except Exception,e:
			print e
			
		
	def upload_file_https(self, filepath):
		if os.path.isfile(filepath):
			md5 = get_file_md5(filepath)
		else:
			return

		opener = poster.streaminghttp.register_openers()
	
		try:						
			params={'file':open(filepath,'rb'), "sn":self.sn, "filepath":filepath, "md5":md5}
		except Exception,msg:
			print msg
			print "open file  %s error"%filepath
		datagen, headers = poster.encode.multipart_encode(params)	
		upload_url = "https://"+self.host+":"+str(self.port)+"/upload_file.php"
		request = urllib2.Request(upload_url, datagen, headers)
		result = urllib2.urlopen(request)
		
		if(result.getcode() != 200):
			print "error upload file %s"%filepath
		print result.read()
		print "\n\n"
	
	def upload_file(self, filepath):
		if os.path.isfile(filepath):
			md5 = get_file_md5(filepath)
		else:
			return

		key = self.__get_salt(md5)
		
		data = {"sn":self.sn, "filepath":filepath, "md5":md5, "key":key }
		data = urllib.urlencode(data)
		files = {"file":open(filepath,"rb")}
		upload_url = "https://"+self.host+":"+str(self.port)+"/upload_file.php?"+data
		print upload_url
		#return 
		response = requests.post(upload_url, files=files, verify=False)
		print response.status_code
		print response.text			

