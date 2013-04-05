# Copyright (c) 2013 Ira Cooper <ira@samba.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

# Change this to be where your datasets are.

DS_DIR='/var/tmp/datasets';

import os
import re
import hashlib
import base64

from bottle import route, run, template, response, HTTPError, static_file
try:
    import json
except ImportError:
    import simplejson as json

def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.digest()

def get_datasets():
    return [f for f in os.listdir(DS_DIR) if os.path.isdir(os.path.join(DS_DIR,f)) and not (f == '.' or f == '..')]

def uuid_to_img(uuid):
    return convert_ds_to_img(uuid_to_ds(uuid))

def uuid_to_ds(uuid):
    return json.loads(open(DS_DIR+"/"+uuid+"/manifest", 'r').read())

def convert_ds_to_img(js):
    return { 'v': 2, 'uuid': js['uuid'], 'urn': js['urn'], 'owner': js['creator_uuid'], 'name': js['name'], 'version': js['version'], 'description': js['description'], 'homepage': 'http://www.samba.org/', 'state':'active', 'public':True, 'published_at': js['published_at'], 'type': js['type'], 'os': js['os'], 'files': [{ 'sha1': js['files'][0]['sha1'], 'size': js['files'][0]['size'], 'compression': ('bzip2' if js['files'][0]['path'][-3:] == 'bz2' else 'gzip')}]}

@route('/ping')
def index():
    return {"ping":"pong", "version":"1.0.0", "imgapi": True}

@route('/datasets')
def index():
    response.content_type='application/json'
    return json.dumps(map(uuid_to_ds, get_datasets()))

@route('/datasets/:uuid')
def index(uuid):
    response.content_type='application/json'
    return json.dumps(uuid_to_ds(uuid))

@route('/datasets/:uuid/:file')
def index(uuid,file):
    full_name = DS_DIR+'/'+uuid+"/"+file;
    statinfo = os.stat(full_name);
    response.headers['Content-MD5'] = base64.standard_b64encode(hashfile(open(full_name,'rb'),hashlib.md5()))
    response.headers['Content-Length'] = statinfo.st_size
    return open(full_name,'rb')

@route('/images/:uuid/file')
def index(uuid):
    ds = uuid_to_ds(uuid)
    r = re.search('/([^/]+)$',ds['files'][0]['url'])
    file = r.group(0);
    full_name = DS_DIR+'/'+uuid+"/"+file;
    statinfo = os.stat(full_name);
    response.headers['Content-MD5'] = base64.standard_b64encode(hashfile(open(full_name,'rb'),hashlib.md5()))
    response.headers['Content-Length'] = statinfo.st_size
    return open(full_name,'rb')

@route('/images/:uuid')
def index(uuid):
    ans = " ";
    try:
        ans = uuid_to_img(uuid)
    except IOError:
        HTTPError(status=404)
    return ans

@route('/images')
def index():
    response.content_type='application/json'
    return json.dumps(map(uuid_to_img,get_datasets()))

run(server='paste',host='0.0.0.0', port=80)
