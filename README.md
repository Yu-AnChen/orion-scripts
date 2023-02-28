# orion-scripts

## Setup conda envs for processing (only needs to be done once for an user)

1. Install miniconda

    - [Download the latest installer for the target
      platform](https://docs.conda.io/en/latest/miniconda.html#windows-installers)
    - Run the installer, select install for user
    - When the installation is completed, launch the *Anaconda Prompt
      (Miniconda3)* application
    - In **Anaconda Prompt (Miniconda3)**, type `git` and hit enter, if it shows
      `'git' is not recognized as an internal or external command, operable
      program or batch file.`, that means `git` isn't installed. Installed it by
      typing `conda install git` and hit enter.

1. Create and setup s3seg and unmicst conda environment. Make sure the desired
   location isn't being used by other conda environments. The following uses
   user's home directory (`C:/Users/%USERNAME%` on Windows machine) as parent
   directory

    - S3seg

      ```bash
      # Create env
      conda create -p ~/mcmicro/s3seg -c conda-forge python=3.10
      # Activate env
      conda activate ~/mcmicro/s3seg
      # Install dependencies from pypi
      python -m pip install palom dask[dataframe] dask-image ome_types
      ```

    - Unmicst

      ```bash
      # Create and activate env
      conda create -p ~/mcmicro/unmicst -c conda-forge python=3.10
      conda activate ~/mcmicro/unmicst
      ```

      In the activated conda env, follow the [instruction from
      `tensorflow`](https://www.tensorflow.org/install/pip) to install
      tensorflow.

      *For Windows Native*

      ```bash
      # Install tensorflow GPU
      conda install -c conda-forge cudatoolkit=11.2 cudnn=8.1.0
      python -m pip install "tensorflow<2.11"
      ```
      <details>
      <summary><em>For Linux</em></summary>

      ```bash
      # Install tensorflow GPU
      conda install -c conda-forge cudatoolkit=11.2.2 cudnn=8.1.0
      export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/
      python3 -m pip install tensorflow

      # Set env var upon env activation and deactivation
      mkdir -p ~/mcmicro/unmicst/etc/conda/activate.d

      echo 'export LD_LIBRARY_PATH_BACKUP="${LD_LIBRARY_PATH:-}"' >> ~/mcmicro/unmicst/etc/conda/activate.d/env_vars.sh
      echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/' >> ~/mcmicro/unmicst/etc/conda/activate.d/env_vars.sh

      mkdir -p ~/mcmicro/unmicst/etc/conda/deactivate.d

      echo 'export LD_LIBRARY_PATH="${LD_LIBRARY_PATH_BACKUP:-}"' >> ~/mcmicro/unmicst/etc/conda/deactivate.d/env_vars.sh
      echo 'unset LD_LIBRARY_PATH_BACKUP' >> ~/mcmicro/unmicst/etc/conda/deactivate.d/env_vars.sh
      ```
      </details>

      *For Windows and Linux*, test installation and continue to install other dependencies.

      ```bash
      # Test if tensorflow uses GPU
      python -c "import tensorflow; print(tensorflow.config.list_physical_devices('GPU'))"
      # Install other dependencies
      python -m pip install palom dask-image czifile nd2reader
      ```

1. Download orion-scripts from github

    The following downloads the scripts to user's home directory (`~` /
   `C:/Users/%USERNAME%` on Windows machine). 

    1. Chnage directory to home directory

        *On Windows*, in a new **Anaconda Prompt (Miniconda3)**

        ```bash
        cd /D %HOMEDRIVE%%HOMEPATH%
        ```

        *On Linux/Unix*, in a new terminal

        ```bash
        cd ~
        ```

    1. Continue to download the scripts

        ```bash
        git clone https://github.com/Yu-AnChen/orion-scripts.git
        cd orion-scripts
        # Download module code
        git submodule update --init
        # Download unet model checkpoint
        curl -f -o modules/UnMicst/models/nucleiDAPILAMIN/model.ckpt.data-00000-of-00001 https://mcmicro.s3.amazonaws.com/models/unmicst2/model.ckpt.data-00000-of-00001
        ```

1. [Optional] Change default settings

    Open `~/orion-scripts/processing/run_all.ini` **in a text editor** - 
    - Update `[CONDA ENV PATH]` section if S3seg and/or Unmicst conda env is
      installed at different location(s).
    - Update `[log path]` section and others as needed

---

## Use the scripts

1. To process images with default parameters, generate a CSV file contains the 3
   columns
    - name: name of the image
    - path: full path to the image, must end with `.ome.tif` or `.ome.tiff`
    - out_dir: path to output directory, doesn't need to include the slide name

    For example, in `Z:/project-X/files.csv`, two images are listed to be processed

    ```csv
    name,path,out_dir
    Sample-A-slide-1,Z:/project-X/raw/slide-1-20221105.ome.tiff,Z:/project-X/processed
    Sample-B-slide-2,Z:/project-X/raw/slide-2-20221216.ome.tiff,Z:/project-X/processed
    ```

    *On Windows*, in **Anaconda Prompt (Miniconda3)**, type the following and hit enter

    ```bash
    python "%HOMEDRIVE%%HOMEPATH%/orion-scripts/processing/run_all.py" -c Z:/project-X/files.csv
    ```

    *On Linux/Unix*, to run it in the background, assuming current directory is
    at `project-X`

    ```bash
    nohup python ~/orion-scripts/processing/run_all.py -c files.csv &
    ```

    will process the two images and generate the following outputs

    ```bash
    Z:/project-X
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
    - If tuning module parameter is needed, make a copy of
      `~/orion-scripts/processing/run_all.ini` to the project directory. E.g.
      `Z:/project-X/custom.ini`
    - Change the `[s3seg]` and `[unmicst]` section as needed
    - Pass the `custom.ini` to the processing call.

    *On Windows*, in **Anaconda Prompt (Miniconda3)**, type the following and hit enter

    ```bash
    python "%HOMEDRIVE%%HOMEPATH%/orion-scripts/processing/run_all.py" -c Z:/project-X/files.csv -m Z:/project-X/custom.ini
    ```

    *On Linux/Unix*, to run it in the background, assuming current directory is
    at `project-X`

    ```bash
    nohup python ~/orion-scripts/processing/run_all.py -c /mnt/orion/Mercury-3/20230227/files.csv -m /mnt/orion/Mercury-3/20230227/custom.ini &
    ```
