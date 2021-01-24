from fractions import Fraction
from time import sleep
from gi.repository import Gtk
from PIL import Image
import gi
import os
from datetime import datetime
gi.require_version("Gtk", "3.0")

# I've chosen not to use the PiCamera library as I have tighter control over the newer
# High Quaity sensor and also because using the CLI does not lock the camera to this process.
# It is also way less buggy!

if os.path.isdir("Captures"):
    print("Captures folder already exists")
else:
    os.system("mkdir Captures")

JPEGquality = 100       # 1% to 100%
cameraISO = 100         # 100 to 800
shutterSpeed = 100      # uhh
timeout = 5000          # Time it takes before capturing an image
timelapseMode = False   # CURRENTLY DOES NOTHING



class PiCamCapture(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="PiCam Capture")

        self.set_size_request(600, 675)

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

        self.controlsGrid = Gtk.Grid()
        self.controlsGrid.set_column_spacing(gridSpacing)
        self.controlsGrid.set_row_spacing(gridSpacing)
        self.mainGrid.attach(self.controlsGrid, 0, 1, 1, 1)

        # ISO (sensor sensitivity) adjustment
        self.sliderISO = Gtk.Adjustment(value=100, lower=100, upper=800, step_increment=100)
        self.sliderISO.connect("value_changed", self.exposureSlider)
        self.sliderISO.emit("value_changed")
        self.scaleISO = Gtk.VScale(adjustment=self.sliderISO, digits=0)
        self.scaleISO.set_vexpand(True)
        self.scaleISO.set_hexpand(True)
        self.scaleISO.set_inverted(True)

        self.lblISO = Gtk.Label()
        self.lblISO.set_label("ISO")

        self.controlsGrid.attach(self.lblISO, 0, 0, 1, 1)
        self.controlsGrid.attach(self.scaleISO, 0, 1, 1, 1)

        # JPEG quality adjustment
        self.sliderJPEG = Gtk.Adjustment(value=100, lower=1, upper=100, step_increment=1)
        self.sliderJPEG.connect("value_changed", self.exposureSlider)
        self.sliderJPEG.emit("value_changed")
        self.scaleJPEG = Gtk.VScale(adjustment=self.sliderJPEG, digits=0)
        self.scaleJPEG.set_vexpand(True)
        self.scaleJPEG.set_hexpand(True)
        self.scaleJPEG.set_inverted(True)
        # self.scaleJPEG.add_mark(80, Gtk.PositionType.LEFT, "Default")


        self.lblJPEG = Gtk.Label()
        self.lblJPEG.set_label("JPEG Quality")

        self.controlsGrid.attach(self.lblJPEG, 1, 0, 1, 1)
        self.controlsGrid.attach(self.scaleJPEG, 1, 1, 1, 1)







        actionBar = Gtk.ActionBar()
        actionBar.set_hexpand(True)
        actionBar.set_vexpand(False)
        self.mainGrid.attach(self.lblSaveDir, 0, 2, 1, 1)
        self.mainGrid.attach(actionBar, 0, 3, 1, 1)
        # grid.attach_next_to(self.scale, self.imgPreview, Gtk.PositionType.BOTTOM, 1, 1)
        self.mainGrid.attach_next_to(self.lblSaveDir, self.scaleISO, Gtk.PositionType.BOTTOM, 1, 1)
        # grid.attach_next_to(actionBar, self.lblSaveDir, Gtk.PositionType.BOTTOM, 1, 1)
        self.mainGrid.attach
        actionBar.pack_start(self.btnPreview)
        actionBar.pack_start(self.btnCapture)
        actionBar.pack_start(self.btnSaveImage)
        actionBar.pack_start(self.btnDeleteImage)

    def exposureSlider(self, widget):
        print(widget.get_value())
        

    def preview(self, widget):
        print("Preview start")
        os.system("raspistill -t 5000")
        print("Preview stopped")

    def capture(self, widget):
        print("Capturing image")
        os.system("raspistill -o capture.jpg -q 100 ")
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
