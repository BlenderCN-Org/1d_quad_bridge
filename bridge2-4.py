# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#   https://github.com/Korchy/1d_bridge2-4
#
# Version history:
#   0.0. (2018.07.21) - start dev


bl_info = {
    'name': 'Bridge2-4',
    'category': 'Mesh',
    'author': 'Nikita Akimov',
    'version': (0, 0, 0),
    'blender': (2, 79, 0),
    'location': 'The 3D_View window - T-panel - the 1D tab',
    'wiki_url': 'https://github.com/Korchy/1d_bridge2-4',
    'tracker_url': 'https://github.com/Korchy/1d_bridge2-4',
    'description': 'Bridge 2-4'
}

import bpy


class Bridge24:
    pass


class Bridge24Panel(bpy.types.Panel):
    bl_idname = 'bridge24.panel'
    bl_label = 'Bridge24'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = '1D'

    def draw(self, context):
        self.layout.operator('bridge24.start', icon='NONE', text='Make Bridge 2-4')


class Bridge24Op(bpy.types.Operator):
    bl_idname = 'bridge24.start'
    bl_label = 'Make Bridge 2-4'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}


def register():
    bpy.utils.register_class(Bridge24Op)
    bpy.utils.register_class(Bridge24Panel)


def unregister():
    bpy.utils.unregister_class(Bridge24Panel)
    bpy.utils.unregister_class(Bridge24Op)


if __name__ == '__main__':
    register()
