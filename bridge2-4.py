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
import bmesh
from mathutils import Vector
import math


class Bridge24:
    @staticmethod
    def make_bridge(context):
        bpy.ops.object.mode_set(mode='OBJECT')
        bm = bmesh.new()
        bm.from_mesh(context.object.data)

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        loops = BmEx.get_verts_loops_from_selection(bm)
        if len(loops) == 2:
            src_loop = loops[0] if len(loops[0]) < len(loops[1]) else loops[1]
            dest_loop = loops[0] if src_loop == loops[1] else loops[1]
            steps = __class__.steps(src_loop, dest_loop)
            if len(src_loop) >= 3 and steps > 0:
                if not BmEx.loops_direction(src_loop, dest_loop):
                    src_loop.reverse()
                print('total steps:', steps)
                for step in range(steps):
                    print('current step: ', step)
                    __class__.build_step(src_loop, dest_loop, final=(step + 1 == steps))




        bm.free()
        bpy.ops.object.mode_set(mode='EDIT')

    @staticmethod
    def steps(loop1, loop2):
        if loop1 and loop2:
            return math.floor((len(loop2) - 1) / ((len(loop1) - 1) * 2))

    @staticmethod
    def build_step(src_loop, dest_loop, final=False):
        prev_block = None
        for i in range(int((len(src_loop) - 1) / 2)):
            print(i)
            prev_block = __class__.block(src_loop[i * 2:], dest_loop[i * 4:], prev_block, final)
            print(prev_block)


    @staticmethod
    def block(src_loop, dest_loop, prev_block, final_step=False):
        return [__class__.v0(src_loop),
                __class__.v1(src_loop),
                __class__.v2(src_loop),
                __class__.v3(src_loop),
                __class__.v4(src_loop),
                __class__.v5(src_loop),
                __class__.v6(src_loop),
                __class__.v7(src_loop),
                __class__.v8(src_loop),
                __class__.v9(src_loop),
                __class__.v10(src_loop),
                __class__.v11(src_loop),
                __class__.v12(src_loop)]

    @staticmethod
    def v0(src_loop):
        return src_loop[0]

    @staticmethod
    def v1(src_loop):
        return src_loop[1]

    @staticmethod
    def v2(src_loop):
        return src_loop[2]

    @staticmethod
    def v3(src_loop):
        return src_loop[2]

    @staticmethod
    def v4(src_loop):
        return src_loop[2]

    @staticmethod
    def v5(src_loop):
        return src_loop[2]

    @staticmethod
    def v6(src_loop):
        return src_loop[2]

    @staticmethod
    def v7(src_loop):
        return src_loop[2]

    @staticmethod
    def v8(src_loop):
        return src_loop[2]

    @staticmethod
    def v9(src_loop):
        return src_loop[2]

    @staticmethod
    def v10(src_loop):
        return src_loop[2]

    @staticmethod
    def v11(src_loop):
        return src_loop[2]

    @staticmethod
    def v12(src_loop):
        return src_loop[2]



class BmEx:
    @staticmethod
    def get_verts_loops_from_selection(bm):
        # get the lists of the arranged vertex loops from selection
        loops = []
        extreme_verts = [vert for vert in bm.verts if vert.select and __class__.vert_is_extreme_in_selection(vert)]
        for vert in extreme_verts:
            loop = [vert]
            while vert:
                next_edge = [edge for edge in vert.link_edges if edge.select and (edge.verts[0] not in loop or edge.verts[1] not in loop)]
                if next_edge:
                    vert = next_edge[0].verts[0] if next_edge[0].verts[0] not in loop else next_edge[0].verts[1]
                    loop.append(vert)
                    if vert in extreme_verts:
                        extreme_verts.remove(vert)
                else:
                    break
            loops.append(loop)
        return loops

    @staticmethod
    def vert_is_extreme_in_selection(vert):
        vert_edges = [edge for edge in vert.link_edges if edge.select]
        return True if len(vert_edges) == 1 else False

    @staticmethod
    def loops_direction(loop1, loop2):
        # loop1, loop2 - vertex lists
        if loop1 and loop2:
            v1 = loop1[0].co - loop1[-1].co
            v2 = loop2[0].co - loop2[-1].co
            v1.normalize()
            v2.normalize()
            if v1.dot(v2) > 0:
                return True
            else:
                return False


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
        Bridge24.make_bridge(context)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(Bridge24Op)
    bpy.utils.register_class(Bridge24Panel)


def unregister():
    bpy.utils.unregister_class(Bridge24Panel)
    bpy.utils.unregister_class(Bridge24Op)


if __name__ == '__main__':
    register()
