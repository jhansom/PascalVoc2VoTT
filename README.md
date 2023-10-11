## Prerequisites
```shell
pip install tqdm
```

## Usage

```shell
python VOC2VoTT.py --help
```
```
usage: VOC2VoTT.py [-h] [--in_path IN_PATH] [--out_path OUT_PATH] --name NAME

    Creates a VoTT project and annotations from a Pascal VOC dataset.
    

options:
  -h, --help           show this help message and exit
  --in_path IN_PATH    Path of the Pascal VOC dataset
  --out_path OUT_PATH  Path to save the VoTT project and annotations to
  --name NAME          Name to give the created VoTT project
```

The only mandatory argument is --name which is used to specify the name of the VoTT project being created.
The absence of an --in_path or --out_path argument will cause the script to use the current working directory for that option.

## Notes
### Input
#### Pascal VOC folder
* Must contain two subfolders: **`annotations`** containing the annotations (`.xml` files) and **`images`** containing the images.
* Must also contain a **`pascal_label_map.pbtxt`** file containing the list of class labels used in the dataset. This file should have the following format:  

        item {
          id: 1
          name: 'dog'
        }

        item {
          id: 2
          name: 'cat'
        }

        item {
          id: 3
          name: 'frog'
        }



### Output
* After a successful conversion it should be possible to open the **`.vott`** file located in the output folder with the VoTT application.
