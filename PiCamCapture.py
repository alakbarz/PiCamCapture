#!/usr/bin/python3

import os
import gi
from time import sleep
from PIL import Image
from datetime import datetime
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GdkPixbuf


# I've chosen not to use the PiCamera library as I have tighter control over the newer
# High Quaity sensor using the CLI and also because the CLI does not lock the camera to
# this process. It is also way less buggy!

if not os.path.isdir("Captures"):
    os.system("mkdir Captures")

if not os.path.isdir("Timelapse"):
    os.system("mkdir Timelapse")

class PiCamCapture(Gtk.Window):
    def __init__(self):
        # Variables to control the capture when using raspistill
        self.camJPEG          = 100     # JPEG quality (1% to 100%)
        self.camAG           = 100     # Sensor ISO (100 to 800)
        self.camShutter       = 2000000 # Shutter speed (max of 200000000 microseconds (200 seconds))
        self.camTimeout       = 500     # Time it takes before capturing an image for single shots (milliseconds)

        self.camTimeJPEG      = 100     # 1% to 100%
        self.camTimeISO       = 100     # 100 to 800
        self.camTimeShutter   = 2000000 # Shutter speed (max of 200000000 microseconds (200 seconds))
        self.camTimeInterval  = 2000    # Time between timelapse captures (2 seconds)
        self.camTimeImage     = 100     # Number of images the timelapse takes
        self.camAG            = 16.0    # Analog gain (16 recommended by stackexchange)
        self.timelapseStop    = False

        self.gridSpacing = 5
        self.margin = 10
        self.previewImage = "preview.png"

        Gtk.Window.__init__(self, title="PiCam Capture")

        self.set_icon_from_file("logo64.png")

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=self.gridSpacing)
        self.add(self.vbox)

        # Use a header bar rather than a title bar
        self.headerBar = Gtk.HeaderBar()
        self.headerBar.set_show_close_button(True)
        self.headerBar.props.title = "PiCam Capture"
        self.set_titlebar(self.headerBar)

        # About button
        self.btnAbout = Gtk.Button(label="About")
        self.btnAbout.connect("clicked", self.about)
        self.btnAbout.set_tooltip_text("Capture image from Raspberry Pi Camera")

        # Add buttons to the header bar
        self.headerBar.pack_end(self.btnAbout)

        # Creating grid and setting spacing
        self.mainGrid = Gtk.Grid()
        self.mainGrid.set_column_spacing(self.gridSpacing)
        self.mainGrid.set_row_spacing(self.gridSpacing)
        # self.add(self.mainGrid)

        # Loading preview image
        self.imgPreview = Gtk.Image(margin=self.margin)
        self.imgPreview.set_from_file(self.previewImage)
        self.imgPreview.set_vexpand(True)
        self.imgPreview.set_hexpand(True)
        self.mainGrid.attach(self.imgPreview, 0, 1, 1, 1) # x, y, xSpan, ySpan

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
        self.controlsGrid = Gtk.Grid(margin=self.margin)
        self.controlsGrid.set_column_spacing(self.gridSpacing)
        self.controlsGrid.set_row_spacing(self.gridSpacing)
        self.controlsGrid.set_hexpand(True)
        # self.mainGrid.attach(self.controlsGrid, 0, 1, 1, 1)
        self.mainGrid.attach_next_to(self.controlsGrid, self.imgPreview, Gtk.PositionType.BOTTOM, 1, 1)

        # ISO (sensor sensitivity) adjustment
        self.sliderAG = Gtk.Adjustment(value=4, lower=1, upper=16, step_increment=0.5)
        self.sliderAG.connect("value_changed", self.adjustAG)
        self.sliderAG.emit("value_changed")
        self.scaleAG = Gtk.HScale(adjustment=self.sliderAG, digits=1)
        self.scaleAG.add_mark(1.0, Gtk.PositionType.BOTTOM, "1")
        self.scaleAG.add_mark(2.0, Gtk.PositionType.BOTTOM, "2")
        self.scaleAG.add_mark(4.0, Gtk.PositionType.BOTTOM, "4")
        self.scaleAG.add_mark(8.0, Gtk.PositionType.BOTTOM, "8")
        self.scaleAG.add_mark(16.0, Gtk.PositionType.BOTTOM, "16")
        self.scaleAG.set_tooltip_text("Sensor sensitivity (higher values produce brighter, noisier images)")
        self.scaleAG.set_hexpand(True)

        self.lblAG = Gtk.Label()
        self.lblAG.set_label("Analogue Gain (Sensor Sensitivity)")

        self.controlsGrid.attach(self.lblAG, 0, 0, 1, 1)
        self.controlsGrid.attach(self.scaleAG, 0, 1, 1, 1)
        # self.controlsGrid.attach_next_to(self.scaleISO, self.lblISO, Gtk.PositionType.BOTTOM, 1, 1)

        separator = Gtk.Separator()
        separator2 = Gtk.Separator()
        self.controlsGrid.attach_next_to(separator, self.scaleAG, Gtk.PositionType.BOTTOM, 1, 1)

        # Shutter speed adjustment
        self.sliderShutter = Gtk.Adjustment(value=1, lower=0.1, upper=60, step_increment=0.5)
        self.sliderShutter.connect("value_changed", self.adjustShutter)
        self.sliderShutter.emit("value_changed")
        self.scaleShutter = Gtk.HScale(adjustment=self.sliderShutter, digits=1)
        self.scaleShutter.add_mark(1, Gtk.PositionType.BOTTOM, "1s")
        self.scaleShutter.add_mark(5, Gtk.PositionType.BOTTOM, "5s")
        self.scaleShutter.add_mark(10, Gtk.PositionType.BOTTOM, "10s")
        self.scaleShutter.add_mark(20, Gtk.PositionType.BOTTOM, "20s")
        self.scaleShutter.add_mark(30, Gtk.PositionType.BOTTOM, "30s")
        self.scaleShutter.add_mark(60, Gtk.PositionType.BOTTOM, "60s")
        self.scaleShutter.set_tooltip_text("Number of seconds of exposure time (higher values produce brighter images, but moving objects will leave trails)")
        self.scaleShutter.set_hexpand(True)

        self.lblShutter = Gtk.Label()
        self.lblShutter.set_label("Exposure Time (Shutter Speed)")

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
        self.scaleJPEG.set_hexpand(True)

        self.controlsGrid.attach_next_to(self.lblJPEG, separator2, Gtk.PositionType.BOTTOM, 1, 1)
        self.controlsGrid.attach_next_to(self.scaleJPEG, self.lblJPEG, Gtk.PositionType.BOTTOM, 1, 1)

        self.actionBar = Gtk.ActionBar()
        self.mainGrid.attach_next_to(self.lblSaveDir, self.controlsGrid, Gtk.PositionType.BOTTOM, 1, 1)
        self.vbox.pack_end(self.actionBar, False, False, 0)
        self.actionBar.pack_start(self.btnPreview)
        self.actionBar.pack_start(self.btnCapture)
        self.actionBar.pack_start(self.btnSaveImage)
        self.actionBar.pack_start(self.btnDeleteImage)

        ######################################

        # Grid for the timelapse controls
        self.timelapseGrid = Gtk.Grid(margin=self.margin)
        self.timelapseGrid.set_column_spacing(self.gridSpacing)
        self.timelapseGrid.set_row_spacing(self.gridSpacing)
        self.timelapseGrid.set_hexpand(True)

        # Analogue gain (sensor sensitivity) adjustment
        self.timelapseSliderAG = Gtk.Adjustment(value=4.0, lower=1.0, upper=16.0, step_increment=0.5)
        self.timelapseSliderAG.connect("value_changed", self.adjustTimelapseAG)
        self.timelapseSliderAG.emit("value_changed")
        self.timelapseScaleAG = Gtk.HScale(adjustment=self.timelapseSliderAG, digits=1)
        self.timelapseScaleAG.add_mark(1.0, Gtk.PositionType.BOTTOM, "1")
        self.timelapseScaleAG.add_mark(2.0, Gtk.PositionType.BOTTOM, "2")
        self.timelapseScaleAG.add_mark(4.0, Gtk.PositionType.BOTTOM, "4")
        self.timelapseScaleAG.add_mark(8.0, Gtk.PositionType.BOTTOM, "8")
        self.timelapseScaleAG.add_mark(16.0, Gtk.PositionType.BOTTOM, "16")
        self.timelapseScaleAG.set_tooltip_text("Sensor sensitivity (higher values produce brighter, noisier images)")
        self.timelapseScaleAG.set_hexpand(True)

        self.timelapseLblAG = Gtk.Label()
        self.timelapseLblAG.set_label("Analogue Gain (Sensor Sensitivity)")

        self.timelapseGrid.attach(self.timelapseLblAG, 0, 0, 1, 1)
        self.timelapseGrid.attach(self.timelapseScaleAG, 0, 1, 1, 1)

        timelapseSeparator = Gtk.Separator()
        timelapseSeparator2 = Gtk.Separator()
        timelapseSeparator3 = Gtk.Separator()
        timelapseSeparator4 = Gtk.Separator()
        timelapseSeparator5 = Gtk.Separator()
        self.timelapseGrid.attach_next_to(timelapseSeparator, self.timelapseScaleAG, Gtk.PositionType.BOTTOM, 1, 1)

        # Shutter speed adjustment
        self.timelapseSliderShutter = Gtk.Adjustment(value=1, lower=0.1, upper=20, step_increment=0.5)
        self.timelapseSliderShutter.connect("value_changed", self.adjustTimelapseShutter)
        self.timelapseSliderShutter.emit("value_changed")
        self.timelapseScaleShutter = Gtk.HScale(adjustment=self.timelapseSliderShutter, digits=1)
        self.timelapseScaleShutter.add_mark(1, Gtk.PositionType.BOTTOM, "1s")
        self.timelapseScaleShutter.add_mark(2.5, Gtk.PositionType.BOTTOM, "2.5s")
        self.timelapseScaleShutter.add_mark(5, Gtk.PositionType.BOTTOM, "5s")
        self.timelapseScaleShutter.add_mark(7.5, Gtk.PositionType.BOTTOM, "7.5s")
        self.timelapseScaleShutter.add_mark(10, Gtk.PositionType.BOTTOM, "10s")
        self.timelapseScaleShutter.add_mark(15, Gtk.PositionType.BOTTOM, "15s")
        self.timelapseScaleShutter.add_mark(20, Gtk.PositionType.BOTTOM, "20s")
        self.timelapseScaleShutter.set_tooltip_text("Number of seconds of exposure time (higher values produce brighter images, but moving objects will leave trails)")
        self.timelapseScaleShutter.set_hexpand(True)

        self.timelapseLblShutter = Gtk.Label()
        self.timelapseLblShutter.set_label("Exposure Time (Shutter Speed)")

        self.timelapseGrid.attach_next_to(self.timelapseLblShutter, timelapseSeparator, Gtk.PositionType.BOTTOM, 1, 1)
        self.timelapseGrid.attach_next_to(self.timelapseScaleShutter, self.timelapseLblShutter, Gtk.PositionType.BOTTOM, 1, 1)
        self.timelapseGrid.attach_next_to(timelapseSeparator2, self.timelapseScaleShutter, Gtk.PositionType.BOTTOM, 1, 1)

        # JPEG quality adjustment
        self.timelapseSliderJPEG = Gtk.Adjustment(value=95, lower=1, upper=100, step_increment=1)
        self.timelapseSliderJPEG.connect("value_changed", self.adjustTimelapseJPEG)
        self.timelapseSliderJPEG.emit("value_changed")
        self.timelapseScaleJPEG = Gtk.HScale(adjustment=self.timelapseSliderJPEG, digits=0)
        self.timelapseLblJPEG = Gtk.Label()
        self.timelapseLblJPEG.set_label("JPEG Quality")
        self.timelapseScaleJPEG.add_mark(50, Gtk.PositionType.BOTTOM, "50%")
        self.timelapseScaleJPEG.add_mark(95, Gtk.PositionType.BOTTOM, "95%")
        self.timelapseScaleJPEG.set_tooltip_text("Quality of captured JPEG images (higher values preserve detail and result in larger files)")
        self.timelapseScaleJPEG.set_hexpand(True)

        self.timelapseGrid.attach_next_to(self.timelapseLblJPEG, timelapseSeparator2, Gtk.PositionType.BOTTOM, 1, 1)
        self.timelapseGrid.attach_next_to(self.timelapseScaleJPEG, self.timelapseLblJPEG, Gtk.PositionType.BOTTOM, 1, 1)
        self.timelapseGrid.attach_next_to(timelapseSeparator3, self.timelapseScaleJPEG, Gtk.PositionType.BOTTOM, 1, 1)

        # Timelapse interval adjustment
        self.timelapseSliderInterval = Gtk.Adjustment(value=30, lower=1, upper=300, step_increment=1)
        self.timelapseSliderInterval.connect("value_changed", self.adjustTimelapseInterval)
        self.timelapseSliderInterval.emit("value_changed")
        self.timelapseScaleInterval = Gtk.HScale(adjustment=self.timelapseSliderInterval, digits=0)
        self.timelapseLblInterval = Gtk.Label()
        self.timelapseLblInterval.set_label("Timelapse Interval")
        self.timelapseScaleInterval.add_mark(1, Gtk.PositionType.BOTTOM, "1s")
        self.timelapseScaleInterval.add_mark(15, Gtk.PositionType.BOTTOM, "15s")
        self.timelapseScaleInterval.add_mark(30, Gtk.PositionType.BOTTOM, "30s")
        self.timelapseScaleInterval.add_mark(60, Gtk.PositionType.BOTTOM, "60s")
        self.timelapseScaleInterval.add_mark(120, Gtk.PositionType.BOTTOM, "2 mins")
        self.timelapseScaleInterval.add_mark(180, Gtk.PositionType.BOTTOM, "3 mins")
        self.timelapseScaleInterval.add_mark(240, Gtk.PositionType.BOTTOM, "4 mins")
        self.timelapseScaleInterval.add_mark(300, Gtk.PositionType.BOTTOM, "5 mins")
        self.timelapseScaleInterval.set_tooltip_text("The number of seconds between each shot. Only functional if greater than exposure time")
        self.timelapseScaleInterval.set_hexpand(True)

        self.timelapseGrid.attach_next_to(self.timelapseLblInterval, timelapseSeparator3, Gtk.PositionType.BOTTOM, 1, 1)
        self.timelapseGrid.attach_next_to(self.timelapseScaleInterval, self.timelapseLblInterval, Gtk.PositionType.BOTTOM, 1, 1)
        self.timelapseGrid.attach_next_to(timelapseSeparator4, self.timelapseScaleInterval, Gtk.PositionType.BOTTOM, 1, 1)

        # Timelapse length adjustment
        self.timelapseSliderImages = Gtk.Adjustment(value=100, lower=10, upper=1000, step_increment=1)
        self.timelapseSliderImages.connect("value_changed", self.adjustTimelapseImages)
        self.timelapseSliderImages.emit("value_changed")
        self.timelapseScaleImages = Gtk.HScale(adjustment=self.timelapseSliderImages, digits=0)
        self.timelapseLblImages = Gtk.Label()
        self.timelapseLblImages.set_label("Number of Images")
        self.timelapseScaleImages.add_mark(10, Gtk.PositionType.BOTTOM, "10")
        self.timelapseScaleImages.add_mark(100, Gtk.PositionType.BOTTOM, "100")
        self.timelapseScaleImages.add_mark(200, Gtk.PositionType.BOTTOM, "200")
        self.timelapseScaleImages.add_mark(300, Gtk.PositionType.BOTTOM, "300")
        self.timelapseScaleImages.add_mark(400, Gtk.PositionType.BOTTOM, "400")
        self.timelapseScaleImages.add_mark(500, Gtk.PositionType.BOTTOM, "500")
        self.timelapseScaleImages.add_mark(600, Gtk.PositionType.BOTTOM, "600")
        self.timelapseScaleImages.add_mark(700, Gtk.PositionType.BOTTOM, "700")
        self.timelapseScaleImages.add_mark(800, Gtk.PositionType.BOTTOM, "800")
        self.timelapseScaleImages.add_mark(900, Gtk.PositionType.BOTTOM, "900")
        self.timelapseScaleImages.add_mark(1000, Gtk.PositionType.BOTTOM, "1000")
        self.timelapseScaleImages.set_tooltip_text("The number of images in the timelapse")
        self.timelapseScaleImages.set_hexpand(True)

        self.timelapseGrid.attach_next_to(self.timelapseLblImages, timelapseSeparator4, Gtk.PositionType.BOTTOM, 1, 1)
        self.timelapseGrid.attach_next_to(self.timelapseScaleImages, self.timelapseLblImages, Gtk.PositionType.BOTTOM, 1, 1)

        self.lblTimelapseStatus = Gtk.Label(margin=25)
        self.lblTimelapseStatus.set_label("Start by clicking capture")

        self.timelapseGrid.attach_next_to(timelapseSeparator5, self.timelapseScaleImages, Gtk.PositionType.BOTTOM, 1, 1)
        self.timelapseGrid.attach_next_to(self.lblTimelapseStatus, timelapseSeparator5, Gtk.PositionType.BOTTOM, 1, 1)

        # Switching between single and timelapse shooting
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(500)
        self.stack.add_titled(self.mainGrid, "single", "Single")
        self.stack.add_titled(self.timelapseGrid, "timelapse", "Timelapse")

        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.stack)
        self.headerBar.pack_start(self.stack_switcher)
        self.vbox.pack_start(self.stack, True, True, 0)

    def test(self, widget, ):
        print("visible child changed")

    def adjustAG(self, widget):
        self.camAG = widget.get_value()
        # print("Analogue Gain: " + str(self.camAG))

    def adjustShutter(self, widget):
        self.camShutter = widget.get_value()*1000000
        # print("Shutter: " + str(self.camShutter))

    def adjustJPEG(self, widget):
        self.camJPEG = widget.get_value()
        # print("JPEG: " + str(self.camJPEG))

    def adjustTimelapseAG(self, widget):
        self.camTimeISO = widget.get_value()
        # print("Timelapse Sensitivity: " + str(self.camTimeAG))

    def adjustTimelapseShutter(self, widget):
        self.camTimeShutter = widget.get_value()*1000000
        # print("Timelapse Shutter: " + str(self.camTimeShutter))

    def adjustTimelapseJPEG(self, widget):
        self.camTimeJPEG = widget.get_value()
        # print("Timelapse JPEG: " + str(self.camTimeJPEG))

    def adjustTimelapseInterval(self, widget):
        self.camTimeInterval = widget.get_value()
        # print("Interval: " + str(self.camTimeInterval))

    def adjustTimelapseImages(self, widget):
        self.camTimeImage = widget.get_value()
        # print("Images: " + str(self.camTimeImage))

    def about(self, widget):
        about = Gtk.AboutDialog()
        about.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_scale("logo.png", 128, 128, True))
        about.set_program_name("PiCam Capture")
        about.set_version("Version 1.0 (13 Mar 2021)")
        about.set_name("Name")
        about.set_authors(["Alakbar"])
        about.set_comments("A simple app for astrophotography on a Raspberry Pi")
        about.set_website("https://alak.bar")
        about.set_website_label("https://alak.bar")
        about.set_copyright("Created for final year honours project")
        about.run()
        about.destroy()

    def preview(self, widget):
        print("Preview start")
        os.system("raspistill --exposure off -t 6000 --shutter 1000000.0 --analoggain 16.0")
        print("Preview stopped")

    def capture(self, widget):
        if self.stack.get_visible_child_name() == "single":
            print("Capturing image")
            command = "raspistill --exposure off -t 500 -o capture.jpg --quality {} --shutter {} --analoggain {}".format(self.camJPEG, self.camShutter, self.camAG)
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

        elif self.stack.get_visible_child_name() == "timelapse":
            print("Capturing timelapse")

            now = datetime.now()
            self.timestamp = now.strftime("%d-%m-%Y-%H%M%S")

            os.system("mkdir Timelapse/{}".format(self.timestamp))
            
            for i in range(int(self.camTimeImage)):
                command = "raspistill --exposure off -t 500 -o Timelapse/{}/timelapse{}.jpg --quality {} --shutter {} --analoggain {}".format(self.timestamp, i, self.camJPEG, self.camTimeShutter, self.camAG)
                print("\n")
                print(command)
                os.system(command)
                sleep(self.camTimeInterval)

            print("Capturing timelapse complete")
            self.lblTimelapseStatus.set_label("Timelapse saved to: {}/Timelapse/{}/".format(os.getcwd(), self.timestamp))


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
