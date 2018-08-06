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
                    __class__.build_step(bm, src_loop, dest_loop, step, steps)



        bm.to_mesh(context.object.data)
        bm.free()
        bpy.ops.object.mode_set(mode='EDIT')

    @staticmethod
    def steps(loop1, loop2):
        if loop1 and loop2:
            return math.floor((len(loop2) - 1) / ((len(loop1) - 1) * 2))

    @staticmethod
    def build_step(bm, src_loop, dest_loop, current_step, steps):
        prev_block = None
        for i in range(int((len(src_loop) - 1) / 2)):
            print(i)
            prev_block = __class__.block(src_loop[i * 2:], dest_loop[i * 4:], prev_block, current_step, steps)
            print('block, ', prev_block)
            # build block from verts
            # verts to BMVert
            bm_verts = []
            for vert in prev_block:
                if vert:
                    bm_vert = vert if isinstance(vert, bmesh.types.BMVert) else bm.verts.new([vert.x, vert.y, vert.z])
                    bm_verts.append(bm_vert)
            # BMFaces from BMVerts
            bm.faces.new([bm_verts[0], bm_verts[3], bm_verts[4], bm_verts[1]])
            bm.faces.new([bm_verts[1], bm_verts[4], bm_verts[5], bm_verts[6]])
            bm.faces.new([bm_verts[1], bm_verts[6], bm_verts[7], bm_verts[2]])


    @staticmethod
    def block(src_loop, dest_loop, prev_block, current_step, steps):
        return [__class__.v0(src_loop),
                __class__.v1(src_loop),
                __class__.v2(src_loop),
                __class__.v3(src_loop, dest_loop, prev_block, current_step),
                __class__.v4(src_loop, dest_loop, current_step, steps),
                __class__.v5(src_loop, dest_loop, current_step, steps),
                __class__.v6(src_loop, dest_loop, current_step, steps),
                __class__.v7(src_loop, dest_loop, current_step, steps),
                __class__.v8(src_loop),
                __class__.v9(src_loop),
                __class__.v10(src_loop),
                __class__.v11(src_loop),
                __class__.v12(src_loop)]

    @staticmethod
    def block_height(src_loop_vert, dest_loop_vert, current_step):
        v1 = src_loop_vert.co if isinstance(src_loop_vert, bmesh.types.BMVert) else src_loop_vert
        v2 = dest_loop_vert.co if isinstance(dest_loop_vert, bmesh.types.BMVert) else dest_loop_vert
        return (v1 - v2).length / (2 ** (current_step + 1))

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
    def v3(src_loop, dest_loop, prev_block, current_step):
        if prev_block:
            return prev_block[7]
        else:
            direction = dest_loop[0].co - src_loop[0].co
            length = __class__.block_height(src_loop[0], dest_loop[0], current_step) / 2
            return src_loop[0].co + direction * length

    @staticmethod
    def v4(src_loop, dest_loop, current_step, steps):
        v1 = src_loop[0].co + (src_loop[1].co - src_loop[0].co) / 2
        v2 = dest_loop[int((2 ** (steps + 1)) / 4)].co
        direction = v2 - v1
        length = __class__.block_height(v1, v2, current_step) / 2
        return v1 + direction * length

    @staticmethod
    def v5(src_loop, dest_loop, current_step, steps):
        v1 = src_loop[1].co
        v2 = dest_loop[int((2 ** (steps + 1)) / 2)].co
        direction = v2 - v1
        length = __class__.block_height(v1, v2, current_step) * 3 / 4
        return src_loop[1].co + direction * length

    @staticmethod
    def v6(src_loop, dest_loop, current_step, steps):
        v1 = src_loop[1].co + (src_loop[2].co - src_loop[1].co) / 2
        v2 = dest_loop[int((2 ** (steps + 1)) * 3 / 4)].co
        direction = v2 - v1
        length = __class__.block_height(v1, v2, current_step) / 2
        return v1 + direction * length

    @staticmethod
    def v7(src_loop, dest_loop, current_step, steps):
        v1 = src_loop[2].co
        v2 = dest_loop[2 ** (steps + 1)].co
        direction = v2 - v1
        length = __class__.block_height(src_loop[0], dest_loop[0], current_step) / 2
        return src_loop[2].co + direction * length

    @staticmethod
    def v8(src_loop):
        return None

    @staticmethod
    def v9(src_loop):
        return None

    @staticmethod
    def v10(src_loop):
        return None

    @staticmethod
    def v11(src_loop):
        return None

    @staticmethod
    def v12(src_loop):
        return None



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
