This is a simple application for viewing Minecraft maps.  The default view is that
of the most recently played world, centered on the player location.  The window
can be panned and zoomed with the mouse.  Press `r` to re-render the map in the
background.  If the window is reactivated, it will re-center on the player location.

TODO:
    - re-draw the map when tile rendering has finished
    - launch to a list of minecraft worlds the user can select from
        - can use a minecraft block texture as the background
```
from PIL import Image
import zipfile
jar = zipfile.ZipFile("/path/to/1.16.2.jar")
with jar.open("assets/minecraft/textures/block/cobblestone.png") as f:
    sprite = Image.open(f)
```
    - render a player location indicator on the map
    - add a loading bar for the rendering process
    - speed it up
