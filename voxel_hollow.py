# SPDX-FileCopyrightText: 2024 Ubiratan Freitas

# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Voxel hollow",
    "description": "Hollow out a manifold mesh using OpenVDB.",
    "author": "Ubiratan Freitas",
    "version": (1, 1, 0),
    "blender": (3, 5, 0),
    "location": "3D Viewport > Sidebar > Hollow",
    "category": "Object",
    }


import bpy
import pyopenvdb as vdb
import numpy as np
import math

from bpy.props import BoolProperty, FloatProperty, PointerProperty, EnumProperty
from bpy.types import Operator, Panel, PropertyGroup


# Properties
class HollowSettings(PropertyGroup):

    offset_direction: EnumProperty(
        items=[
            ('INSIDE', "Inside", "Offset surface inside of object"),
            ('OUTSIDE', "Outside", "Offset surface outside of object"),
            ],
        name="Offset Direction",
        description="Where the offset surface is created relative to the object",
        default='INSIDE',
        )
    offset: FloatProperty(
        name="Offset",
        description="Surface offset in relation to original mesh",
        default=1.0,
        subtype='DISTANCE',
        min=0.0,
        step=1,
        )
    voxel_size: FloatProperty(
        name="Voxel size",
        description="Size of the voxel used for volume evaluation. Lower values preserve finer details",
        default=1.0,
        min=0.0001,
        step=1,
        subtype='DISTANCE',
        )
    make_hollow_duplicate: BoolProperty(
        name="Hollow Duplicate",
        description="Create hollowed out copy of the object",
        )

# Test functions for polling
def is_mode_object(context):
    return context.mode == 'OBJECT'

def is_active_object_mesh(context):
    active_object = context.active_object
    return active_object is not None and active_object.type == 'MESH' and active_object.select_get() 

class OBJECT_PT_hollow(Panel):
    bl_space_type = "VIEW_3D"
    #bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Voxel Hollow"
    bl_category = "Voxel hollow"
    @classmethod
    def poll(cls, context):
        return is_mode_object(context) and is_active_object_mesh(context)

    def draw(self, context):
        hollow_settings = context.scene.hollow
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(hollow_settings, "offset_direction", expand=True)
        layout.prop(hollow_settings, "offset")
        layout.prop(hollow_settings, "voxel_size")
        layout.prop(hollow_settings, "make_hollow_duplicate")
        layout.operator("mesh.voxel_hollow")

class MESH_OT_voxel_hollow(Operator):
    bl_idname = "mesh.voxel_hollow"
    bl_label = "Voxel Hollow"
    bl_description = "Create offset surface"
    bl_options = {'REGISTER', 'UNDO'}

    offset_direction: EnumProperty(
        items=[
            ('INSIDE', "Inside", "Offset surface inside of object"),
            ('OUTSIDE', "Outside", "Offset surface outside of object"),
            ],
        name="Offset Direction",
        description="Where the offset surface is created relative to the object",
        default='INSIDE',
        )
    offset: FloatProperty(
        name="Offset",
        description="Surface offset in relation to original mesh",
        default=1.0,
        subtype='DISTANCE',
        min=0.0,
        step=1,
        )
    voxel_size: FloatProperty(
        name="Voxel size",
        description="Size of the voxel used for volume evaluation. Lower values preserve finer details",
        default=1.0,
        min=0.0001,
        step=1,
        subtype='DISTANCE',
        )
    make_hollow_duplicate: BoolProperty(
        name="Hollow Duplicate",
        description="Create hollowed out copy of the object",
        )

    @classmethod
    def poll(cls, context):
        return is_mode_object(context) and is_active_object_mesh(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.separator()

        layout.prop(self, "offset_direction", expand=True)
        layout.prop(self, "offset")
        layout.prop(self, "voxel_size")
        layout.prop(self, "make_hollow_duplicate")

    def execute(self, context):

        if not self.offset:
            return {'FINISHED'}

        # Get target mesh with modifiers
        obj = context.active_object
        depsgraph = context.evaluated_depsgraph_get()
        mesh_target = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))

        # Apply scale, but avoid translating the mesh
        mat = obj.matrix_world.copy()
        mat.translation = 0, 0, 0
        mesh_target.transform(mat)

        # Read mesh to numpy arrays
        nverts = len(mesh_target.vertices)
        ntris = len(mesh_target.loop_triangles)
        verts = np.zeros(3 * nverts, dtype=np.float32)
        tris = np.zeros(3 * ntris, dtype=np.int32)
        mesh_target.vertices.foreach_get("co", verts)
        verts.shape = (-1, 3)
        mesh_target.loop_triangles.foreach_get("vertices", tris)
        tris.shape = (-1, 3)

        # Generate VDB levelset
        half_width = max(3.0, math.ceil(abs(self.offset) / self.voxel_size) + 2.0) # half_width has to envelop offset
        trans = vdb.Transform()
        trans.scale(self.voxel_size)
        levelset = vdb.FloatGrid.createLevelSetFromPolygons(verts, triangles=tris, transform=trans, halfWidth=half_width)

        # Generate offset surface
        if self.offset_direction == 'INSIDE':
            newverts, newquads = levelset.convertToQuads(-self.offset)
            if newquads.size == 0:
                self.report({'ERROR'}, "Make sure target mesh has closed surface and offset value is less than half of target thickness")
                return {'FINISHED'}
        else:
            newverts, newquads = levelset.convertToQuads(self.offset)

        polys = list(newquads)

        # Instantiate new object in Blender
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        mesh_offset = bpy.data.meshes.new(mesh_target.name + " offset")
        mesh_offset.from_pydata(newverts, [], polys)

        # For some reason OpenVDB has inverted normals
        mesh_offset.flip_normals()
        obj_offset = bpy.data.objects.new(obj.name + " offset", mesh_offset)
        obj_offset.matrix_world.translation = obj.matrix_world.translation
        bpy.context.collection.objects.link(obj_offset)
        obj_offset.select_set(True)
        context.view_layer.objects.active = obj_offset

        if self.make_hollow_duplicate:
            obj_hollow = bpy.data.objects.new(obj.name + " hollow", mesh_target)
            bpy.context.collection.objects.link(obj_hollow)
            obj_hollow.matrix_world.translation = obj.matrix_world.translation
            obj_hollow.select_set(True)
            if self.offset_direction == 'INSIDE':
                mesh_offset.flip_normals()
            else:
                mesh_target.flip_normals()
            context.view_layer.objects.active = obj_hollow
            bpy.ops.object.join()
        else:
            bpy.data.meshes.remove(mesh_target)

        hollow_settings = context.scene.hollow
        hollow_settings.offset_direction = self.offset_direction
        hollow_settings.offset = self.offset
        hollow_settings.voxel_size = self.voxel_size
        hollow_settings.make_hollow_duplicate = self.make_hollow_duplicate

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
        hollow_settings = context.scene.hollow
        self.offset_direction = hollow_settings.offset_direction
        self.offset = hollow_settings.offset
        self.voxel_size = hollow_settings.voxel_size
        self.make_hollow_duplicate = hollow_settings.make_hollow_duplicate
        return self.execute(context)

classes = (
        HollowSettings,
        OBJECT_PT_hollow,
        MESH_OT_voxel_hollow,
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
