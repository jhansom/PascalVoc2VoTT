## How To Run

```python 
>>> python VOC2VOTT.py --help
```
```
usage: VOC2VOTT.py [-h] --pascal_voc_dir PASCAL_VOC_DIR --vott_file VOTT_FILE --out_dir OUT_DIR

        Converts Pascal VOC datasets into VoTT json datasets.
        This script is for editing annotations after they have been exported, which VoTT does not support natively.


optional arguments:
  -h, --help            show this help message and exit

required arguments:
  --pascal_voc_dir PASCAL_VOC_DIR
                        Path to the directory exported by VoTT
  --vott_file VOTT_FILE
                        Path to .vott project file to convert to
  --out_dir OUT_DIR     Path to output VoTT project and annotations at
```

### Everything below has not been updated since I redid the CLI
#### The general idea is correct but some parts might be incorrect

<h5>Make sure your pascal voc data is separated into two folders, annotations [.xml] and images [.jpg, .png]</h3>
<img src="assets/a_i_images.PNG">
<h5>Set up a project in VOTT, connecting it to your dataset's images folder create a folder in which your output will be stored use that as target connection</h5>
<img src="assets/vott_setup.PNG">

<h5>When the project opens, immediately save it without making any changes</h5>
<img src="assets/save.PNG">

<h5>This will project a file `[project_name].vott` in the directory you specified as the target.</h5>
<img src="assets/saved_file.PNG">

<h5>Copy this file into this repo's root directory and rename it to `sample_vott.json` </h5>
<img src="assets/copy_rename.PNG">

<h5>Before executing, be sure to edit the `TAGS_LIST` variable in the `Converter` class with all the known classes/labels in your dataset</h5>
<img src="assets/classlist.PNG">

<h5>Now execute</h5>
<h5>`python3 main.py --out_dir [path to directory you want to store the results]  --anno_path [path to directory containing all .xml files]`</h5>

<h5>Please note that `out_dir` should be the absolute to the same directory as `[project_name].vott` mentioned earlier</h5>
<h5>Please note that `anno_path` should be the absolute to the same directory as where your dataset's images are stored.</h5>

<h5>This should produce all the necessary files that VOTT uses along with a file called `output.vott`. Rename this file to the name of `[project_name].vott` as mentioned earlier</h5>

<h5>And that's it. Close and reopen VOTT and open a local project</h5>
<img src="assets/local.PNG">

<h5>Search for the .vott file and open it</h5>
<img src="assets/vottfile.PNG">

<h5>You should now be able to see all your labelled images</h5>
<h5>This worked for me, please feel free to edit it as you see fit to make it work for you if it doesn't out of the box. Happy Coding</h5>
