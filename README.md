# Beat Saber playlist generator
## Usage
### --- Interactive mode ---
You can simply run the script and thereby switch to interactive mode, which will ask you to enter the basic parameters step-by-step.
### --- Options ---
|          Option           |                    Usage                   |
|---------------------------|--------------------------------------------|
|```-h, --help```           |         help message                       |
|```-s, --songs_dir```      |      Folder with ZIPs song arhives         |
|```-n, --name```           |          Playlist name                     |
|```-a, --author```         |         Playlist author                    |
|```--online```             |  Try to use Beatsaver API for get<br> hash of map, else uses local hashing (maybe bad)      |
|```--local```              |   Force using local hashing                |
|```-i, --image```          |   Path to image for playlist cover image   |
|```-o, --output_dir```     |   Set custom output dir.<br>By default "songs" in folder with ZIPs   |
|```--dry-run```            |   Out playlist JSON to console, instead of file               |
|```-v, --verbose```        |   Show input and output folders in log                |

After completing all operations, place the folders and file.bplist to the right places.

### Example for Quest 3/3S
ModData\com.beatgames.beatsaber\Mods\PlaylistManager\Playlists\\```your_file.bplist```
ModData\com.beatgames.beatsaber\Mods\SongCore\CustomLevels\\```your_maps_folders```

## Nuances
### Local hashing 
Local hashing may not work well with some maps downloaded from Beatsaver or from somewhere else. It works for ~60% of Beat Saver maps (I haven't been able to figure out what's wrong with my hash calculation yet).
It also works great with maps downloaded from BeatSage.

