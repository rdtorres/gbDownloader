'''
     FakePlugin override.
'''
import logging
import ConfigParser
import os
from datetime import datetime


class FakePlugin:
    def __init__(self,iniFile):
        self.propFile = iniFile
        #logging.config.fileConfig(iniFile)
        self.tainted = False
        self.log = logging.getLogger('FakePlugin')
        self.props = ConfigParser.RawConfigParser()
        if os.path.exists(self.propFile):
            self.log.info('Using Properties file:',  self.propFile)
            self.props.read(self.propFile)
        else:
            print datetime.now(), 'properties file ' +  self.propFile + ' does not exist in script directory'
            print datetime.now(), 'Execution aborted for module:', __file__
            exit()

    def __del__(self):
        if self.tainted:
            self.props.write(file(self.propFile,'wb'))

    def set_setting(self, name, data):
        self.tainted = True
        self.props.set('Global',name,data)
        return data

    def get_setting(self, name):
        try:
            return self.props.get('Global',name)
        except:
		    return None

