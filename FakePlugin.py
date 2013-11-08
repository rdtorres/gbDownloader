'''
     FakePlugin override.

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.
     
     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.
     
     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

