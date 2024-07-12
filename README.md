# GPX-Maker-for-Garmin-devices
This QGIS plugin outputs vector layers as GPX files, which you can import and view on your Garmin device. Supporting point layers, line layers, and polygon layers. By optional setting, you can output features without dissolving them.<br>

# How to Make GPX
## starting method
![画像名](./画像4.png)<br>
Launch GPX Maker from the Processing Tools panel.<br>
## Setting method
![画像名](./画像5.png)<br>
① Select the vector layer to output<br>
② Select the display name on the GARMIN device (corresponding to the name attribute)<br>
③ Additional option: Do not merge features, output them separately. Checking this box will ignore ② and set the attribute specified in ③ as the name attribute.<br>
④ Set the destination to save the GPX file.<br>

## Preservation method
![画像名](./画像6.png)<br>
Save it in the GPX folder inside your GARMIN device.<br>

# How to Display on your Garmin devices (ex.GPSMAP67i)
### Polygons and lines
Main menu > Track management > Track name > Menu > Display on map<br>

### Points
No special settings required. Displayed on the screen by default.<br>
Main menu > Point manager (You can delete them individually.)
