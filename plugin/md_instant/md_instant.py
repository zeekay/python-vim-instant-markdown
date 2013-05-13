# -*- coding: utf-8 -*-

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import threading
import sys
import os
import json
from markdown import markdown

import ws

markdown_options = ['extra', 'codehilite']
current_dir = os.path.dirname(os.path.abspath(__file__))

import re
from hashlib import md5

def gfm(text):
    # Extract pre blocks.
    extractions = {}
    def pre_extraction_callback(matchobj):
        digest = md5(matchobj.group(0)).hexdigest()
        extractions[digest] = matchobj.group(0)
        return "{gfm-extraction-%s}" % digest
    pattern = re.compile(r'<pre>.*?</pre>', re.MULTILINE | re.DOTALL)
    text = re.sub(pattern, pre_extraction_callback, text)

    # Prevent foo_bar_baz from ending up with an italic word in the middle.
    def italic_callback(matchobj):
        s = matchobj.group(0)
        if list(s).count('_') >= 2:
            return s.replace('_', '\_')
        return s
    pattern = re.compile(r'^(?! {4}|\t)\w+(?<!_)_\w+_\w[\w_]*', re.MULTILINE | re.UNICODE)
    text = re.sub(pattern, italic_callback, text)

    # In very clear cases, let newlines become <br /> tags.
    def newline_callback(matchobj):
        if len(matchobj.group(1)) == 1:
            return matchobj.group(0).rstrip() + '  \n'
        else:
            return matchobj.group(0)
    pattern = re.compile(r'^[\w\<][^\n]*(\n+)', re.MULTILINE | re.UNICODE)
    text = re.sub(pattern, newline_callback, text)

    # Insert pre block extractions.
    def pre_insert_callback(matchobj):
        return '\n\n' + extractions[matchobj.group(1)]
    text = re.sub(r'{gfm-extraction-([0-9a-f]{32})\}', pre_insert_callback, text)

    return text

def markdown_to_html(data):
    return markdown(gfm('\n'.join(data).decode('utf-8')), markdown_options)

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        f = open(current_dir+'/index.html', 'r')
        data = f.read()
        self.wfile.write(data)
        f.close()

def sendall(data):
    threading.Thread(target=ws.sendall, args=(json.dumps({'type': 'html', 'html': markdown_to_html(data)}),)).start()

def startbrowser():
    url = 'http://localhost:7000/'
    if sys.platform.startswith('darwin'):
        os.system('open -g '+url)
    elif sys.platform.startswith('win'):
        os.system('start '+url)
    else:
        os.system('xdg-open '+url)

t_server = None
t_ws = None

def startserver():
    s = HTTPServer(('', 7000), MyHandler)
    s.serve_forever()

def stopserver():
    threading.Thread(target=ws.sendall, args=(json.dumps({'type': 'close'}),)).start()
    t_server._Thread__stop()
    t_ws._Thread__stop()

def main(content):
    global t_server, t_ws
    t_server = threading.Thread(target=startserver)
    t_ws = threading.Thread(target=ws.main, args=(markdown_to_html(content),))
    t_server.start()
    t_ws.start()
