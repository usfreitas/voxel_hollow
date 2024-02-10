# SPDX-FileCopyrightText: 2024 Ubiratan Freitas

# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Voxel hollow",
    "description": "Hollow out a manifold mesh using VDB.",
    "author": "Ubiratan Freitas",
    "version": (1, 0, 0),
    "blender": (3, 5, 0),
    "location": "3D Viewport > Sidebar > Hollow",
    "category": "Object",
    }


import bpy
import pyopenvdb as vdb
import numpy as np
import math

from bpy.props import BoolProperty, FloatProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup


# Properties
class HollowSettings(PropertyGroup):

    offset : FloatProperty(
        name = "Offset",
        description = "Surface offset in relation to original mesh. Negative -> inwards",
        default = -5.0,
        subtype = 'DISTANCE',
        )

    resolution : FloatProperty(
        name = "Resolution",
        description = "Resolution of the VDB voxel grid",
        default = 5.0,
        min = 0.01,
        subtype = 'DISTANCE',
        )

    join : BoolProperty(
        name = "Join",
        description = "Join the generated offset mesh to the original object, effectively hollowing it",
        default = False
        )

# Test functions for polling
def is_mode_object(context):
    return context.mode == 'OBJECT'

def is_active_object_mesh(context):
    return context.active_object is not None and context.active_object.type == 'MESH'

class OBJECT_PT_hollow(Panel):
    bl_space_type = "VIEW_3D"
    #bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Hollow"
    bl_category = "Voxel hollow"
    @classmethod
    def poll(cls, context):
        return is_mode_object(context) and is_active_object_mesh(context)

    def draw(self, context):
        hollow_settings = context.scene.hollow
        layout = self.layout
        layout.label(text="Voxel Hollow")
        row = layout.row(align=True)
        row.prop(hollow_settings, "offset")
        row = layout.row(align=True)
        row.prop(hollow_settings, "resolution")
        row = layout.row(align=True)
        row.prop(hollow_settings, "join")
        layout.operator("hollow.create")

class Hollow_OT_create(Operator):
    bl_idname = "hollow.create"
    bl_label = "Create offset surface"
    bl_description = "Create offset surface"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_mode_object(context) and is_active_object_mesh(context)

    def execute(self, context):
        settings = context.scene.hollow
        offset = settings.offset
        resolution = settings.resolution
        join = settings.join

        # Target object
        obj = context.active_object
        m = obj.data # mesh

        # Read mesh to numpy arrays
        nverts = len(m.vertices)
        ntris = len(m.loop_triangles)
        verts = np.zeros(3*nverts, dtype=np.float32)
        tris = np.zeros(3*ntris, dtype=np.int32)
        m.vertices.foreach_get('co', verts)
        verts.shape = (-1, 3)
        m.loop_triangles.foreach_get('vertices', tris)
        tris.shape = (-1, 3)

        # Generate VDB levelset
        half_width = max(3.0, math.ceil(abs(offset)/resolution) + 2.0) # half_width has to envelop offset
        trans = vdb.Transform()
        trans.scale(resolution)
        levelset = vdb.FloatGrid.createLevelSetFromPolygons(verts, triangles=tris, transform=trans, halfWidth=half_width)
        
        # Generate offset surface
        newverts, newquads = levelset.convertToQuads(offset)
        polys = [x for x in newquads]

        # Instantiate new object in Blender
        mesh = bpy.data.meshes.new(m.name + ' offset')
        mesh.from_pydata(newverts, [], polys)
        newobj = bpy.data.objects.new(obj.name + ' offset', mesh)
        newobj.matrix_world = obj.matrix_world.copy()
        bpy.context.collection.objects.link(newobj)

        if not join:
            # for some reason OpenVDB has inverted normals
            mesh.flip_normals()
        else:
            if offset < 0.0:
                # offset surface already has normals as they should, see above
                pass
            else:
                # offset surface is outside, correct normals, see above
                mesh.flip_normals()
                # original surface is inside, flip its normals
                m.flip_normals()
            bpy.ops.object.select_all(action='DESELECT')
            newobj.select_set(True)
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.join()

        return {'FINISHED'}

classes = (
        HollowSettings,
        OBJECT_PT_hollow,
        Hollow_OT_create,
        )
# Register
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hollow = PointerProperty(type=HollowSettings)


# Unregister
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.hollow


if __name__ == "__main__":
    register()
