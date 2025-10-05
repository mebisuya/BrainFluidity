import napari
import numpy as np
from magicgui import magicgui
from qtpy.QtWidgets import QFileDialog
from skimage import filters, io
import csv
import os

viewer = napari.Viewer()
image_name = None 

# ---------- Load image ----------
@magicgui(call_button='Load Image')
def load_image():
    global image_name
    image_name = None 
    path, _ = QFileDialog.getOpenFileName(
        caption="Choose image", 
        filter="TIFF (*.tif *.tiff);;All files (*)"
    )
    if not path:
        return
    image_name = os.path.splitext(os.path.basename(path))[0]
    image = io.imread(path)
    if image.max() > 255:
        image = (image / image.max() * 255).astype(np.uint8)
    viewer.layers.clear()
    viewer.add_image(image, name=image_name, colormap='gray')
    viewer.window.status = f"Loaded image: {os.path.basename(path)}"

# ---------- Segment image with Otsu ----------
@magicgui(call_button='Otsu Segment', threshold_offset={"label": "Otsu offset", "min": 5, "max": 20, "step": 1})
def segment_image(threshold_offset: int = 10):
    if image_name not in viewer.layers:
        viewer.window.status = "No image layer found"
        return

    image_layer = viewer.layers[image_name]
    image = image_layer.data

    if image.ndim == 2:
        threshold = filters.threshold_otsu(image) - threshold_offset
        mask = (image > threshold).astype(np.uint8)
    else:
        mask = np.zeros_like(image, dtype=np.uint8)
        for z in range(image.shape[0]):
            slice_ = image[z]
            if np.any(slice_):
                t = filters.threshold_otsu(slice_) - threshold_offset
                mask[z] = (slice_ > t).astype(np.uint8)

    if 'segmentation' in viewer.layers:
        viewer.layers['segmentation'].data = mask
    else:
        viewer.add_labels(mask, name='segmentation')

    viewer.window.status = f"Otsu segmentation complete (offset: {threshold_offset})"

# ---------- Export mask as .npy ----------
@magicgui(call_button='Export Masks')
def export_masks(segmentation: 'napari.layers.Labels'):
    path, _ = QFileDialog.getSaveFileName(
        caption="Save segmentation as NPY", 
        filter="NumPy Files (*.npy)"
    )
    if not path:
        return
    np.save(path, segmentation.data)
    viewer.window.status = f"Mask saved to {os.path.basename(path)}"

# ---------- Import .npy mask ----------
@magicgui(call_button='Import Masks')
def import_masks():
    path, _ = QFileDialog.getOpenFileName(
        caption="Import segmentation NPY", 
        filter="NumPy Files (*.npy)"
    )
    if not path:
        return
    mask = np.load(path)
    viewer.add_labels(mask, name='segmentation')
    viewer.window.status = f"Imported mask from {os.path.basename(path)}"

# ---------- Export pixel stats ----------
@magicgui(call_button='Export Pixel Stats')
def export_pixel_stats(segmentation: 'napari.layers.Labels'):
    mask = segmentation.data
    is_3d = mask.ndim == 3
    
    rows = []
    shape = viewer.layers[image_name].data.shape
    total_pixels = shape[1] *shape[2]
    if is_3d:
        for z in range(mask.shape[0]):
            count = np.sum(mask[z] == 1)
           
            rows.append((z, count))
    else:
        count = np.sum(mask == 1)
        rows.append((0, count))

    csv_path, _ = QFileDialog.getSaveFileName(
        caption="Save pixel stats as CSV", 
        filter="CSV Files (*.csv)"
    )
    if not csv_path:
        return

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Slice Index', 'Pixel Count', 'Total Pixels'])
        for slice_idx, count in rows:
            writer.writerow([slice_idx, count, total_pixels])
    
    viewer.window.status = f"Exported pixel stats to {os.path.basename(csv_path)}"

# ---------- Add buttons to Napari ----------
viewer.window.add_dock_widget(load_image, area='right')
viewer.window.add_dock_widget(segment_image, area='right')
viewer.window.add_dock_widget(export_masks, area='right')
viewer.window.add_dock_widget(import_masks, area='right')
viewer.window.add_dock_widget(export_pixel_stats, area='right')

napari.run()
