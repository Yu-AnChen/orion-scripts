# orion-scripts

## Use the scripts (assuming [setup](#setup-conda-envs-for-processing-only-needs-to-be-done-once-on-a-computer) is already completed)

1. Install miniconda (only needs to be done once for each user)

    - [Download the latest Windows 64-bit installer](https://docs.conda.io/en/latest/miniconda.html#windows-installers)
    - Run the installer, select install for user
    - When the installation is completed, launch the *Anaconda Prompt (Miniconda3)* application

1. Look for orion-script directory on the computer. Its recommended location is `C:\Users\Public\Downloads\orion-scripts` (only needs to be done once for each user)

1. To process images with default parameters, generate a CSV file contains the 3 columns
    - name: name of the image
    - path: full path to the image, must end with `.ome.tif` or `.ome.tiff`
    - out_dir: path to output directory, doesn't need to include the slide name

    For example, in `Z:\project-X\files.csv`, two images are listed to be processed

    ```csv
    name,path,out_dir
    Sample-A-slide-1,Z:\project-X\raw\slide-1-20221105.ome.tiff,Z:\project-X\processed
    Sample-B-slide-2,Z:\project-X\raw\slide-2-20221216.ome.tiff,Z:\project-X\processed
    ```

    In *Anaconda Prompt (Miniconda3)*, type the following and hit enter

    ```bash
    python C:\Users\Public\Downloads\orion-scripts\processing\run_all.py -c Z:\project-X\files.csv
    ```

    will process the two images and generate the following outputs

    ```bash
    Z:\project-X
    │   files.csv
    │
    ├───processed
    │   ├───Sample-A-slide-1
    │   │   ├───segmentation
    │   │   │   └───slide-1-20221105
    │   │   │       │   cellRing.ome.tif
    │   │   │       │   cytoRing.ome.tif
    │   │   │       │   nucleiRing.ome.tif
    │   │   │       │
    │   │   │       └───qc
    │   │   │               nucleiRingOutlines.ome.tif
    │   │   │
    │   │   └───unmicst2
    │   │           Sample-A-slide-1_Probabilities_0.ome.tif
    │   │
    │   └───Sample-B-slide-2
    │       ├───segmentation
    │       │   └───slide-2-20221216
    │       │       │   cellRing.ome.tif
    │       │       │   cytoRing.ome.tif
    │       │       │   nucleiRing.ome.tif
    │       │       │
    │       │       └───qc
    │       │               nucleiRingOutlines.ome.tif
    │       │
    │       └───unmicst2
    │               Sample-B-slide-2_Probabilities_0.ome.tif
    │
    └───raw
            slide-1-20221105.ome.tiff
            slide-2-20221216.ome.tiff
    ```
  
1. [Optional] Change module parameters
    - If tuning module parameter is needed, make a copy of `C:\Users\Public\Downloads\orion-scripts\processing\run_all.ini` to the project directory. E.g. `Z:\project-X\custom.ini`
    - Change the `[s3seg]` and `[unmicst]` section as needed
    - Pass the `custom.ini` to the processing call.

    In *Anaconda Prompt (Miniconda3)*, type the following and hit enter

    ```bash
    python C:\Users\Public\Downloads\orion-scripts\processing\run_all.py -c Z:\project-X\files.csv -m Z:\project-X\custom.ini
    ```

---

## Setup conda envs for processing (only needs to be done once on a computer)

1. Install miniconda

    - [Download the latest Windows 64-bit
      installer](https://docs.conda.io/en/latest/miniconda.html#windows-installers)
    - Run the installer, select install for user
    - When the installation is completed, launch the *Anaconda Prompt
      (Miniconda3)* application
    - In *Anaconda Prompt (Miniconda3)*, type `git` and hit enter, if it shows
      `'git' is not recognized as an internal or external command, operable
      program or batch file.`, that means `git` isn't installed. Installed it by
      typing `conda install git` and hit enter.

1. Setup s3seg and unmicst conda env at a public location. The following uses `C:\Users\Public\Downloads\mcmicro` as parent directory

    - S3seg

      ```bash
      # Create env
      conda create -p C:\Users\Public\Downloads\mcmicro\s3seg -c conda-forge python=3.10
      # Activate env
      conda activate C:\Users\Public\Downloads\mcmicro\s3seg
      # Install dependencies from pypi
      python -m pip install palom dask[dataframe] dask-image ome_types
      ```

    - Unmicst

      ```bash
      # Create and activate env
      conda create -p C:\Users\Public\Downloads\mcmicro\unmicst -c conda-forge python=3.10
      conda activate C:\Users\Public\Downloads\mcmicro\unmicst
      # Install tensorflow GPU
      conda install -c conda-forge cudatoolkit=11.2 cudnn=8.1.0
      python -m pip install "tensorflow<2.11"
      # Test if tensorflow uses GPU
      python -c "import tensorflow; print(tensorflow.config.list_physical_devices('GPU'))"
      # Install other dependencies
      python -m pip install palom dask-image czifile nd2reader
      ```

1. Download orion-scripts from github

    The following download the scripts to `C:\Users\Public\Downloads`

    ```bash
    git clone https://github.com/Yu-AnChen/orion-scripts.git C:\Users\Public\Downloads\orion-scripts
    cd C:\Users\Public\Downloads\orion-scripts
    # Download module code
    git submodule update --init
    # Download unet model checkpoint
    curl -f -o modules/UnMicst/models/nucleiDAPILAMIN/model.ckpt.data-00000-of-00001 https://mcmicro.s3.amazonaws.com/models/unmicst2/model.ckpt.data-00000-of-00001
    ```

1. [Optional] Change default settings

    In `C:\Users\Public\Downloads\orion-scripts\processing\run_all.ini`
    - Update `[CONDA ENV PATH]` section if S3seg and/or Unmicst conda env is
      installed at different location(s).
    - Update `[log path]` section and others as needed
