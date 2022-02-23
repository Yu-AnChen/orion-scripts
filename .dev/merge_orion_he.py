import skimage.io
import pathlib
import numpy as np
import skimage.segmentation
from subprocess import call
from joblib import Parallel, delayed

def main2(img_path, he_path, out_name, mask_path=None, prob_path=None, img_channels=[], out_dir='.'):
    img_path = pathlib.Path(img_path)
    he_path = pathlib.Path(he_path)
    out_dir = pathlib.Path(out_dir)

    def read_and_write(p, c, count=None):

        print('reading', p.name)

        img = skimage.io.imread(str(p), key=c)
        if img.dtype == np.uint8:
            img = img.astype(np.uint16)
            img *= 160
        if count is None:
            count = c
        img_out_path = out_dir / '{:02}-{}-ch_{:02}.tif'.format(count, p.stem, c)
        skimage.io.imsave(
            str(img_out_path),
            img,
            metadata=None, bigtiff=True, check_contrast=False
        )
        img = None
        return
    
    # Parallel(n_jobs=5, verbose=1)(delayed(read_and_write)(
    #     img_path,
    #     channel
    # ) for channel in img_channels)

    # print(he_path)
    # Parallel(n_jobs=3)(delayed(read_and_write)(
    #     he_path,
    #     channel,
    #     count
    # ) for channel, count in zip([0, 1, 2], [20, 21, 22]))

    # if mask_path is not None:
    #     mask_path = pathlib.Path(mask_path)
    #     read_and_write(mask_path, 1, 23)

    if prob_path is not None:
        prob_path = pathlib.Path(prob_path)
        read_and_write(prob_path, 1, 24)

    single_channel_files = sorted(out_dir.glob('*.tif'))
    single_channel_files = ' '.join([str(s) for s in single_channel_files])
    call('python pyramid_assemble.py {} {} --pixel-size {}'.format(
        single_channel_files, out_dir / out_name, 0.325
    )) 



import csv

with open(r'Z:\RareCyte-S3\YC-analysis\Lung_066-082\scripts-processing\merge_list.csv') as file_config_csv:
    csv_reader = csv.DictReader(file_config_csv)
    file_config = [dict(row) for row in csv_reader]

file_config = file_config[:1]

ome_tiffs = [r['path'] for r in file_config]
slide_names = [r['name'] for r in file_config]
he_names = [r['he_path'] for r in file_config]

group_dir = pathlib.Path(r'Z:\RareCyte-S3\YC-analysis\Lung_066-082')
he_dir = pathlib.Path(r'Z:\RareCyte-S3\Registered_HE')
ome_tiff_dir = pathlib.Path(r'Z:\RareCyte-S3')

ome_tiff_paths = [
    ome_tiff_dir / o_t
    for o_t in ome_tiffs
]

mask_paths = [
    group_dir / 'segmentation_mask_qc' / '{}-cellRingMask-qc.ome.tif'.format(s_n)
    for s_n in slide_names
]

he_paths = [
    he_dir / h_n
    for h_n in he_names
]

prob_paths = [
    sorted(group_dir.glob('*/unmicst2/{}_Probabilities_*.tif'.format(s_n)))[0]
    for s_n in slide_names
]

out_dirs = [
    pathlib.Path(r'D:\yc296\RC') / s_n
    for s_n in slide_names
]    


for i, h, s, m, p, d in zip(
    ome_tiff_paths,
    he_paths,
    slide_names,
    mask_paths,
    prob_paths,
    out_dirs
):
    print('Processing', s)
    # if d.exists():
    #     print('    Already exists')
    #     continue
    
    d.mkdir(exist_ok=True, parents=True)

    main2(
        i,
        h,
        '{}-orion-he-cellRingMask.ome.tif'.format(s),
        mask_path=m,
        prob_path=p,
        img_channels=list(range(20)),
        out_dir=d
    )

    print()

# for m, o, s, d in zip(
#     mask_paths[:],
#     ome_tiffs[:],
#     slide_names[:],
#     out_dirs[:]
# ):
#     print('Processing', s.name)
#     if d.exists():
#         print('    Already exists')
#         continue
    
#     d.mkdir(exist_ok=True, parents=True)
#     main(m, r'Z:\RareCyte-S3' / o, '{}-orion-qc.ome.tif'.format(s), img_channel=2, out_dir=d)
#     print()