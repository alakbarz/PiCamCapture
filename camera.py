#!/usr/bin/python3

from time import sleep
from PIL import Image
import os
from datetime import datetime

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# I've chosen not to use the PiCamera library as I have tighter control over the newer
# High Quaity sensor and also because using the CLI does not lock the camera to this process.
# It is also way less buggy!

if not os.path.isdir("Captures"):
    os.system("mkdir Captures")

class PiCamCapture(Gtk.Window):
    def __init__(self):
        # Variables to control the capture when using raspistill
        self.camJPEG          = 100     # 1% to 100%
        self.camISO           = 100     # 100 to 800
        self.camShutter       = 2000000 # Max of 200000000 microseconds (200 seconds)
        self.camTimeout       = 500     # Time it takes before capturing an image (milliseconds)
        self.camTimelapseMode = False   # CURRENTLY DOES NOTHING

        Gtk.Window.__init__(self, title="PiCam Capture")

        self.set_border_width(10)
        # self.set_size_request(600, 500)

        gridSpacing = 5
        previewImage = "preview.png"

        # Creating grid and setting spacing
        self.mainGrid = Gtk.Grid()
        self.mainGrid.set_column_spacing(gridSpacing)
        self.mainGrid.set_row_spacing(gridSpacing)
        self.add(self.mainGrid)

        # Loading preview image
        self.imgPreview = Gtk.Image()
        self.imgPreview.set_from_file(previewImage)
        self.imgPreview.set_vexpand(True)
        self.mainGrid.attach(self.imgPreview, 0, 0, 1, 1) # x, y, xSpan, ySpan

        # Label
        self.lblSaveDir = Gtk.Label()
        self.lblSaveDir.set_label("Start by capturing an image")

        # Preview button
        self.btnPreview = Gtk.Button(label="Preview")
        self.btnPreview.connect("clicked", self.preview)
        self.btnPreview.set_tooltip_text("Open preview from camera for 5 seconds")

        # Capture button
        self.btnCapture = Gtk.Button(label="Capture")
        self.btnCapture.connect("clicked", self.capture)
        self.btnCapture.set_tooltip_text("Capture image from Raspberry Pi Camera")

        # Save captured image button
        self.btnSaveImage = Gtk.Button(label="Save Image")
        self.btnSaveImage.connect("clicked", self.saveImage)
        self.btnSaveImage.set_tooltip_text("Save current image")
        self.btnSaveImage.set_sensitive(False)

        # Delete captured image button
        self.btnDeleteImage = Gtk.Button(label="Delete Image")
        self.btnDeleteImage.connect("clicked", self.deleteImage)
        self.btnDeleteImage.set_tooltip_text("Delete current image (does not delete saved images from Captures folder)")
        self.btnDeleteImage.set_sensitive(False)

        # Grid for the controls
        self.controlsGrid = Gtk.Grid()
        self.controlsGrid.set_column_spacing(gridSpacing)
        self.controlsGrid.set_row_spacing(gridSpacing)
        self.mainGrid.attach(self.controlsGrid, 0, 1, 1, 1)

        # ISO (sensor sensitivity) adjustment
        self.sliderISO = Gtk.Adjustment(value=200, lower=100, upper=800, step_increment=100)
        self.sliderISO.connect("value_changed", self.adjustISO)
        self.sliderISO.emit("value_changed")
        self.scaleISO = Gtk.HScale(adjustment=self.sliderISO, digits=0)
        self.scaleISO.add_mark(100, Gtk.PositionType.BOTTOM, "100")
        self.scaleISO.add_mark(200, Gtk.PositionType.BOTTOM, "200")
        self.scaleISO.add_mark(400, Gtk.PositionType.BOTTOM, "400")
        self.scaleISO.add_mark(800, Gtk.PositionType.BOTTOM, "800")
        self.scaleISO.set_tooltip_text("Sensor sensitivity (higher values produce brighter, noisier images)")

        self.lblISO = Gtk.Label()
        self.lblISO.set_label("ISO (Sensor Sensitivity)")

        self.controlsGrid.attach(self.lblISO, 0, 0, 1, 1)
        self.controlsGrid.attach(self.scaleISO, 0, 1, 1, 1)

        separator = Gtk.Separator()
        separator2 = Gtk.Separator()
        self.controlsGrid.attach_next_to(separator, self.scaleISO, Gtk.PositionType.BOTTOM, 1, 1)

        # Shutter speed adjustment
        self.sliderShutter = Gtk.Adjustment(value=1, lower=0.1, upper=60, step_increment=1)
        self.sliderShutter.connect("value_changed", self.adjustShutter)
        self.sliderShutter.emit("value_changed")
        self.scaleShutter = Gtk.HScale(adjustment=self.sliderShutter, digits=1)
        self.scaleShutter.set_hexpand(True)
        self.scaleShutter.add_mark(1, Gtk.PositionType.BOTTOM, "1s")
        self.scaleShutter.add_mark(5, Gtk.PositionType.BOTTOM, "5s")
        self.scaleShutter.add_mark(10, Gtk.PositionType.BOTTOM, "10s")
        self.scaleShutter.add_mark(30, Gtk.PositionType.BOTTOM, "30s")
        self.scaleShutter.add_mark(20, Gtk.PositionType.BOTTOM, "20s")
        self.scaleShutter.add_mark(60, Gtk.PositionType.BOTTOM, "60s")
        self.scaleShutter.set_tooltip_text("Number of seconds of exposure time (higher values produce brighter images, but moving objects will leave trails)")

        self.lblShutter = Gtk.Label()
        self.lblShutter.set_label("Exposure Time")

        self.controlsGrid.attach_next_to(self.lblShutter, separator, Gtk.PositionType.BOTTOM, 1, 1)
        self.controlsGrid.attach_next_to(self.scaleShutter, self.lblShutter, Gtk.PositionType.BOTTOM, 1, 1)
        self.controlsGrid.attach_next_to(separator2, self.scaleShutter, Gtk.PositionType.BOTTOM, 1, 1)

        # JPEG quality adjustment
        self.sliderJPEG = Gtk.Adjustment(value=95, lower=1, upper=100, step_increment=1)
        self.sliderJPEG.connect("value_changed", self.adjustJPEG)
        self.sliderJPEG.emit("value_changed")
        self.scaleJPEG = Gtk.HScale(adjustment=self.sliderJPEG, digits=0)
        self.lblJPEG = Gtk.Label()
        self.lblJPEG.set_label("JPEG Quality")
        self.scaleJPEG.add_mark(50, Gtk.PositionType.BOTTOM, "50%")
        self.scaleJPEG.add_mark(95, Gtk.PositionType.BOTTOM, "95%")
        self.scaleJPEG.set_tooltip_text("Quality of captured JPEG images (higher values preserve detail and result in larger files)")

        self.controlsGrid.attach_next_to(self.lblJPEG, separator2, Gtk.PositionType.BOTTOM, 1, 1)
        self.controlsGrid.attach_next_to(self.scaleJPEG, self.lblJPEG, Gtk.PositionType.BOTTOM, 1, 1)

        actionBar = Gtk.ActionBar()
        actionBar.set_hexpand(True)
        self.mainGrid.attach(self.lblSaveDir, 0, 2, 1, 1)
        self.mainGrid.attach(actionBar, 0, 3, 1, 1)
        self.mainGrid.attach
        actionBar.pack_start(self.btnPreview)
        actionBar.pack_start(self.btnCapture)
        actionBar.pack_start(self.btnSaveImage)
        actionBar.pack_start(self.btnDeleteImage)

    def adjustISO(self, widget):
        self.camISO = widget.get_value()
        # print("ISO: " + str(self.camISO))

    def adjustShutter(self, widget):
        self.camShutter = widget.get_value()*1000000
        # print("Shutter: " + str(self.camShutter))

    def adjustJPEG(self, widget):
        self.camJPEG = widget.get_value()
        # print("JPEG: " + str(self.camJPEG))

    def preview(self, widget):
        print("Preview start")
        os.system("raspistill -t 5000")
        print("Preview stopped")

    def capture(self, widget):
        print("Capturing image")
        command = "raspistill --exposure off -t {} -o capture.jpg --quality {} --shutter {}".format(self.camTimeout, self.camJPEG, self.camShutter)
        print(command)
        os.system(command)
        print("Capture complete")
        self.lblSaveDir.set_label(os.getcwd() + "/capture.jpg")

        # Duplicating and resizing image for preview in window
        print("Duplicating captured image")
        os.system("cp capture.jpg preview.jpg")
        image = Image.open(r"preview.jpg")
        image = image.resize((720, 540))
        image.save("preview.jpg")
        self.imgPreview.set_from_file("preview.jpg")
        self.resize(720, 750)

        # Enable save and delete image buttons
        self.btnDeleteImage.set_sensitive(True)
        self.btnSaveImage.set_sensitive(True)

    def saveImage(self, widget):
        print("Saving image")
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y-%H%M%S")
        os.system("cp capture.jpg Captures/capture-{}.jpg".format(timestamp))
        self.lblSaveDir.set_label("Image saved to: {}/Captures/".format(os.getcwd()))

    def deleteImage(self, widget):
        print("Deleting current image from directory")
        os.system("rm capture.jpg")
        print("Deleting preview image from directory")
        os.system("rm preview.jpg")

        self.imgPreview.set_from_file("preview.png")
        self.resize(600, 675)
        self.lblSaveDir.set_label("")
        self.btnDeleteImage.set_sensitive(False)
        self.btnSaveImage.set_sensitive(False)


window = PiCamCapture()
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()
