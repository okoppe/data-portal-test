import os, logging, subprocess, threading, glob, signal, time, traceback,random, yaml
from flask import Flask, render_template, request, Response, send_from_directory, redirect
import os
from multiprocessing import Process,Queue,Pipe
from server_pipe_test import f

#subprocess.call(['ufw', 'allow', os.environ['PORT_START']])
#subprocess.call(['EXPOSE', os.environ['PORT_START']])
#subprocess.call(['sudo', 'ufw', 'allow', '5000'])

selectedValue2 = " "

# global config
config={}

app = Flask(__name__)
logger=app.logger

#hone directory
@app.route("/")
def index():
    parent_conn,child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()

    BokehLinkDictFlaskCopy = parent_conn.recv()
    p.join()
    return render_template("index.html", noteBookNames=list(BokehLinkDictFlaskCopy.keys()), BokehLinkDictFlaskCopy = BokehLinkDictFlaskCopy,
        bool_files = len(BokehLinkDictFlaskCopy.keys()), selectedValue = "select a notebook") #len(BokehLinkDictFlaskCopy), selectedValue = list(BokehLinkDictFlaskCopy.keys())[0],
        #linkToBokeh = BokehLinkDictFlask[selectedValue])

#path for veiwing data set inline
@app.route('/chooseDataSet/<noteBookName>', methods = ['POST', 'GET'])
def chooseDataSet(noteBookName):
    global selectedValue2
    selectedValue2 = noteBookName

    parent_conn,child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()

    BokehLinkDictFlaskCopy2 = parent_conn.recv()
    p.join()

    return render_template("index.html", noteBookNames=list(BokehLinkDictFlaskCopy2.keys()),
        bool_files = len(BokehLinkDictFlaskCopy2.keys()), selectedValue = selectedValue2,
        linkToBokeh = BokehLinkDictFlaskCopy2[selectedValue2])

#path for downloading file
@app.route("/download", methods=['GET', 'POST'])
def download():

    return send_from_directory(directory=os.getcwd()+"/notebooks", path=selectedValue2, as_attachment=True)

# //////////////////////////////////////////////////////////////////////////
def LoadConfigFile():
    from yaml.loader import SafeLoader
    with open(os.path.join(os.path.dirname(__file__),'config.yaml')) as f:
        return yaml.load(f, Loader=SafeLoader)

if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    config=LoadConfigFile()
    logger.info(f"Notebooks {config}")
    app.run(host="0.0.0.0", port=config["port"], debug=bool(config["debug"]))