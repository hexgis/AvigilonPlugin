#! /usr/bin/python
import sys
import os
import time
import urllib2
import vlc

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from constants import *

class Player(QMainWindow):
    """A simple Media Player using VLC and Qt
    """
    def __init__(self, filename, cameraId=None, master=None):
        QMainWindow.__init__(self, master)
        self.setWindowTitle("Media Player")

        # creating a basic vlc instance
        self.filename = filename
        self.instance = vlc.Instance()
        # creating an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()

        self.createUI()
        self.isPaused = True
        self.cameraId = str(cameraId)

    def createUI(self):
        """Set up the user interface, signals & slots
        """
        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        # In this widget, the video will be drawn
        self.videoframe = QFrame()
        self.palette = self.videoframe.palette()
        self.palette.setColor (QPalette.Window,
                               QColor(0,0,0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)

        self.positionslider = QSlider(Qt.Horizontal, self)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.connect(self.positionslider,
                     SIGNAL("sliderMoved(int)"), self.setPosition)

        self.hbuttonbox = QHBoxLayout()
        self.playbutton = QPushButton("Play")
        self.hbuttonbox.addWidget(self.playbutton)
        self.connect(self.playbutton, SIGNAL("clicked()"),
                     self.PlayPause)

        self.stopbutton = QPushButton("Stop")
        self.hbuttonbox.addWidget(self.stopbutton)
        self.connect(self.stopbutton, SIGNAL("clicked()"),
                     self.Stop)

        self.zoominbutton = QPushButton("Zoom In")
        self.hbuttonbox.addWidget(self.zoominbutton)
        self.zoominbutton.clicked.connect(self.ZoomIn)
        
        self.zoomoutbutton = QPushButton("Zoom Out")
        self.hbuttonbox.addWidget(self.zoomoutbutton)
        self.zoomoutbutton.clicked.connect(self.ZoomOut)

        self.movecambutton = QPushButton("Move Camera")
        self.hbuttonbox.addWidget(self.movecambutton)
        self.movecambutton.clicked.connect(self.MoveCameraMenu)
        self.movecambutton.setCheckable(True)

        self.moveupbutton = QPushButton("Up")
        self.hbuttonbox.addWidget(self.moveupbutton)
        self.moveupbutton.clicked.connect(self.MoveUp)
        self.moveupbutton.hide()

        self.movedownbutton = QPushButton("Down")
        self.hbuttonbox.addWidget(self.movedownbutton)
        self.movedownbutton.clicked.connect(self.MoveDown)
        self.movedownbutton.hide()

        self.moveleftbutton = QPushButton("Left")
        self.hbuttonbox.addWidget(self.moveleftbutton)
        self.moveleftbutton.clicked.connect(self.MoveLeft)
        self.moveleftbutton.hide()

        self.moverightbutton = QPushButton("Right")
        self.hbuttonbox.addWidget(self.moverightbutton)
        self.moverightbutton.clicked.connect(self.MoveRight)
        self.moverightbutton.hide()

        self.hbuttonbox.addStretch(1)
        # self.volumeslider = QSlider(Qt.Horizontal, self)
        # self.volumeslider.setMaximum(100)
        # self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
        # self.volumeslider.setToolTip("Volume")
        # self.hbuttonbox.addWidget(self.volumeslider)
        # self.connect(self.volumeslider,
        #              SIGNAL("valueChanged(int)"),
        #              self.setVolume)

        self.vboxlayout = QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe)
        self.vboxlayout.addWidget(self.positionslider)
        self.vboxlayout.addLayout(self.hbuttonbox)

        self.widget.setLayout(self.vboxlayout)

        open = QAction("&Open", self)
        self.connect(open, SIGNAL("triggered()"), self.OpenFile)
        exit = QAction("&Exit", self)
        self.connect(exit, SIGNAL("triggered()"), sys.exit)
        menubar = self.menuBar()
        filemenu = menubar.addMenu("&File")
        filemenu.addAction(open)
        filemenu.addSeparator()
        filemenu.addAction(exit)

        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.connect(self.timer, SIGNAL("timeout()"),
                     self.updateUI)

    def PlayPause(self):
        """Toggle play/pause status
        """
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.isPaused = True
        else:
            if self.mediaplayer.play() == -1:
                self.OpenFile()
                return
            self.mediaplayer.play()
            self.playbutton.setText("Pause")
            self.timer.start()
            self.isPaused = False

    def Stop(self):
        """Stop player
        """
        self.mediaplayer.stop()
        self.playbutton.setText("Play")

    def ZoomIn(self):
        """Zoom in
        """
        action_url = os.path.join(SERVER_IP, self.cameraId, ZOOM_IN)
        print (action_url)
        try:
            req = urllib2.urlopen(action_url).read()
            print(req)         
        except:
            pass

    def ZoomOut(self):
        """Zoom out
        """
        action_url = os.path.join(SERVER_IP, self.cameraId, ZOOM_OUT)
        print (SERVER_IP)
        try:
            req = urllib2.urlopen(action_url).read()
            print(req)         
        except:
            pass

    def MoveCameraMenu(self):
        if self.isHidden:
            self.moveupbutton.show()
            self.movedownbutton.show()
            self.moveleftbutton.show()
            self.moverightbutton.show()
            self.movecambutton.setChecked(True)
            self.isHidden = False
        else:
            self.moveupbutton.hide()
            self.movedownbutton.hide()
            self.moveleftbutton.hide()
            self.moverightbutton.hide()
            self.movecambutton.setChecked(False)
            self.isHidden = True

    def MoveUp(self):
        action_url = os.path.join(SERVER_IP, self.cameraId, TILT_UP)
        print (action_url)
        try:
            req = urllib2.urlopen(action_url).read()
            print(req)         
        except:
            pass

    def MoveDown(self):
        action_url = os.path.join(SERVER_IP, self.cameraId, TILT_DOWN)
        print (action_url)
        try:
            req = urllib2.urlopen(action_url).read()
            print(req)         
        except:
            pass

    def MoveLeft(self):
        action_url = os.path.join(SERVER_IP, self.cameraId, PAN_IN)
        print (action_url)
        try:
            req = urllib2.urlopen(action_url).read()
            print(req)         
        except:
            pass

    def MoveRight(self):
        action_url = os.path.join(SERVER_IP, self.cameraId, PAN_OUT)
        print (action_url)
        try:
            req = urllib2.urlopen(action_url).read()
            print(req)         
        except:
            pass

    def OpenFile(self, filename=None):
        """Open a media file in a MediaPlayer
        """
        if filename is None:
            return
            filename = self.filename
        if not filename:
            return

        # create the media
        self.media = self.instance.media_new(unicode(filename))
        # put the media in the media player
        self.mediaplayer.set_media(self.media)

        # parse the metadata of the file
        self.media.parse()
        # set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        # the media player has to be 'connected' to the QFrame
        # (otherwise a video would be displayed in it's own window)
        # this is platform specific!
        if sys.platform == "linux2": # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaplayer.set_agl(self.videoframe.windId())

        self.PlayPause()

    # def setVolume(self, Volume):
    #     """Set the volume
    #     """
    #     self.mediaplayer.audio_set_volume(Volume)

    def setPosition(self, position):
        """Set the position
        """
        # setting the position to where the slider was dragged
        self.mediaplayer.set_position(position / 1000.0)
        # the vlc MediaPlayer needs a float value between 0 and 1, Qt
        # uses integer variables, so you need a factor; the higher the
        # factor, the more precise are the results
        # (1000 should be enough)

    def updateUI(self):
        """updates the user interface"""
        # setting the slider to the desired position
        self.positionslider.setValue(self.mediaplayer.get_position() * 1000)

        if not self.mediaplayer.is_playing():
            # no need to call this function if nothing is played
            self.timer.stop()
            if not self.isPaused:
                # after the video finished, the play button stills shows
                # "Pause", not the desired behavior of a media player
                # this will fix it
                self.Stop()


    def start(self, isStreaming):
        self.show()
        self.resize(900, 600)
        if isStreaming:
            self.OpenFile(self.filename)
