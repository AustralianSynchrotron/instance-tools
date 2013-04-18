#-------------------------------------------------------------
#           Monitor server for a cloud instance
#
#  Features:
#  - shutdown the instance after a specified time
#  - cancel and list running shutdowns
#  - sets a metadata value
#-------------------------------------------------------------

import os
import sys
import argparse
import time
import datetime
import logging
import ConfigParser
import json
import urllib2

from tornado.web import RequestHandler, Application, asynchronous
from tornado.httpserver import HTTPRequest
from tornado.ioloop import IOLoop
import tornado.log

from subprocess import call

# enable logging
tornado.log.enable_pretty_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# get the OpenStack token
def getOpenStackToken():
    conf = Configuration()
    headers = {'Content-Type': 'application/json'}
    body = {'auth' :{'passwordCredentials': {'username': conf['username'], 'password': conf['password']}, 'tenantId': conf['tenantId']}}
    url = conf['authURL']+'/tokens'
    req = urllib2.Request(url, headers=headers, data=json.dumps(body))
    resp = urllib2.urlopen(req)
    j = json.loads(resp.read())
    return j['access']['token']['id']

# get the instance ID
def getInstanceID():
    url = 'http://169.254.169.254/openstack/2012-08-10/meta_data.json'
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    j = json.loads(resp.read())
    return j['uuid']

# set the instance's "nexel-ready" flag to true
def setMetadata(token, instanceID, name, value):
    if name == '':
        return
    conf = Configuration()
    headers = {'Content-Type': 'application/json'}
    headers['X-Auth-Token'] = token
    body = {'metadata': {name: value}}
    url = conf['novaURL']+'/'+conf['tenantId']+'/servers/'+instanceID+'/metadata'
    req = urllib2.Request(url, headers=headers, data=json.dumps(body))
    urllib2.urlopen(req)

# terminate the instance
def terminateInstance(token, instanceID):
    conf = Configuration()
    headers = {'Content-Type': 'application/json'}
    headers['X-Auth-Token'] = token
    url = conf['novaURL']+'/'+conf['tenantId']+'/servers/'+instanceID
    req = urllib2.Request(url, headers=headers)
    req.get_method = lambda: 'DELETE'
    urllib2.urlopen(req)


# list of timeout handlers
class __TimeoutSingleton(object):
    l = []

def Timeout():
    return __TimeoutSingleton().l


# configuration
class __ConfigurationSingleton(object):
    d = {}

def Configuration():
    return __ConfigurationSingleton().d


class ShutdownInstance():

    _timoutHandle = None

    def _shutdownInstance(self):
        handle = next((item for item in Timeout() if item['handle'] == self._timoutHandle), None)
        if handle != None:
            del Timeout()[:]
            terminateInstance(getOpenStackToken(), getInstanceID())

    def addToIOLoop(self, timeout):
        if timeout > -1:
            self._timoutHandle = IOLoop.instance().add_timeout(time.time()+(timeout*60),self._shutdownInstance)
            Timeout().append({'handle'   : self._timoutHandle,
                              'start'    : time.time(),
                              'duration' : timeout*60})


# handler classes
class AddShutdownHandler(RequestHandler):
    _shtdwn = ShutdownInstance()

    @asynchronous
    def post(self):
        timeout = int(self.get_argument('timeout', '-1'))
        _shtdwn.addToIOLoop(timeout)
        self.finish()


class CancelAllShutdownHandler(RequestHandler):
    @asynchronous
    def post(self):
        for item in Timeout():
            IOLoop.instance().remove_timeout(item['handle'])
        del Timeout()[:]
        self.finish()


class ListShutdownHandler(RequestHandler):
    @asynchronous
    def get(self):
        for item in Timeout():
            output = "--------------\n"
            output += "Start    : %s\n"%time.strftime("%d %b %Y %H:%M:%S", time.localtime(item['start']))
            output += "End      : %s\n"%time.strftime("%d %b %Y %H:%M:%S", time.localtime(item['start']+item['duration']))
            output += "Remaining: %i min\n"%int((item['start']+item['duration']-time.time())/60)
            self.write(output)
        self.finish()


class SetMetadataHandler(RequestHandler):
    @asynchronous
    def post(self):
        name  = self.get_argument('name', '')
        value = self.get_argument('value', '')
        setMetadata(getOpenStackToken(), getInstanceID(), name, value)
        self.finish()


def runStartScript():
    call(Configuration()['startScript'], shell=True)


def main():
    # read the configuration
    parser = argparse.ArgumentParser(prog='instmonitord',
                                     description='Instance monitor daemon')
    parser.add_argument('<config_file>', action='store',
                        help='Path to configuration file')
    args = vars(parser.parse_args())
    confPath = args['<config_file>']

    confParser = ConfigParser.ConfigParser()
    confParser.read(confPath)
    config = {}
    config['port']         = int(confParser.get('config','port'))
    config['username']     = confParser.get('config','username')
    config['password']     = confParser.get('config','password')
    config['tenantId']     = confParser.get('config','tenantId')
    config['authURL']      = confParser.get('config','authURL')
    config['novaURL']      = confParser.get('config','novaURL')
    if confParser.get('config','deleteConfig').lower() == "true":
        config['deleteConfig'] = True
    else:
        config['deleteConfig'] = False
    if confParser.get('init','countdown') != "":
        config['countdown'] = int(confParser.get('init','countdown'))
    else:
        config['countdown'] = -1
    if confParser.get('init','metadata') != "":
        config['metadata'] = json.loads(confParser.get('init','metadata'))
    else:
        config['metadata'] = {}

    Configuration().clear()
    Configuration().update(config)

    # the API of the server
    application = Application([
        (r"/shutdown/add",       AddShutdownHandler),       # Shutdown the instance after the specified time [sec]
        (r"/shutdown/cancelAll", CancelAllShutdownHandler), # Cancel all shutdown requests
        (r"/shutdown/list",      ListShutdownHandler),      # Lists all currently running shutdowns
        (r"/metadata/set",       SetMetadataHandler),       # Sets a metadata entry to the specified value
    ])

    # delete the config file if the associated flag is set to True
    if config['deleteConfig']:
        os.remove(confPath)

    # perform the init commands
    ShutdownInstance().addToIOLoop(config['countdown'])
    for key, value in config['metadata']:
        setMetadata(getOpenStackToken(), getInstanceID(), key, value)

    # Start the http server
    application.listen(config['port'])

    # start the IOLoop
    IOLoop.instance().start()
