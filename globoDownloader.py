'''
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
import urllib2
import shutil
import urlparse
import os
import test.storageserverdummy as StorageServer
import argparse
import subprocess
from FakePlugin import FakePlugin
from resources.lib import globo
from datetime import datetime




class GloboDownloader:
    def __init__(self, iniFile):
        self.cache = StorageServer.StorageServer("Globosat", 12)
        self.plugin = FakePlugin(iniFile)
        self.api = globo.GloboApi(self.plugin, self.cache)

    def download(self, url, fileName):
        if self.plugin.get_setting('download_command') != None:
            return self.download_native(url, fileName)

        return self.download_urlib(url, fileName)
    
    def download_native(self, url, fileName):
        print self.plugin.get_setting('download_command') % (fileName, url)
        retCode = subprocess.call(self.plugin.get_setting('download_command') % (fileName, url)  , shell=True)
        if retCode != 0:
            print 'Error downloading file %s to %s' % (url, fileName )
            raise Exception('Error downloading file %s to %s' % (url, fileName ))
        return fileName


    def download_urlib(self, url, fileName):
        def getFileName(url,openUrl):
            if 'Content-Disposition' in openUrl.info():
                # If the response has Content-Disposition, try to get filename from it
                cd = dict(map(
                    lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
                    openUrl.info()['Content-Disposition'].split(';')))
                if 'filename' in cd:
                    filename = cd['filename'].strip("\"'")
                    if filename: return filename
            # if no filename was found above, parse it out of the final URL.
            return os.path.basename(urlparse.urlsplit(openUrl.url)[2])
    
        r = urllib2.urlopen(urllib2.Request(url))
        try:
            fileName = fileName or getFileName(url,r)
            with open(fileName, 'wb') as f:
                shutil.copyfileobj(r,f)
        finally:
            r.close()
    
        return fileName
    
    
    def printCategories(self):
        print '%-15s ==> %15s' % ('[CATEGORY NAME]','[CATEGORY]')
        categories = self.api.get_shows_by_categories()
        for slug, category in categories.items():
            print '%-15s ==> %15s' % (category['title'],slug)
    
    def printShows(self,category):
        if category not in self.api.get_shows_by_categories():
            print 'unkown category [%s]' % (category)
            return
    
        print '%-35s ==> %45s' % ('[SHOW NAME]','[URI]')
        shows = self.api.get_shows_by_categories()[category]['shows']
        for uri, name, icon in shows:
            print '%-35s ==> %45s' % (name, uri)
    
    def printShowRails(self,uri):
        print '%-35s ==> %35s' % ('[NAME]','[RAIL]')
        rails = self.api.get_rails(uri)
        for rail, name in rails:
            print '%-35s ==> %35s' % (name, rail)
    
    def printShowRailsVideos(self,uri,rail,page=1):
        kwargs = {
            'uri': uri,
            'rail': rail,
            'page': page
        }
        
        print '%-55s ==> %10s' % ('[VIDEO TITLE]','[VIDEO ID]')
        programs = self.api.get_rail_videos(**kwargs)
        for program in programs.list:
            print '%-55s ==> %10s' % (program.title,program.id)
    
    def printVideosParts(self,videoId): 
        print '%-55s ==> %10s' % ('[VIDEO TITLE]','[VIDEO PART URL]')
        videos = self.api.get_videos(videoId) 
        for video in videos:
            print '%-55s ==> %10s' % (video.title, self.api.resolve_video_url(video.id))

    def downloadRailsVideos(self, uri, rail, downloadDir, force, combine,limit):
        kwargs = {
            'uri': uri,
            'rail': rail,
            'page': 1
        }
        
        programs = self.api.get_rail_videos(**kwargs)
        for program in programs.list[:limit]:
            downloadFile = os.path.join(downloadDir,'%s.mp4' % (program.title.replace(' ','_').replace('/','_')).encode('ascii', 'ignore'))
            if os.path.exists(downloadFile) and not force:
                print 'File %s already exists. Skipping it.' % (downloadFile)
                continue
            videoPartsFiles = self.downloadVideoParts(program.id,downloadDir,force)
            if len(videoPartsFiles) > 0 and combine:
                self.combineVideoParts(downloadFile,videoPartsFiles)

    def downloadVideoParts(self, videoId, downloadDir, force):
        videosParts = self.api.get_videos(videoId)
        videoPartsFiles = []
        for video in videosParts:
            dowloadVideoPartFile = os.path.join(downloadDir,'%s.mp4' % (video.title.replace(' ','_').replace('/','_'))).encode('ascii', 'ignore')
            videoPartsFiles.append(dowloadVideoPartFile)
            if os.path.exists(dowloadVideoPartFile) and not force:
                print 'File %s already exists. Skipping it.' % (dowloadVideoPartFile)
                continue
            url = self.api.resolve_video_url(video.id)
            print "Downloading %s to %s" % (url,dowloadVideoPartFile)
            try:
                self.download(url,dowloadVideoPartFile)
                print "Downloaded %s" % (url)
            except:
                print 'Error downloading file %s' % (dowloadVideoPartFile)
                videoPartsFiles.remove(dowloadVideoPartFile)
                if os.path.exists(dowloadVideoPartFile):
                    print 'Deleting partial downloaded file %s' % ( dowloadVideoPartFile )
                    os.remove(dowloadVideoPartFile)
        return videoPartsFiles

    def combineVideoParts(self,outputFile,videos):
        intermediate_cmd = self.plugin.get_setting('ffmpeg_step')
        final_cmd = self.plugin.get_setting('ffmpeg_final')

        for video in videos:
            retCode = subprocess.call(intermediate_cmd % (video, video + '_intermediate.ts') , shell=True)
            if retCode != 0:
                print 'Error converting file %s to %s' % (video, video + '_intermediate.ts')
                return

        retCode = subprocess.call(final_cmd % ('_intermediate.ts|'.join(videos) + '_intermediate.ts', outputFile) , shell=True)
        if retCode != 0:
            print 'Error combining files %s to %s' % ('_intermediate.ts|'.join(videos) + '_intermediate.ts', outputFile)
            return

        for video in videos:
            os.remove(video)
            os.remove(video + '_intermediate.ts')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Globo downloader', description='utility used to download content from globo.com website')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    group = parser.add_mutually_exclusive_group(required=True)
    printGroup = group.add_mutually_exclusive_group()
    printGroup.add_argument('-pc', '--printCategory', help='Print Top Categories', action='store_true')
    printGroup.add_argument('-ps', '--printShow', metavar='CATEGORY', help='Print Shows')
    printGroup.add_argument('-pr', '--printRails', metavar='URI', help='Print ShowRails')
    printGroup.add_argument('-pv', '--printRailsVideos', metavar=('URI','RAIL')  , help='Print ShowRailsVideos', nargs=2)
    printGroup.add_argument('-pu', '--printVideosPartsURL', metavar='VIDEO_ID', help='Print VideoParts', nargs=1)
    group.add_argument('-dv', '--downloadVideo', metavar='VIDEO_ID', help='Download all video parts of a given video id', nargs='*')
    group.add_argument('-drv','--downloadRailVideos',  metavar=('URI','RAIL'), help='Dowload all videos, including its parts, of a given rail.', nargs=2)
    parser.add_argument('-dir','--downloadDir', metavar=('DIRECTORY'), help='Target Directory where the movies will be dowloaded', default='./')
    parser.add_argument('-ini','--iniFile', metavar=('FILE PATH'), help='Configuration file used to store username, password, gbid and video quality', default='globoDownloader.ini',  nargs=1)
    parser.add_argument('-f','--force', help='Force Download overhiding existing files', action='store_true')
    parser.add_argument('-nc','--notCombine', help='Do not compine video parts into a single file', action='store_false')
    parser.add_argument('-l','--limit',  metavar=('MAX'), help='Limit the maximum number of dowloaded videos rails', type=int, default=5)
    args = vars(parser.parse_args())
    
    #print args
    
    gd = GloboDownloader(args['iniFile'])
    
    if args['printCategory']:
        gd.printCategories()
    elif args['printShow']:
        gd.printShows(args['printShow'])
    elif args['printRails']:
        gd.printShowRails(args['printRails'])
    elif args['printRailsVideos']:
        gd.printShowRailsVideos(args['printRailsVideos'][0],args['printRailsVideos'][1])
    elif args['printVideosPartsURL']:
        gd.printVideosParts(args['printVideosPartsURL'][0])
    elif args['downloadRailVideos']:
        gd.downloadRailsVideos(args['downloadRailVideos'][0],args['downloadRailVideos'][1],args['downloadDir'],args['force'],args['notCombine'],args['limit'])
    elif args['downloadVideo']:
        for video in args['downloadVideo']:
            gd.downloadVideoParts(video,args['downloadDir'],args['force'])

