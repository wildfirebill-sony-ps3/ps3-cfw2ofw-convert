modified to add gui

run with
python gui.py
```
Python 3 with tkinter installed

**Features:**

- **PS3_GAME directory selection** — Browse button + auto-detect if `PS3_GAME/` is in the same folder
- **Game info display** — Reads PARAM.SFO via `sfoprint.exe` and shows title, disc ID, versions
- **Title ID conversion** — Auto-suggests the NPXX ID with full mapping reference table
- **Custom game ID** — Override the auto-suggested ID or leave blank to use default
- **Update checker** — Queries Sony's server, parses XML, shows version/size, optional download
- **File type skip options** — Radio buttons for SDAT/EDAT/SPRX/SELF (matching the batch script options 0-4)
- **Real-time log** — ScrolledText showing conversion progress
- **Conversion flow** — Copies base files, runs `make_npdata.exe` on each file, handles license generation (launches KDW tool if needed), creates LIC.EDAT

No extra dependencies required — just Python 3 with tkinter (included by default on Windows). All existing `bin/` tools are called exactly as the batch script does.





# ps3-cfw2ofw-convert
Heavily Modified Script Based on The original convert.bat from pspx.ru

![Image](http://i.imgur.com/D9sY7fx.png)
<br/><br/>

![Image](http://i.imgur.com/y7XkpRi.png)
<br/><br/>

![Image](http://i.imgur.com/oaIsiVZ.png)
<br/><br/>

![Image](http://i.imgur.com/FrhTtpt.png)
<br/><br/>

![Image](http://i.imgur.com/dOKxpsN.png)
<br/><br/>


