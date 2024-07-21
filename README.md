# Voxel hollow
A Blender add-on for hollowing out meshes 

## Installing
### Blender 4.2 
This tool is now integrated in the `3D Print Toolbx` add-on, which is 
available as an [extension](https://extensions.blender.org/add-ons/print3d-toolbox/)
and can be downloaded/installed directly from Blender itself.

If you have the 4.2 (or a newer) Blender, don´t bother with `voxel_hollow`,
just install the `3D Print Toolbox`. It has the same functionality, plus
other useful stuff.

### Older Blender versions (3.6 up to 4.1)

Download the file `voxel_hollow.py`. Start Blender, go to Edit -> 
Preferences -> Add-ons -> Install and pick the downloaded file. Then enable 
the add-on.

## Use
On the 3D Viewport in object mode, select the target object. The UI is in the
Sidebar under Voxel hollow.

### Parameters

#### Offset Direction
Where the offset surface is created relative to the object.
 - **INSIDE**: Offset surface inside of object. Use it to hollow out the object.
 - **OUTSIDE**: Offset surface outside of object. This can  be use to create 
   a mold of the target object.

#### Offset
Offset of the generated surface in relation to original mesh. 

#### Voxel Size
The size of the voxel in the VDB grid. Lower values preserve finer details
in the offset surface. Too big a value may lead to the inner wall intersecting
the outer wall. 

#### Hollow Duplicate
Create hollowed out copy of the object. A copy of the original mesh, with
modifiers and scale applied is joined with the generated offset surface.

### Tips
 - For internal offsets, the target mesh needs to be closed, but not 
   necessarily manifold. External offsets should work with any mesh.
 - Outside offset surfaces can be an alternative to the solidify modifier.
