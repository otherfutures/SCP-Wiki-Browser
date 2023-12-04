#

# Brief Description
A commandline SCP Wiki browser. It can save entries as .txt files (or not, if you so choose), read entries aloud, and browse random entries. It also pretty prints blockquotes in an ASCII frame. 

N.B. It doesn't show images (although it does link to them in Markdown formatting), but fortunately most SCP entries are pure text. 
<br>
<br>

# Sample Screenshot
![ASCII Frame Blockquotes Sample.jpg](./Documentation%20Assets/ASCII%20Frame%20Blockquotes%20Sample.jpg)
<br>
<br>

# Configuration & Usage
1. Fill in `HEADERINFO` using one of the below (whichever you prefer; there's not much difference between the two).

Chrome: 
```
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
```

Firefox:
```
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/109.0
```

`HEADERINFO` should look something like:
```
HEADERINFO = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"
}
```
<br>
<br>

2. Fill in a filepath for `DESTINATION` (where you want to store downloaded SCP entries as .txt files). the `r` before the quotation marks are to make a string literal, which removes the need to escape `\` on Windows filepaths.
<br>
<br>

3. Adjust `LINE_WIDTH` for your terminal (if you want). Set  `CENTRED_TEXT` to `False` and uncomment `INDENTATION` if you prefer left adjusted text.
<br>
<br>

4. Save `scp-reader.py` to save your settings once you're done.
<br>
<br>

5. Install the required 3rd party libraries. You can enter `pip install -r requirements.txt` into the terminal to install the libraries in one go after `cd` to this repo.
<br>
<br>

6. Give it a go! The usage is e.g. `python scp-reader.py 10` (it will automatically find the right URL, which in this case would be https://scp-wiki.wikidot.com/scp-010 ; note that you don't have to enter `python scp.reader.py 010`). Note there are also other options available which can be passed as CLI args (e.g. `python scp-reader.py 10 -a` will read the entry aloud for you, `python scp-reader.py10 -at` if you want to read along with the audio). You can also combine CLI args (e.g. `python scp-reader 10 -r -t` to find a random SCP entry without saving it/the .txt to your computer).
<br>
<br>
<img src="./Documentation Assets/CLI Args.jpg" height="230" alt="CLI Args.jpg">
<br>
<br>

# Potential Future Updates
- Might include some ASCII art at some point
- Might dynamically generate `MAX_SCP_NUMBER` instead of hardcoding it
<br>
<br>

# Misc.
- The font I'm using in the screenshots is one called [Glass TTY VT220](https://github.com/svofski/glasstty).
- The colour I'm using is a pure black background & a font colour of #FFB000.
