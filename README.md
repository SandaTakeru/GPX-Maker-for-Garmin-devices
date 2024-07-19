# GPX-Maker-for-Garmin-devices
This QGIS plugin outputs vector layers as GPX files, which you can import and view on your Garmin device. Supporting point layers, line layers, and polygon layers. By optional setting, you can output features without dissolving them.<br>

# How to Make GPX
## starting method
![画像名](./001.png)<br>
Launch GPX Maker from the Processing Tools panel.<br>
## Setting method
![画像名](./002.png)<br>
① Select the vector layer to output<br>
② Select the display name on the GARMIN device (corresponding to the name attribute)<br>
③ Additional option: Do not merge features, output them separately. Checking this box will ignore ② and set the attribute specified in ③ as the name attribute.<br>
④ Set the destination to save the GPX file.<br>

## Preservation method
![画像名](./003.png)<br>
Save it in the GPX folder inside your GARMIN device.<br>

# How to Display on your Garmin devices (ex.GPSMAP67i)
![画像名](./67.bmp)<br>
### Polygons and lines
Main Menu > Saved Tracks > Select Track > Menu > Show On Map<br>

### Points
No special settings required. Displayed on the screen by default.<br>
Main Menu > Waypoint Manager (You can delete them individually.)
