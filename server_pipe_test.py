#!/usr/bin/env python
# coding: utf-8

from multiprocessing import Process, Pipe
import subprocess
import os
import bokeh
import threading
from psutil import process_iter
from signal import SIGTERM
import git
from git import Repo
import signal
import time
import yaml

class jupterNotebook:
    '''
    The jupterNotebook class represents a single juypter notebook.
    A jupterNotebook object has all the information needed to server the notebook to a bokeh server.
    '''
    def __init__(self, fileName, filePath, port, hostIP):

        self.fileName = fileName
        self.hostIP = hostIP
        self.filePath = filePath
        self.port = port

    '''
    Serves the Bokeh application to the websocket. Starts
    the server on its on thread.
    '''
    def serveBokehApp(self):
        def startServer(self):
            BOKEH_ALLOW_WS_ORIGIN=str(self.hostIP)+':'+str(self.port)
            subprocess.call(['python3', '-m', 'bokeh', 'serve',  self.filePath, '--port', str(self.port),
                 '--allow-websocket-origin='+str(self.hostIP)+':'+str(self.port)])

        thread1 = threading.Thread(target=startServer, args=(self,))
        thread1.start()

    '''
    Shuttdowns the Bokeh server using npx.
    '''
    def shutdown(self):
         from psutil import process_iter
         from signal import SIGTERM

         for proc in process_iter():
             for conns in proc.connections(kind='inet'):
                 if conns.laddr.port == self.port:
                     proc.send_signal(SIGTERM)
        #subprocess.call(['npx', 'kill-port', str(self.port)])

    '''
    Getter function to return the link to the Bokeh server.
    '''
    def getPortLink(self):
        return ('http://'+str(self.hostIP)+':'+str(self.port)+'/'+self.fileName.replace(".ipynb",""))

    '''
    Getter for the port that the Bokeh server will be deployed on.
    '''
    def getPort(self):
        return self.port


class handlePorts:
    '''
    This class keeps tracks of what ports have been assinged to jupterNotebook objects
    and which ports are open to be assigned to a new notebook.
    '''
    def __init__(self, firstPortNumber):
        self.firstPortNumber = firstPortNumber
        self.openPorts = []
        self.NextNewPort = firstPortNumber

    '''
    Assigns a new port. This method opens up the next port in line to be used to the web.

    returns: new_port, an integer, the number of the new port that has been spun up.
    '''
    def assignNewPort(self):
        # Check if any previously shut down ports were shut down.
        if (len(self.openPorts)>0):
            new_port = self.openPorts[0]
            self.openPorts.remove(new_port)
            #subprocess.call(['EXPOSE', str(new_port)])
            return new_port
        else:
            self.NextNewPort = self.NextNewPort+1
            #subprocess.call(['EXPOSE', str(self.NextNewPort-1)])
            return(self.NextNewPort-1)
    '''
    This method adds back old port numbers to the list of avalible ports.
    It stops allowing web traffic to the port.
    '''
    def addBackOldPort(self, oldPort):
        #subprocess.call(['ufw', 'deny', str(oldPort)])
        self.openPorts.append(oldPort)


class jupterNoteBookList:
    '''
    This class represents a colection of jupterNotebook objects that corrispond to the .ipynb files in a git hub repo.
    '''
    def __init__(self, gitHubLink, portStart, hostIP):
        self.hostIP = hostIP
        self.gitHubLink = gitHubLink
        self.repoDir = os.getcwd()+"/notebooks"
        if(os.path.isdir(self.repoDir)==False):
            Repo.clone_from(self.gitHubLink, self.repoDir)
        self.gitHubLink = gitHubLink
        self.servedFiles = 0
        self.notebookDict = {}
        self.g = git.cmd.Git(self.repoDir)
        self.g.pull(self.gitHubLink)
        self.fileArray = []
        self.BokehLinkDict = {}
        self.ports = handlePorts(portStart+1)

    '''
    This functions does one Git Pull of the repositroy to update the local files. It then updates the file list
    by searching through the file name list and adding or deleting file names as needed.
    '''
    def updateLocalFiles(self):
        self.g.pull(self.gitHubLink)
        thisPullFiles = []
        for root, dirs, files in os.walk(self.repoDir):
            if (".git" not in root):
                for f in files:
                    if(".ipynb" in f):
                        thisPullFiles.append(f)
                    if("requirements.txt" in f):
                        subprocess.call(['pip', 'install', '-r', f])

        #delete files and jupterNotebook objects from the array that have been deleted in the repo
        for oldFile in self.fileArray:
            if(oldFile not in thisPullFiles):
                self.fileArray.remove(oldFile)
                self.ports.addBackOldPort(self.notebookDict[oldFile].getPort())
                self.notebookDict[oldFile].shutdown()
                self.notebookDict.pop(oldFile)
                self.BokehLinkDict.pop(oldFile)

        # Create a new jupterNotebook object for each new .ipynb file
        for newFile in thisPullFiles:
            if newFile not in self.fileArray:
                self.fileArray.append(newFile)
                port = self.ports.assignNewPort()
                jnb = jupterNotebook(newFile, self.repoDir + "/" + newFile, port, self.hostIP)
                jnb.serveBokehApp()
                self.notebookDict[newFile] = jnb
                self.BokehLinkDict[newFile] = jnb.getPortLink()

    '''
    Driver function for the running the updateFiles method as a thread.
    '''
    def loopUpdate(self):
        def loopFunction():
            while(True):
                self.updateLocalFiles()

        threadUpdateFiles = threading.Thread(target=loopFunction, args=())
        threadUpdateFiles.start()

    '''
    Getter function for the fileArray contaning all the repositorys file names.
    '''
    def getFileArray(self):
        return self.fileArray

    '''
    Getter function for the BokehLinkDict which contains all .ipynb files and the
    link to the port where bokeh server lives.
    '''
    def getBokehLinkDict(self):
        return self.BokehLinkDict

def LoadConfigFile():
    from yaml.loader import SafeLoader
    with open(os.path.join(os.path.dirname(__file__),'config.yaml')) as f:
        return yaml.load(f, Loader=SafeLoader)

config=LoadConfigFile()

j1 = jupterNoteBookList(config['remote'], config['worker-ports']['from'], config['ip'])
#j1 = jupterNoteBookList("https://github.com/okoppe/Juypter-Notebook-Repo.git", 5000)
j1.loopUpdate()

def f(child_conn):
    child_conn.send(j1.getBokehLinkDict())
    child_conn.close()
