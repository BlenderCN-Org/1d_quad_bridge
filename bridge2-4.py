# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#   https://github.com/Korchy/1d_bridge2-4
#
# Version history:
#   0.1.0. (2018.07.21) - start dev


bl_info = {
    'name': 'Bridge2-4',
    'category': 'Mesh',
    'author': 'Nikita Akimov',
    'version': (0, 1, 0),
    'blender': (2, 79, 0),
    'location': 'The 3D_View window - T-panel - the 1D tab',
    'wiki_url': 'https://github.com/Korchy/1d_bridge2-4',
    'tracker_url': 'https://github.com/Korchy/1d_bridge2-4',
    'description': 'Bridge 2-4'
}

import bpy
import bmesh


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
            # count levels with src and dest loops correction
            src_loop, dest_loop, levels = __class__.levels(src_loop, dest_loop)
            # print('src_loop', src_loop, ' len = ', len(src_loop))
            # print('dest_loop', dest_loop, ' len = ', len(dest_loop))
            # print('levels', levels)
            if levels > 0:
                for level in range(levels):
                    # print('current level: ', level)
                    src_loop = __class__.build_level(bm, src_loop, dest_loop, level, levels)
                    # print('next src_loop ', src_loop)
        bm.to_mesh(context.object.data)
        bm.free()
        bpy.ops.object.mode_set(mode='EDIT')

    @staticmethod
    def levels(src_loop, dest_loop):
        # count levels with src and dest loops correction (cutting redundant verts from the end of the lists)
        if src_loop and dest_loop:
            levels = 0
            cor_src_loop = src_loop
            cor_dest_loop = dest_loop
            if len(src_loop) >= 3 and len(dest_loop) >= 5:
                # correct src_loop
                if not BmEx.loops_direction(src_loop, dest_loop):
                    cor_src_loop.reverse()
                if not len(cor_src_loop) % 2:
                    cor_src_loop = cor_src_loop[:-1]
                # count levels
                src_len = len(cor_src_loop) - 1
                dest_len = len(dest_loop) - 1
                while src_len * 2 <= dest_len:
                    levels += 1
                    src_len *= 2
                # correct dest_loop
                cor_dest_loop = dest_loop[:src_len + 1]
            return (cor_src_loop, cor_dest_loop, levels)

    @staticmethod
    def build_level(bm, src_loop, dest_loop, level, levels):
        # returns top line of the builded level (new src_loop for the next level)
        top_line = []
        prev_block = None
        for step in range(int((len(src_loop) - 1) / 2)):
            # print('current step:', step)
            prev_block = __class__.block(src_loop[step * 2:step * 2 + 3], dest_loop[step * 2 ** (levels - level + 1):step * 2 ** (levels - level + 1) + 2 ** (levels - level + 1) + 1], prev_block, level, levels)
            # build block from verts
            # verts to BMVert
            for i, vert in enumerate(prev_block):
                if vert:
                    prev_block[i] = vert if isinstance(vert, bmesh.types.BMVert) else bm.verts.new([vert.x, vert.y, vert.z])
            # BMFaces from BMVerts
            bm.faces.new([prev_block[0], prev_block[3], prev_block[4], prev_block[1]])
            bm.faces.new([prev_block[1], prev_block[4], prev_block[5], prev_block[6]])
            bm.faces.new([prev_block[1], prev_block[6], prev_block[7], prev_block[2]])
            bm.faces.new([prev_block[3], prev_block[8], prev_block[9], prev_block[4]])
            bm.faces.new([prev_block[4], prev_block[9], prev_block[10], prev_block[5]])
            bm.faces.new([prev_block[5], prev_block[10], prev_block[11], prev_block[6]])
            bm.faces.new([prev_block[6], prev_block[11], prev_block[12], prev_block[7]])
            # append top_line
            if not top_line:
                top_line.append(prev_block[8])
            top_line.extend([prev_block[9], prev_block[10], prev_block[11], prev_block[12]])
        return top_line


    @staticmethod
    def block(src_loop, dest_loop, prev_block, level, levels):
        return [__class__.v0(src_loop),
                __class__.v1(src_loop),
                __class__.v2(src_loop),
                __class__.v3(src_loop, dest_loop, prev_block, level, levels),
                __class__.v4(src_loop, dest_loop, level, levels),
                __class__.v5(src_loop, dest_loop, level, levels),
                __class__.v6(src_loop, dest_loop, level, levels),
                __class__.v7(src_loop, dest_loop, level, levels),
                __class__.v8(src_loop, dest_loop, prev_block, level, levels),
                __class__.v9(src_loop, dest_loop, level, levels),
                __class__.v10(src_loop, dest_loop, level, levels),
                __class__.v11(src_loop, dest_loop, level, levels),
                __class__.v12(src_loop, dest_loop, level, levels)
                ]

    @staticmethod
    def level_height(src_loop_vert, dest_loop_vert, level, levels, debug=0):
        # returns height for the current level
        v1 = src_loop_vert.co if isinstance(src_loop_vert, bmesh.types.BMVert) else src_loop_vert
        v2 = dest_loop_vert.co if isinstance(dest_loop_vert, bmesh.types.BMVert) else dest_loop_vert
        length = (v1 - v2).length
        levels = levels - level
        level = 1   # level = 1 every time (because src_loops updates every level)
        # if debug:
        #     print('v5 height')
        #     print('levels ', levels)
        #     print('level ', level)
        #     print('all parts ', 2 ** levels - 1)
        #     print('get parts ', 2 ** (levels - level))
        #     print('persentage, ', (2 ** (levels - level)) / (2 ** levels - 1))
        return length * (2 ** (levels - level)) / (2 ** levels - 1)

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
    def v3(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[7]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels) / 2
            return src_loop[0].co + direction * length

    @staticmethod
    def v4(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[1].co - src_loop[0].co) / 2
        v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 4)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) / 2
        return v1 + direction * length

    @staticmethod
    def v5(src_loop, dest_loop, level, levels):
        v1 = src_loop[1].co
        v2 = dest_loop[int((len(dest_loop) - 1) / 2)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels, 1) * 3 / 4
        return src_loop[1].co + direction * length

    @staticmethod
    def v6(src_loop, dest_loop, level, levels):
        v1 = src_loop[1].co + (src_loop[2].co - src_loop[1].co) / 2
        v2 = dest_loop[int((len(dest_loop) - 1) * 3 / 4)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) / 2
        return v1 + direction * length

    @staticmethod
    def v7(src_loop, dest_loop, level, levels):
        v1 = src_loop[2].co
        v2 = dest_loop[len(dest_loop) - 1].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) / 2
        return src_loop[2].co + direction * length

    @staticmethod
    def v8(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[12]
        elif level == levels - 1:
            return dest_loop[0]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return src_loop[0].co + direction * length

    @staticmethod
    def v9(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[1]
        else:
            v1 = src_loop[0].co + (src_loop[1].co - src_loop[0].co) / 2
            v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 4)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v10(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[2]
        else:
            v1 = src_loop[1].co
            v2 = dest_loop[int((len(dest_loop) - 1) / 2)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return src_loop[1].co + direction * length

    @staticmethod
    def v11(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[3]
        else:
            v1 = src_loop[1].co + (src_loop[2].co - src_loop[1].co) / 2
            v2 = dest_loop[int((len(dest_loop) - 1) * 3 / 4)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v12(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[4]
        else:
            v1 = src_loop[2].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return src_loop[2].co + direction * length


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
