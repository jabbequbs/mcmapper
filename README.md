This is going to be a simple application for viewing Minecraft maps.

Upon launch, a window will open listing the Minecraft worlds on this machine,
most recently played first.  A background task will be spawned to map each
region in the worlds, starting with the most recent.  A map tile will be
generated for each region file and stored in the application directory.
Later on, the tile will only be refreshed if the region file is more recently
modified.  The user will be able to select a world and a new window will
open, allowing the map to be navigated.

Currently this is only set up to run on Windows, but it should be easy to
modify it to run on other operating systems, as long as Python 3.6+ is
installed.
