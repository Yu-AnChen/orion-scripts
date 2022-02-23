#Functions for reading in single cell imaging data
#Joshua Hess

#Import necessary modules
import skimage.io
import h5py
import pandas as pd
import numpy as np
import os
import skimage.measure as measure
from pathlib import Path
import csv
from joblib import Parallel, delayed
from collections import OrderedDict


def MaskChannel(mask_loaded,image_loaded_z):
    """Function for quantifying a single channel image

    Returns a table with CellID according to the mask and the mean pixel intensity
    for the given channel for each cell"""
    dat = measure.regionprops(mask_loaded, image_loaded_z)
    n = len(dat)
    intensity_z = np.empty(n)
    for i in range(n):
        intensity_z[i] = dat[i].mean_intensity
        # Clear reference to avoid memory leak -- see MaskIDs for explanation.
        dat[i] = None
    return intensity_z

def MaskChannelParallel(mask_loaded, image_loaded_z):

    def props_of_keys(prop, keys):
        return [prop[k] for k in keys]

    dat = measure.regionprops(mask_loaded, image_loaded_z)
    props = np.array(
        Parallel(n_jobs=1, verbose=1)(delayed(props_of_keys)(
            prop, ['mean_intensity']
        )
            for prop in dat
        )
    ).T
    return props[0]

def MaskIDs(mask):
    """This function will extract the CellIDs and the XY positions for each
    cell based on that cells centroid

    Returns a dictionary object"""

    dat = measure.regionprops(mask)
    n = len(dat)

    # Pre-allocate numpy arrays for all properties we'll calculate.
    labels = np.empty(n, int)
    xcoords = np.empty(n)
    ycoords = np.empty(n)
    area = np.empty(n, int)
    minor_axis_length = np.empty(n)
    major_axis_length = np.empty(n)
    eccentricity = np.empty(n)
    solidity = np.empty(n)
    extent = np.empty(n)
    orientation = np.empty(n)

    for i in range(n):
        labels[i] = dat[i].label
        xcoords[i] = dat[i].centroid[1]
        ycoords[i] = dat[i].centroid[0]
        area[i] = dat[i].area
        major_axis_length[i] = dat[i].major_axis_length
        minor_axis_length[i] = dat[i].minor_axis_length
        eccentricity[i] = dat[i].eccentricity
        solidity[i] = dat[i].solidity
        extent[i] = dat[i].extent
        orientation[i] = dat[i].orientation
        # By clearing the reference to each RegionProperties object, we allow it
        # and its cache to be garbage collected immediately. Otherwise memory
        # usage creeps up needlessly while this function is executing.
        dat[i] = None

    IDs = {
        "CellID": labels,
        "X_centroid": xcoords,
        "Y_centroid": ycoords,
        "Area": area,
        "MajorAxisLength": major_axis_length,
        "MinorAxisLength": minor_axis_length,
        "Eccentricity": eccentricity,
        "Solidity": solidity,
        "Extent": extent,
        "Orientation": orientation,
    }

    return IDs

def MaskIDsParallel(mask):

    def props_of_keys(prop, keys):
        return [prop[k] for k in keys]

    dat = measure.regionprops(mask)
    IDs = OrderedDict({
        "CellID": 'label',
        'centroid': 'centroid',
        "Area": 'area',
        "MajorAxisLength": 'major_axis_length',
        "MinorAxisLength": 'minor_axis_length',
        "Eccentricity": 'eccentricity',
        "Solidity": 'solidity',
        "Extent": 'extent',
        "Orientation": 'orientation',
    })
    props = np.array(
        Parallel(n_jobs=1, verbose=1)(delayed(props_of_keys)(
            prop, [IDs[key] for key in IDs]
        )
            for prop in dat
        )
    ).T
    for idx, key in enumerate(IDs):
        IDs[key] = props[idx]
    IDs['X_centroid'], IDs['Y_centroid'] = np.array(
        [(c[1], c[0]) for c in IDs['centroid']]
    ).T
    IDs['CellID'] = IDs['CellID'].astype(np.int32)
    IDs['Area'] = IDs['Area'].astype(np.int32)
    del IDs['centroid']

    return IDs

def PrepareData(image,z, do_rolling_ball=False, rolling_ball_radius=None):
    """Function for preparing input for maskzstack function. Connecting function
    to use with mc micro ilastik pipeline"""

    image_path = Path(image)

    #Check to see if image tif(f)
    if image_path.suffix == '.tiff' or image_path.suffix == '.tif':
        #Check to see if the image is ome.tif(f)
        if  image.endswith(('.ome.tif','.ome.tiff')):
            #Read the image
            image_loaded_z = skimage.io.imread(image,img_num=z,plugin='tifffile')
            #print('OME TIF(F) found')
        else:
            #Read the image
            image_loaded_z = skimage.io.imread(image,img_num=z,plugin='tifffile')
            #print('TIF(F) found')
            # Remove extra axis
            #image_loaded = image_loaded.reshape((image_loaded.shape[1],image_loaded.shape[3],image_loaded.shape[4]))

    #Check to see if image is hdf5
    elif image_path.suffix == '.h5' or image_path.suffix == '.hdf5':
        #Read the image
        f = h5py.File(image,'r+')
        #Get the dataset name from the h5 file
        dat_name = list(f.keys())[0]
        ###If the hdf5 is exported from ilastik fiji plugin, the dat_name will be 'data'
        #Get the image data
        image_loaded = np.array(f[dat_name])
        #Remove the first axis (ilastik convention)
        image_loaded = image_loaded.reshape((image_loaded.shape[1],image_loaded.shape[2],image_loaded.shape[3]))
        ###If the hdf5 is exported from ilastik fiji plugin, the order will need to be
        ###switched as above --> z_stack = np.swapaxes(z_stack,0,2) --> z_stack = np.swapaxes(z_stack,0,1)

    if do_rolling_ball:
        import pyimagej_rolling_ball as prb
        image_loaded_z = prb.ij_rolling_ball_dask(image_loaded_z, rolling_ball_radius, chunk_size=2**13)

    #Return the objects
    print(z, image_loaded_z.shape)
    return image_loaded_z


def MaskZstack(mask_loaded,image,channel_names_loaded, do_rolling_ball=False, rolling_ball_radius=None):
    """This function will extract the stats for each cell mask through each channel
    in the input image

    mask: Tiff image mask that represents the cells in your image. Must end with the word mask!!

    z_stack: Multichannel z stack image"""

    #Get the CellIDs for this dataset
    IDs = pd.DataFrame(MaskIDsParallel(mask_loaded))
    #Iterate through the z stack to extract intensities
    # list_of_chan = []
    #Get the z channel and the associated channel name from list of channel names
    # for z in range(len(channel_names_loaded)):
    #     #Run the data Prep function
    #     image_loaded_z = PrepareData(image,z)
    #     #Use the above information to mask z stack
    #     list_of_chan.append(MaskChannel(mask_loaded,image_loaded_z))
    #     #Print progress
    #     print("Finished "+str(z))
    list_of_chan = Parallel(n_jobs=1, verbose=1)(
        delayed(MaskChannel)(mask_loaded,PrepareData(image,z, do_rolling_ball=do_rolling_ball, rolling_ball_radius=rolling_ball_radius))
        for z in range(len(channel_names_loaded))
    )
    
    #Convert the channel names list and the list of intensity values to a dictionary and combine with CellIDs and XY
    dat = pd.concat([IDs,pd.DataFrame(dict(zip(channel_names_loaded,list_of_chan)))],axis=1)
    #Get the name of the columns in the dataframe so we can reorder to histoCAT convention
    cols = list(dat.columns.values)
    #Reorder the list (Move xy position to end with spatial information)
    cols.append(cols.pop(cols.index("X_centroid")))
    cols.append(cols.pop(cols.index("Y_centroid")))
    cols.append(cols.pop(cols.index("Area")))
    cols.append(cols.pop(cols.index("MajorAxisLength")))
    cols.append(cols.pop(cols.index("MinorAxisLength")))
    cols.append(cols.pop(cols.index("Eccentricity")))
    cols.append(cols.pop(cols.index("Solidity")))
    cols.append(cols.pop(cols.index("Extent")))
    cols.append(cols.pop(cols.index("Orientation")))
    #Reindex the dataframe with new order
    dat = dat.reindex(columns=cols)
    #Return the dataframe
    return dat


def ExtractSingleCells(mask,image,channel_names,output, do_rolling_ball=False, rolling_ball_radius=None):
    """Function for extracting single cell information from input
    path containing single-cell masks, z_stack path, and channel_names path."""

    #Create pathlib object for output
    output = Path(output)

    #Check if header available
    #sniffer = csv.Sniffer()
    #sniffer.has_header(open(channel_names).readline())
    #If header not available
    #if not sniffer:
        #If header available
        #channel_names_loaded = pd.read_csv(channel_names)
        #channel_names_loaded_list = list(channel_names_loaded.marker_name)
    #else:
        #print("negative")
        #old one column version
        #channel_names_loaded = pd.read_csv(channel_names,header=None)
        #Add a column index for ease
        #channel_names_loaded.columns = ["marker"]
        #channel_names_loaded = list(channel_names_loaded.marker.values)

    #Read csv channel names
    channel_names_loaded = pd.read_csv(channel_names)
    #Check for size of columns
    if channel_names_loaded.shape[1] > 1:
        #Get the marker_name column if more than one column (CyCIF structure)
        channel_names_loaded_list = list(channel_names_loaded.marker_name)
    else:
        #old one column version -- re-read the csv file and add column name
        channel_names_loaded = pd.read_csv(channel_names, header = None)
        #Add a column index for ease and for standardization
        channel_names_loaded.columns = ["marker"]
        channel_names_loaded_list = list(channel_names_loaded.marker)

    #Check for unique marker names -- create new list to store new names
    channel_names_loaded_checked = []
    for idx,val in enumerate(channel_names_loaded_list):
        #Check for unique value
        if channel_names_loaded_list.count(val) > 1:
            #If unique count greater than one, add suffix
            channel_names_loaded_checked.append(val + "_"+ str(channel_names_loaded_list[:idx].count(val) + 1))
        else:
            #Otherwise, leave channel name
            channel_names_loaded_checked.append(val)

    #Clear small memory amount by clearing old channel names
    channel_names_loaded, channel_names_loaded_list = None, None

    print('Number of channels:', len(channel_names_loaded_checked))
    print('Channel names:', ', '.join(channel_names_loaded_checked))

    #Read the mask
    mask_loaded = skimage.io.imread(mask,plugin='tifffile')

    scdata_z = MaskZstack(mask_loaded,image,channel_names_loaded_checked, do_rolling_ball=do_rolling_ball, rolling_ball_radius=rolling_ball_radius)
    #Write the singe cell data to a csv file using the image name

    im_full_name = os.path.basename(image)
    im_name = im_full_name.split('.')[0]
    scdata_z.to_csv(str(Path(os.path.join(str(output),str(im_name+".csv")))),index=False)


def MultiExtractSingleCells(mask,image,channel_names,output, do_rolling_ball=False, rolling_ball_radius=None):
    """Function for iterating over a list of z_stacks and output locations to
    export single-cell data from image masks"""

    print("Extracting single-cell data for "+str(image)+'...')

    #Run the ExtractSingleCells function for this image
    ExtractSingleCells(mask,image,channel_names,output, do_rolling_ball=do_rolling_ball, rolling_ball_radius=rolling_ball_radius)

    #Print update
    im_full_name = os.path.basename(image)
    im_name = im_full_name.split('.')[0]
    print("Finished "+str(im_name))
