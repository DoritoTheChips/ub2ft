# ub2ft
Convert [Ultrabox](https://ultraabox.github.io/) songs to [Famitracker](http://www.famitracker.com/) track.

Sort of proof of concept, this was initialy created for personal use but feel free to use to program if you find it usefull.
I am not planning to improve this project, even tho I know that VRC7 could theoretically be implemented (idc).

Reminder that this code is a sort of **PROOF OF CONCEPT** and was **NOT WRITTEN WITH PUBLIC RELEASE IN MIND**, I just wanted to release it because no one shared a converter like this online.

This program wasn't tested on any other [Beepbox](https://www.beepbox.co/) fork other than [Ultrabox](https://ultraabox.github.io/).

# Usage
[Youtube tutorial + showcase](https://youtu.be/RutCX44icm0)
1. Open your Ultrabox project
2. Export your song to a `.json` format
3. Open ub2ft and select the `.json` file you just exported
4. Once the convertion is done, select an output path where the converted file will be saved
5. Open Famitracker
5. Go to `File > Import text...`
6. Select the converted `.txt` file
7. Enjoy

# Features & limitations
- ub2ft will **only** export the 4 last channel *(ignoring the mod channel)* and will read them in the following order:
    * pulse 1
    * pulse 2
    * triangle
    * noise
- Not all effect are converted, here is a list of all effects supported by ub2ft:
    * note volume
    * detune
    * pitch slide
    * volume slide
    * apreggio
    * blip
- Some effects like volume slide have static parameters applied to them when exported - ub2ft will not change the speed of slides for exemple.
- Songs with a BPM above 255 cannot be imported in Famitracker and will need manual modification in the exported `.txt` file in order to work.
- The **only** time signature supported is **4 beats per bars**.
- The **only** rhythm supported is **8 notes per beat**.
- Any envelope effect targeting the pitch shift parameter on an instrument will be considered as a "blip" effect.
- Volume isn't 100% accurate to the original Ultrabox song.
- Song informations such as `title`, `author` and `copyright` isn't converted.
