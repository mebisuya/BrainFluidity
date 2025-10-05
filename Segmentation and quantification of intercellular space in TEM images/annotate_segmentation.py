import numpy as np
import napari
from napari.utils.notifications import show_info
from napari.layers import Labels, Image
from magicgui import magicgui, widgets
import pathlib
import os
import pandas as pd

from skimage import measure



color_dict = {1:'transparent'}
for i in range(2, 256):
    color_dict[i] = 'red'

# total area
# space ratio
# individual space area
# cnt
# converter


@magicgui(
        excel_dir = {"mode": "d"},
        call_button="export",)
def export_excel(
    excel_dir=pathlib.Path('/path/to/folder/'),
):
    image_layers = viewer.layers 
    if len(image_layers) == 0:
        show_info("please open an image first")
    elif len(image_layers) ==1 or len(image_layers) > 2:
        show_info("please check if label or image is loaded correctly")
    else:
        
        if not os.path.exists(excel_dir):
            show_info("select the directory first")
        else:
          
            fn = None
            label_data = None
            for i in image_layers:
                if i.name  == 'space':
                    label_data = i.data
                else:
                    fn = i.name
                    image_data = i.data
            if label_data is not None and fn is not None:
                export_file_path = os.path.join(excel_dir, fn+"_labels.csv")
                image_pixel_num = np.count_nonzero(image_data != 2**15)
                if os.path.exists(export_file_path):
                    show_info("saving updated file")
                else:
                    label_data[label_data == 1] = 0
                    show_info(f"exporting statistics to {export_file_path}")
                new_label_data = measure.label(label_data)
                viewer.layers.remove("space")
                np.save(os.path.join(excel_dir, fn+".npy"), new_label_data)
                viewer.add_labels(new_label_data, opacity= 0.5, name='space')
                
                out_dict = measure.regionprops_table(
                    new_label_data, 
                    properties=('label', 'area'))
                
                df = pd.DataFrame(out_dict)
                df.loc[len(df)] = ['total', image_pixel_num]
                
                df.to_csv(export_file_path)
                
            else:
                show_info("please check if label or image is loaded")

    

@magicgui(  
        labels_path = {"mode": "d"},  
        call_button="upload", 
        )
def load_image_label(
    labels_path=pathlib.Path('/path/to/folder/'),
) -> napari.layers.Labels:
    image_layers = viewer.layers 
    if len(image_layers) == 0:
        show_info("please open an image first")
    elif len(image_layers) == 1:
        current_layer = image_layers[0]
        fn = current_layer.name+".npy"
        if not os.path.exists(labels_path):
            show_info("select the directory first")
        elif fn in os.listdir(labels_path):
            if current_layer.name+"_labels.csv" in os.listdir(labels_path):
                label_im =  np.load(os.path.join(labels_path,fn))
                return napari.layers.Labels(label_im, opacity= 0.5, name='space')
            else:
                label_im =  np.load(os.path.join(labels_path,fn))
                return napari.layers.Labels(label_im, colormap=color_dict, opacity=0.5, name='space')
        else:
            show_info("no labels for the current image")
    else:
        show_info("please make sure only 1 layer is opened")

class LoadExport(widgets.Container):
    def __init__(self, widget_list = [load_image_label, export_excel]):
        super().__init__(widgets = widget_list, labels = False)

# viewer = napari.current_viewer()
viewer = napari.Viewer()
viewer.window.add_dock_widget(LoadExport())

napari.run()