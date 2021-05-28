# MC Mapper

This is a simple application for viewing Minecraft maps.  The default view is that
of the most recently played world, centered on the player location.  Alternate worlds
can be selected with command line arguments.  The window can be panned and zoomed
with the mouse, or with the arrow keys and page up/down.  On-screen buttons can
be used to re-render the map or to center the map on the player location.

![Screenshot](https://raw.githubusercontent.com/jabbequbs/mcmapper/master/screenshot.png)

### Notes

Something like the following code can be used to extract the colors of new blocks:
```
from PIL import Image
import zipfile
jar = zipfile.ZipFile("/path/to/1.16.2.jar")
with jar.open("assets/minecraft/textures/block/cobblestone.png") as f:
    sprite = Image.open(f)
```

### TODO
* Check the region's chunk's `LastUpdate` (or `InhabitedTime`?), since file timestamps are not very reliable
* Save the map data in a Sqlite database along with relevant timestamps
* Log any unrecognized block names
* Allow selection of alternate worlds from within the app
* Allow selection of alternate dimensions from within the app
* Allow locating different players for multiplayer maps
* Allow the user to place pins/labels on the map
* Move GUI rendering into batches
* Speed up map rendering process
