# Voxel hollow
A Blender add-on for hollowing out meshes 

## Installing
Download the file `voxel_hollow.py`. Start Blender, go to Edit -> 
Preferences -> Add-ons -> Install and pick the downloaded file. Then enable 
the add-on.

## Use
This will only work on watertight meshes. On the 3D Viewport in object mode, 
select the target object. The UI is in the Sidebar under Voxel hollow.

### Parameters

#### Offset
Offset of the generated surface in relation to original mesh. For negative 
offset values, the generated surface is inside the original mesh, which is
necessary for hollowing out. 

Positive offset values generate a surface outside the original. This can 
be use to create a mold of the target object with a wall thickness given by
the offset.

#### Resolution
The resolution of the VDB grid. Too big a value may lead to the inner wall
intersecting the outer wall. 

#### Join
If checked, the generated surface will be joined with the targed object, 
effectively hollowing it. The code will flip the normals of the generated
surface or the target depending on the sign of the offset.

### Tips
 - Apply scale and modifiers before using.
 - Generate the surface without joining at first to check the parameters.
 - With negative offsets the generated surface will not usually be visible,
   hide the target to inspect it.