# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#   https://github.com/Korchy/1d_quad_bridge
#
# Version history:
#   0.1.0. (2018.07.21) - start dev
#   0.2.0. (2018.08.18) - added 3 more bridges types (2-4, 2-2, 1-3)
#   0.2.1. (2018.08.31) - added 3-7 bridges
#   0.3.0. (2018.09.04) - improve - add filing closed areas (two types: 1) to center from two sides 2) to dest loop with its recreation)

import bpy
import bmesh
import bpy.utils.previews
import os
from inspect import getsourcefile
from abc import ABC, abstractmethod


class QuadBridge(ABC):

    block_src_verts = None
    block_dest_verts = None
    block_side_verts = None

    @classmethod
    def make_bridge(cls, context):
        # cannot make bridges with not integer power (we can build bridge 2 polygons -> 4 polygons, but could'nt 3 polygons -> 5 polygons, reminder polygons appears)
        if cls.block_dest_edges() % cls.block_src_edges():
            print('can not use blocks with not integer power ', cls.block_dest_edges() / cls.block_src_edges())
            return
        # for active object
        if context.selected_objects:
            bpy.ops.object.mode_set(mode='OBJECT')
            bm = bmesh.new()
            bm.from_mesh(context.object.data)
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            # if area selected - clear it
            cls.clear_selection_area(bm)
            filling_type = cls.get_filling_type(bm)
            # print(filling_type)
            for task in cls.tasks_by_filling_type(bm, filling_type):
                if task['levels'] > 0:
                    for level in range(task['levels']):
                        # print('current level: ', level)
                        task['source_loop'] = cls.build_level(bm, task['source_loop'],
                                                              task['dest_loop'],
                                                              task['from_side'] if 'from_side' in task else [],
                                                              task['to_side'] if 'to_side' in task else [],
                                                              level,
                                                              task['levels']
                                                              )
                        # print('next src_loop ', src_loop)
            bm.to_mesh(context.object.data)
            bm.free()
            bpy.ops.object.mode_set(mode='EDIT')

    @classmethod
    def tasks_by_filling_type(cls, bm, filling_type):
        # create list of tasks to fill the area (with dsta correction) from current selection
        verts_selection = [vert for vert in bm.verts if vert.select]
        active_vert = bm.select_history.active
        tasks = []
        if filling_type == 'TWO_LOOPS_SIDES_RECREATE_DEST':
            task = {'source_loop': [], 'dest_loop': [], 'from_side': [], 'to_side': [], 'levels': 0}
            loops = BmEx.get_verts_loops_from_selection(verts_selection)
            # print(loops)
            task['dest_loop'] = [loop for loop in loops if active_vert in loop][0]
            task['source_loop'] = [loop for loop in loops if task['dest_loop'][0] not in loop and task['dest_loop'][-1] not in loop][0]
            loops.remove(task['dest_loop'])
            loops.remove(task['source_loop'])
            if len(task['source_loop']) >= cls.block_src_verts and (len(task['source_loop']) - 1) % cls.block_src_edges() == 0:
                # count levels number
                any_side = [loop for loop in loops if loop != task['dest_loop'] and loop != task['source_loop']][0]
                task['levels'] = int((len(any_side) - 1) / cls.block_side_edges())
                # print('levels', task['levels'])
                # recreate dest_loop according to levels number
                BmEx.remove_verts(bm, task['dest_loop'][1:-1])
                task['dest_loop'] = BmEx.create_multiedge(bm, task['dest_loop'][0], task['dest_loop'][-1], cls.dest_loop_verts_number(len(task['source_loop']), task['levels']), select=True)
                # correct source_loop direction to dest_loop direction
                if not BmEx.loops_direction(task['source_loop'], task['dest_loop']):
                    task['source_loop'].reverse()
                # get 'from' and 'to' sides
                task['from_side'] = [loop for loop in loops if task['dest_loop'][0] and loop and task['source_loop'][0] in loop][0]
                task['to_side'] = [loop for loop in loops if task['dest_loop'][-1] and loop and task['source_loop'][-1] in loop][0]
                if not task['source_loop'][0] == task['from_side'][0]:
                    task['from_side'].reverse()
                if not task['source_loop'][-1] == task['to_side'][0]:
                    task['to_side'].reverse()
            # for elem, value in task.items():
            #     print(elem, value)
            tasks.append(task)
        elif filling_type == 'TO_CENTER_SIDES':
            task = {'source_loop': [], 'dest_loop': [], 'levels': 0}
            loops = BmEx.get_verts_loops_from_selection(verts_selection)
            print(loops)


            

            tasks.append(task)
        elif filling_type == 'TWO_LOOPS':
            task = {'source_loop': [], 'dest_loop': [], 'levels': 0}
            loops = BmEx.get_verts_loops_from_selection(verts_selection)
            # print(loops)
            if len(loops) == 2:
                src_loop = loops[0] if len(loops[0]) < len(loops[1]) else loops[1]
                dest_loop = loops[0] if src_loop == loops[1] else loops[1]
                # count levels with src and dest loops correction
                src_loop, dest_loop, levels = cls.levels(src_loop, dest_loop)
                task = {'source_loop': src_loop, 'dest_loop': dest_loop, 'levels': levels}
            tasks.append(task)
        print(tasks)
        return tasks

    @classmethod
    def clear_selection_area(cls, bm):
        # clear selection if selected an area
        verts_to_remove = [vert for vert in bm.verts if vert.select and len([edge for edge in vert.link_edges if edge.select]) == 4]
        BmEx.remove_verts(bm, verts_to_remove)

    @classmethod
    def get_filling_type(cls, bm):
        # find filing type and return this type and loops data
        filing_type = None
        verts_selection = [vert for vert in bm.verts if vert.select]
        active_vert = bm.select_history.active
        selection_is_closed_loop = BmEx.selection_is_closed_loop(verts_selection)
        if selection_is_closed_loop:
            if len(active_vert.link_edges) == 2:
                # filling between two loops with sides (with deleting dest loop and recreating it with required vertex number)
                filing_type = 'TWO_LOOPS_SIDES_RECREATE_DEST'
            else:
                # filling to center with sides
                filing_type = 'TO_CENTER_SIDES'
        if not filing_type:
            # filling between two loops without sides
            filing_type = 'TWO_LOOPS'
        return (filing_type)

    @classmethod
    def levels(cls, src_loop, dest_loop):
        if src_loop and dest_loop:
            levels = 0
            cor_src_loop = src_loop
            cor_dest_loop = dest_loop
            if len(src_loop) >= cls.block_src_verts and len(dest_loop) >= cls.block_dest_verts:
                # correct src_loop
                if not BmEx.loops_direction(src_loop, dest_loop):
                    cor_src_loop.reverse()
                # while not len(cor_src_loop) % cls.block_src_edges():
                while (len(cor_src_loop) - 1) % cls.block_src_edges():
                    cor_src_loop = cor_src_loop[:-1]
                # count levels
                src_edges = len(cor_src_loop) - 1
                dest_edges = len(dest_loop) - 1
                # print('block_level_power', cls.block_level_power())
                if cls.block_level_power() == 1:
                    levels = 1
                elif cls.block_level_power() > 1:
                    while src_edges * cls.block_level_power() <= dest_edges:
                        levels += 1
                        src_edges *= cls.block_level_power()
                        # print('src_edges', src_edges)
                        # if levels > 20:
                        #     break
                # correct dest_loop
                cor_dest_loop = dest_loop[:src_edges + 1]
            return (cor_src_loop, cor_dest_loop, levels)

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

    @classmethod
    def build_level(cls, bm, src_loop, dest_loop, from_side, to_side, level, levels):
        new_src_loop = []
        prev_block = None
        if from_side and to_side:
            prev_block = cls.block_data_from_sides(from_side[level * cls.block_side_edges():level * cls.block_side_edges() + cls.block_side_verts],
                                                   to_side[level * cls.block_side_edges():level * cls.block_side_edges() + cls.block_side_verts])
        steps_on_level = int((len(src_loop) - 1) / cls.block_src_edges())
        # print('steps ', steps_on_level)
        for step in range(steps_on_level):
            # print('current step:', step)
            step_src_loop = src_loop[step * cls.block_src_edges():step * cls.block_src_edges() + cls.block_src_verts]
            step_dest_loop = dest_loop[step * int((len(dest_loop) - 1) / steps_on_level):step * int((len(dest_loop) - 1) / steps_on_level) + int((len(dest_loop) - 1) / steps_on_level) + 1]
            # print('step_dest_loop', step_dest_loop)
            prev_block = cls.block(step_src_loop, step_dest_loop, prev_block, None, level, levels)
            # verts to BMVert
            for i, vert in enumerate(prev_block):
                if vert:
                    prev_block[i] = vert if isinstance(vert, bmesh.types.BMVert) else bm.verts.new([vert.x, vert.y, vert.z])
            block_top_line = cls.fillBlock(bm, prev_block)
            # append new_src_loop
            if not new_src_loop:
                new_src_loop.append(block_top_line[0])
            new_src_loop.extend(block_top_line[1:])
        return new_src_loop

    @classmethod
    def block(cls, src_loop, dest_loop, prev_block, next_block, level, levels):
        # make block verts here
        # returns list with current block verts
        return []

    @classmethod
    def block_data_from_sides(cls, from_side, to_side):
        # return blosk with verts getted from sides (on current level)
        return []

    @classmethod
    def fillBlock(cls, bm, block_verts):
        # make block faces from block_verts here
        # returns sorted(!) top line of the block
        return []

    @classmethod
    def block_src_edges(cls):
        return cls.block_src_verts - 1

    @classmethod
    def block_dest_edges(cls):
        return cls.block_dest_verts - 1

    @classmethod
    def block_side_edges(cls):
        return cls.block_side_verts - 1

    @classmethod
    def block_level_power(cls):
        # must be integer to build bridges
        return int(cls.block_dest_edges() / cls.block_src_edges())

    @classmethod
    def dest_loop_verts_number(cls, source_loop_verts_number, levels):
        return (source_loop_verts_number - 1) * cls.block_level_power() ** levels + 1


class QuadBirdge_3_5(QuadBridge):

    block_src_verts = 3
    block_dest_verts = 5
    block_side_verts = 3

    @classmethod
    def fillBlock(cls, bm, block_verts):
        # BMFaces from BMVerts
        bm.faces.new([block_verts[0], block_verts[3], block_verts[4], block_verts[1]])
        bm.faces.new([block_verts[1], block_verts[4], block_verts[5], block_verts[6]])
        bm.faces.new([block_verts[1], block_verts[6], block_verts[7], block_verts[2]])
        bm.faces.new([block_verts[3], block_verts[8], block_verts[9], block_verts[4]])
        bm.faces.new([block_verts[4], block_verts[9], block_verts[10], block_verts[5]])
        bm.faces.new([block_verts[5], block_verts[10], block_verts[11], block_verts[6]])
        bm.faces.new([block_verts[6], block_verts[11], block_verts[12], block_verts[7]])
        # returns sorted(!) top line of the block
        return [block_verts[8], block_verts[9], block_verts[10], block_verts[11], block_verts[12]]

    @classmethod
    def block(cls, src_loop, dest_loop, prev_block, next_block, level, levels):
        return [__class__.v0(src_loop),
                __class__.v1(src_loop),
                __class__.v2(src_loop, next_block),
                __class__.v3(src_loop, dest_loop, prev_block, level, levels),
                __class__.v4(src_loop, dest_loop, level, levels),
                __class__.v5(src_loop, dest_loop, level, levels),
                __class__.v6(src_loop, dest_loop, level, levels),
                __class__.v7(src_loop, dest_loop, next_block, level, levels),
                __class__.v8(src_loop, dest_loop, prev_block, level, levels),
                __class__.v9(src_loop, dest_loop, level, levels),
                __class__.v10(src_loop, dest_loop, level, levels),
                __class__.v11(src_loop, dest_loop, level, levels),
                __class__.v12(src_loop, dest_loop, next_block, level, levels)
                ]

    @classmethod
    def block_data_from_sides(cls, from_side, to_side):
        return [from_side[0],
                None,
                to_side[0],
                from_side[1],
                None,
                None,
                None,
                to_side[1],
                from_side[2],
                None,
                None,
                None,
                to_side[2]
                ]

    @staticmethod
    def v0(src_loop):
        return src_loop[0]

    @staticmethod
    def v1(src_loop):
        return src_loop[1]

    @staticmethod
    def v2(src_loop, next_block):
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
            return v1 + direction * length

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
        return v1 + direction * length

    @staticmethod
    def v6(src_loop, dest_loop, level, levels):
        v1 = src_loop[1].co + (src_loop[2].co - src_loop[1].co) / 2
        v2 = dest_loop[int((len(dest_loop) - 1) * 3 / 4)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) / 2
        return v1 + direction * length

    @staticmethod
    def v7(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[3]
        else:
            v1 = src_loop[2].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels) / 2
            return v1 + direction * length

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
            return v1 + direction * length

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
            return v1 + direction * length

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
    def v12(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[8]
        elif level == levels - 1:
            return dest_loop[4]
        else:
            v1 = src_loop[2].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length


class QuadBirdge_2_4(QuadBridge):

    block_src_verts = 2
    block_dest_verts = 4
    block_side_verts = 3

    @classmethod
    def fillBlock(cls, bm, block_verts):
        # BMFaces from BMVerts
        bm.faces.new([block_verts[0], block_verts[2], block_verts[3], block_verts[4]])
        bm.faces.new([block_verts[0], block_verts[4], block_verts[5], block_verts[1]])
        bm.faces.new([block_verts[2], block_verts[6], block_verts[7], block_verts[3]])
        bm.faces.new([block_verts[3], block_verts[7], block_verts[8], block_verts[4]])
        bm.faces.new([block_verts[4], block_verts[8], block_verts[9], block_verts[5]])
        # returns sorted(!) top line of the block
        return [block_verts[6], block_verts[7], block_verts[8], block_verts[9]]

    @classmethod
    def block(cls, src_loop, dest_loop, prev_block, next_block, level, levels):
        return [__class__.v0(src_loop),
                __class__.v1(src_loop, next_block),
                __class__.v2(src_loop, dest_loop, prev_block, level, levels),
                __class__.v3(src_loop, dest_loop, level, levels),
                __class__.v4(src_loop, dest_loop, level, levels),
                __class__.v5(src_loop, dest_loop, next_block, level, levels),
                __class__.v6(src_loop, dest_loop, prev_block, level, levels),
                __class__.v7(src_loop, dest_loop, level, levels),
                __class__.v8(src_loop, dest_loop, level, levels),
                __class__.v9(src_loop, dest_loop, next_block, level, levels)
                ]

    @classmethod
    def block_data_from_sides(cls, from_side, to_side):
        return [from_side[0],
                to_side[0],
                from_side[1],
                None,
                None,
                to_side[1],
                from_side[2],
                None,
                None,
                to_side[2]
                ]

    @staticmethod
    def v0(src_loop):
        return src_loop[0]

    @staticmethod
    def v1(src_loop, next_block):
        return src_loop[1]

    @staticmethod
    def v2(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[5]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels) / 2
            return v1 + direction * length

    @staticmethod
    def v3(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[1].co - src_loop[0].co) * 1 / 3
        v2 = dest_loop[int((len(dest_loop) - 1) / 3)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) * 2 / 3
        return v1 + direction * length

    @staticmethod
    def v4(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[1].co - src_loop[0].co) * 2 / 3
        v2 = dest_loop[int((len(dest_loop) - 1) * 2 / 3)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) / 2
        return v1 + direction * length

    @staticmethod
    def v5(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[2]
        else:
            v1 = src_loop[1].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels, 1) / 2
            return v1 + direction * length

    @staticmethod
    def v6(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[9]
        elif level == levels - 1:
            return dest_loop[0]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v7(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[1]
        else:
            v1 = src_loop[0].co + (src_loop[1].co - src_loop[0].co) * 1 / 3
            v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 3)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v8(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[2]
        else:
            v1 = src_loop[0].co + (src_loop[1].co - src_loop[0].co) * 2 / 3
            v2 = dest_loop[int((len(dest_loop) - 1) * 2 / 3)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v9(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[6]
        elif level == levels - 1:
            return dest_loop[3]
        else:
            v1 = src_loop[1].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length


class QuadBirdge_2_2(QuadBridge):

    block_src_verts = 2
    block_dest_verts = 2
    block_side_verts = 3

    @classmethod
    def fillBlock(cls, bm, block_verts):
        # BMFaces from BMVerts
        bm.faces.new([block_verts[0], block_verts[2], block_verts[3], block_verts[1]])
        bm.faces.new([block_verts[2], block_verts[4], block_verts[5], block_verts[3]])
        # returns sorted(!) top line of the block
        return [block_verts[4], block_verts[5]]

    @classmethod
    def block(cls, src_loop, dest_loop, prev_block, next_block, level, levels):
        return [__class__.v0(src_loop),
                __class__.v1(src_loop, next_block),
                __class__.v2(src_loop, dest_loop, prev_block, level, levels),
                __class__.v3(src_loop, dest_loop, next_block, level, levels),
                __class__.v4(src_loop, dest_loop, prev_block, level, levels),
                __class__.v5(src_loop, dest_loop, next_block, level, levels)
                ]

    @classmethod
    def block_data_from_sides(cls, from_side, to_side):
        return [from_side[0],
                to_side[0],
                from_side[1],
                to_side[1],
                from_side[2],
                to_side[2]
                ]

    @staticmethod
    def v0(src_loop):
        return src_loop[0]

    @staticmethod
    def v1(src_loop, next_block):
        return src_loop[1]

    @staticmethod
    def v2(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[3]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels) / 2
            return v1 + direction * length

    @staticmethod
    def v3(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[2]
        else:
            v1 = src_loop[1].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels, 1) / 2
            return v1 + direction * length

    @staticmethod
    def v4(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[5]
        elif level == levels - 1:
            return dest_loop[0]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v5(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[4]
        elif level == levels - 1:
            return dest_loop[1]
        else:
            v1 = src_loop[1].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length


class QuadBirdge_1_3(QuadBridge):

    block_src_verts = 3
    block_dest_verts = 5
    block_side_verts = 3

    @classmethod
    def fillBlock(cls, bm, block_verts):
        # BMFaces from BMVerts
        bm.faces.new([block_verts[0], block_verts[5], block_verts[6], block_verts[1]])
        bm.faces.new([block_verts[1], block_verts[6], block_verts[7], block_verts[2]])
        bm.faces.new([block_verts[0], block_verts[3], block_verts[4], block_verts[5]])
        bm.faces.new([block_verts[2], block_verts[7], block_verts[8], block_verts[9]])
        bm.faces.new([block_verts[3], block_verts[10], block_verts[11], block_verts[4]])
        bm.faces.new([block_verts[4], block_verts[11], block_verts[12], block_verts[5]])
        bm.faces.new([block_verts[6], block_verts[5], block_verts[12], block_verts[7]])
        bm.faces.new([block_verts[7], block_verts[12], block_verts[13], block_verts[8]])
        bm.faces.new([block_verts[8], block_verts[13], block_verts[14], block_verts[9]])
        # returns sorted(!) top line of the block
        return [block_verts[10], block_verts[11], block_verts[12], block_verts[13], block_verts[14]]

    @classmethod
    def block(cls, src_loop, dest_loop, prev_block, next_block, level, levels):
        return [__class__.v0(src_loop),
                __class__.v1(src_loop),
                __class__.v2(src_loop, next_block),
                __class__.v3(src_loop, dest_loop, prev_block, level, levels),
                __class__.v4(src_loop, dest_loop, level, levels),
                __class__.v5(src_loop, dest_loop, level, levels),
                __class__.v6(src_loop, dest_loop, level, levels),
                __class__.v7(src_loop, dest_loop, level, levels),
                __class__.v8(src_loop, dest_loop, level, levels),
                __class__.v9(src_loop, dest_loop, next_block, level, levels),
                __class__.v10(src_loop, dest_loop, prev_block, level, levels),
                __class__.v11(src_loop, dest_loop, level, levels),
                __class__.v12(src_loop, dest_loop, level, levels),
                __class__.v13(src_loop, dest_loop, level, levels),
                __class__.v14(src_loop, dest_loop, next_block, level, levels)
                ]

    @classmethod
    def block_data_from_sides(cls, from_side, to_side):
        return [from_side[0],
                None,
                to_side[0],
                from_side[1],
                None,
                None,
                None,
                None,
                None,
                to_side[1],
                from_side[2],
                None,
                None,
                None,
                to_side[2]
                ]

    @staticmethod
    def v0(src_loop):
        return src_loop[0]

    @staticmethod
    def v1(src_loop):
        return src_loop[1]

    @staticmethod
    def v2(src_loop, next_block):
        return src_loop[2]

    @staticmethod
    def v3(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[9]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels) / 2
            return src_loop[0].co + direction * length

    @staticmethod
    def v4(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 1 / 4
        v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 4)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) * 2 / 3
        return v1 + direction * length

    @staticmethod
    def v5(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 3 / 8
        v2 = dest_loop[0].co + (dest_loop[len(dest_loop) - 1].co - dest_loop[0].co) * 3 / 8
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels, 1) * 5 / 8
        return v1 + direction * length

    @staticmethod
    def v6(src_loop, dest_loop, level, levels):
        v1 = src_loop[1].co
        v2 = dest_loop[0].co + (dest_loop[len(dest_loop) - 1].co - dest_loop[0].co) * 1 / 2
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) * 1 / 4
        return v1 + direction * length

    @staticmethod
    def v7(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 5 / 8
        v2 = dest_loop[0].co + (dest_loop[-1].co - dest_loop[0].co) * 5 / 8
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) * 5 / 8
        return v1 + direction * length

    @staticmethod
    def v8(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 3 / 4
        v2 = dest_loop[int((len(dest_loop) - 1) * 3 / 4)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) * 2 / 3
        return v1 + direction * length

    @staticmethod
    def v9(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[3]
        else:
            v1 = src_loop[2].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels) / 2
            return v1 + direction * length

    @staticmethod
    def v10(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[14]
        elif level == levels - 1:
            return dest_loop[0]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v11(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[1]
        else:
            v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 1 / 4
            v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 4)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v12(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[2]
        else:
            v1 = src_loop[1].co
            v2 = dest_loop[int((len(dest_loop) - 1) / 2)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v13(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[3]
        else:
            v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 3 / 4
            v2 = dest_loop[int((len(dest_loop) - 1) * 3 / 4)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v14(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[10]
        elif level == levels - 1:
            return dest_loop[4]
        else:
            v1 = src_loop[2].co
            v2 = dest_loop[len(dest_loop) - 1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length


class QuadBirdge_3_7(QuadBridge):

    block_src_verts = 3
    block_dest_verts = 7
    block_side_verts = 3

    @classmethod
    def fillBlock(cls, bm, block_verts):
        # BMFaces from BMVerts
        bm.faces.new([block_verts[0], block_verts[3], block_verts[4], block_verts[1]])
        bm.faces.new([block_verts[1], block_verts[4], block_verts[5], block_verts[6]])
        bm.faces.new([block_verts[1], block_verts[6], block_verts[7], block_verts[8]])
        bm.faces.new([block_verts[1], block_verts[8], block_verts[9], block_verts[2]])
        bm.faces.new([block_verts[3], block_verts[10], block_verts[11], block_verts[4]])
        bm.faces.new([block_verts[4], block_verts[11], block_verts[12], block_verts[5]])
        bm.faces.new([block_verts[5], block_verts[12], block_verts[13], block_verts[6]])
        bm.faces.new([block_verts[6], block_verts[13], block_verts[14], block_verts[7]])
        bm.faces.new([block_verts[7], block_verts[14], block_verts[15], block_verts[8]])
        bm.faces.new([block_verts[8], block_verts[15], block_verts[16], block_verts[9]])
        # returns sorted(!) top line of the block
        return [block_verts[10], block_verts[11], block_verts[12], block_verts[13], block_verts[14], block_verts[15], block_verts[16]]

    @classmethod
    def block(cls, src_loop, dest_loop, prev_block, next_block, level, levels):
        return [__class__.v0(src_loop),
                __class__.v1(src_loop),
                __class__.v2(src_loop, next_block),
                __class__.v3(src_loop, dest_loop, prev_block, level, levels),
                __class__.v4(src_loop, dest_loop, level, levels),
                __class__.v5(src_loop, dest_loop, level, levels),
                __class__.v6(src_loop, dest_loop, level, levels),
                __class__.v7(src_loop, dest_loop, level, levels),
                __class__.v8(src_loop, dest_loop, level, levels),
                __class__.v9(src_loop, dest_loop, next_block, level, levels),
                __class__.v10(src_loop, dest_loop, prev_block, level, levels),
                __class__.v11(src_loop, dest_loop, level, levels),
                __class__.v12(src_loop, dest_loop, level, levels),
                __class__.v13(src_loop, dest_loop, level, levels),
                __class__.v14(src_loop, dest_loop, level, levels),
                __class__.v15(src_loop, dest_loop, level, levels),
                __class__.v16(src_loop, dest_loop, next_block, level, levels)
                ]

    @classmethod
    def block_data_from_sides(cls, from_side, to_side):
        return [from_side[0],
                None,
                to_side[0],
                from_side[1],
                None,
                None,
                None,
                None,
                None,
                to_side[1],
                from_side[2],
                None,
                None,
                None,
                None,
                None,
                to_side[2]
                ]

    @staticmethod
    def v0(src_loop):
        return src_loop[0]

    @staticmethod
    def v1(src_loop):
        return src_loop[1]

    @staticmethod
    def v2(src_loop, next_block):
        return src_loop[2]

    @staticmethod
    def v3(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[9]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels) / 2
            return v1 + direction * length

    @staticmethod
    def v4(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 1 / 6
        v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 6)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) / 2
        return v1 + direction * length

    @staticmethod
    def v5(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 1 / 3
        v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 3)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels, 1) * 3 / 4
        return v1 + direction * length

    @staticmethod
    def v6(src_loop, dest_loop, level, levels):
        v1 = src_loop[1].co
        v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 2)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) / 2
        return v1 + direction * length

    @staticmethod
    def v7(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 2 / 3
        v2 = dest_loop[int((len(dest_loop) - 1) * 2 / 3)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) * 3 / 4
        return v1 + direction * length

    @staticmethod
    def v8(src_loop, dest_loop, level, levels):
        v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 5 / 6
        v2 = dest_loop[int((len(dest_loop) - 1) * 5 / 6)].co
        direction = v2 - v1
        direction.normalize()
        length = __class__.level_height(v1, v2, level, levels) / 2
        return v1 + direction * length

    @staticmethod
    def v9(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[3]
        else:
            v1 = src_loop[2].co
            v2 = dest_loop[-1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels) / 2
            return v1 + direction * length

    @staticmethod
    def v10(src_loop, dest_loop, prev_block, level, levels):
        if prev_block:
            return prev_block[16]
        elif level == levels - 1:
            return dest_loop[0]
        else:
            v1 = src_loop[0].co
            v2 = dest_loop[0].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v11(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[1]
        else:
            v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 1 / 6
            v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 6)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v12(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[2]
        else:
            v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 1 / 3
            v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 3)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v13(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[3]
        else:
            v1 = src_loop[1].co
            v2 = dest_loop[int((len(dest_loop) - 1) * 1 / 2)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v14(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[4]
        else:
            v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 2 / 3
            v2 = dest_loop[int((len(dest_loop) - 1) * 2 / 3)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v15(src_loop, dest_loop, level, levels):
        if level == levels - 1:
            return dest_loop[5]
        else:
            v1 = src_loop[0].co + (src_loop[2].co - src_loop[0].co) * 5 / 6
            v2 = dest_loop[int((len(dest_loop) - 1) * 5 / 6)].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length

    @staticmethod
    def v16(src_loop, dest_loop, next_block, level, levels):
        if next_block:
            return next_block[10]
        elif level == levels - 1:
            return dest_loop[6]
        else:
            v1 = src_loop[2].co
            v2 = dest_loop[-1].co
            direction = v2 - v1
            direction.normalize()
            length = __class__.level_height(v1, v2, level, levels)
            return v1 + direction * length


class QuadBridges:

    # add new Bridge class here to make new preview in the menu
    bridges = [['3-5', 'b00.jpg', QuadBirdge_3_5],
               ['2-4', 'b01.jpg', QuadBirdge_2_4],
               ['2-2', 'b02.jpg', QuadBirdge_2_2],
               ['1-3 (3-5)', 'b03.jpg', QuadBirdge_1_3],
               ['3-7', 'b04.jpg', QuadBirdge_3_7],
               ]

    @staticmethod
    def bridge(bridge_id, context):
        if __class__.bridges[bridge_id][2]:
            __class__.bridges[bridge_id][2].make_bridge(context)


class BmEx:
    @staticmethod
    def get_verts_loops_from_selection(verts_selecton_list):
        # get the lists of the arranged vertex loops from selection
        loops = []
        extreme_verts = [vert for vert in verts_selecton_list if vert.select and __class__.is_vert_extreme(vert)]
        for vert in extreme_verts:
            # print('extreme verts', extreme_verts)
            # print('extreme vert', vert)
            extreme_verts.remove(vert)
            # for next_vert in [edge.other_vert(vert) for edge in vert.link_edges if edge.select]:
            for edge in [edge for edge in vert.link_edges if edge.select]:
                if extreme_verts:
                    current_loop = [vert]
                    next_vert = edge.other_vert(vert)
                    while next_vert:
                        current_loop.append(next_vert)
                        selected_edges = [edge for edge in next_vert.link_edges if edge.select]
                        # print(selected_edges)
                        if __class__.is_vert_extreme_endpoint(next_vert):
                            # comes to endpoint
                            loops.append(current_loop)
                            extreme_verts.remove(next_vert)
                            next_vert = None
                        else:
                            if __class__.is_vert_extreme_angle(next_vert):
                                if next_vert in extreme_verts:
                                    # comes through the 90 degree corner - finish this loop and start new loop
                                    extreme_verts.remove(next_vert)
                                    loops.append(current_loop)
                                    next_edge = [edge for edge in selected_edges if (edge.verts[0] not in current_loop or edge.verts[1] not in current_loop)][0]
                                    current_loop = [next_vert]
                                    next_vert = next_edge.other_vert(next_vert)
                                else:
                                    # comes to angle-vert in closed loop from which starts - finish current loop and stop
                                    loops.append(current_loop)
                                    break
                            else:
                                # continue to next vert
                                next_edge = [edge for edge in selected_edges if (edge.verts[0] not in current_loop or edge.verts[1] not in current_loop)][0]
                                next_vert = next_edge.other_vert(next_vert)
        return loops

    @staticmethod
    def is_vert_extreme(vert):
        # check is vert is extreme
        return __class__.is_vert_extreme_angle(vert) or __class__.is_vert_extreme_endpoint(vert)

    @staticmethod
    def is_vert_extreme_endpoint(vert):
        # check if vert is the endpoint extreme
        selected_edges = [edge for edge in vert.link_edges if edge.select]
        return True if len(selected_edges) == 1 else False

    @staticmethod
    def is_vert_extreme_angle(vert):
        # check if vert is the 90 degree angle extreme
        selected_edges = [edge for edge in vert.link_edges if edge.select]
        return True if (len(selected_edges) == 2 and (len(vert.link_edges) == 4 or len(vert.link_faces) == 1)) else False

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

    @staticmethod
    def selection_is_closed_loop(selection_verts):
        # check if selection is a closed verts loop
        is_closed_loop = True
        for vert in selection_verts:
            if len([edge for edge in vert.link_edges if edge.select]) != 2:
                is_closed_loop = False
                break
        return is_closed_loop

    @staticmethod
    def remove_verts(bm, verts_list):
        # remove verts by verts_list
        for vert in verts_list:
            bm.verts.remove(vert)

    @staticmethod
    def create_multiedge(bm, vert1, vert2, verts_count, select=False):
        # create edges loop between two verts consists of verts_count verts (including v1 and v2)
        direction = vert2.co - vert1.co
        length = direction.length / (verts_count - 1)
        direction.normalize()
        loop = [vert1]
        next_vert = vert1
        for i in range(verts_count - 2):
            next_vert = bm.verts.new((next_vert.co + direction * length))
            next_edge = bm.edges.new((loop[-1], next_vert))
            loop.append(next_vert)
            if select:
                next_vert.select = True
                next_edge.select = True
        bm.edges.new((loop[-1], vert2))
        loop.append(vert2)
        return loop


class QuadBridgePanel(bpy.types.Panel):
    bl_idname = 'quadbridge.panel'
    bl_label = 'QuadBridge'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = '1D'

    def draw(self, context):
        self.layout.template_icon_view(context.window_manager.quadbridge_previews, 'items', show_labels=True)


class QuadBridgeOp(bpy.types.Operator):
    bl_idname = 'quadbridge.start'
    bl_label = 'Make Bridge 2-4'
    bl_options = {'REGISTER', 'UNDO'}

    bridge_id = bpy.props.IntProperty(
        name='BridgeId',
        default=0
    )

    def execute(self, context):
        QuadBridges.bridge(self.bridge_id, context)
        return {'FINISHED'}


class QuadBridgePreviews:

    items_list = None

    @staticmethod
    def register():
        __class__.items_list = bpy.utils.previews.new()
        __class__.items_list.items = []
        __class__.create_previews()

    @staticmethod
    def unregister():
        __class__.items_list.items.clear()
        bpy.utils.previews.remove(__class__.items_list)

    @staticmethod
    def create_previews():
        for i, bridge in enumerate(QuadBridges.bridges):
            path = __class__.get_preview_path(bridge[1])
            thumb = __class__.items_list.load(path, path, 'IMAGE')
            __class__.items_list.items.append((str(i), bridge[0], '', thumb.icon_id, i))

    @staticmethod
    def get_previews(self, context):
        if context:
            return __class__.items_list.items
        else:
            return []

    @staticmethod
    def get_preview_path(filename):
        return os.path.dirname(os.path.abspath(getsourcefile(lambda:0))) + os.path.sep + 'img' + os.path.sep + filename

    @staticmethod
    def on_preview_select(self, context):
        bpy.ops.quadbridge.start(bridge_id=int(self.items))
        bpy.ops.ed.undo_push()


class QuadBridgePreviewsItems(bpy.types.PropertyGroup):
    items = bpy.props.EnumProperty(
        items=lambda self, context: QuadBridgePreviews.get_previews(self, context),
        update=lambda self, context: QuadBridgePreviews.on_preview_select(self, context)
    )


def register():
    bpy.utils.register_class(QuadBridgeOp)
    bpy.utils.register_class(QuadBridgePanel)
    QuadBridgePreviews.register()
    bpy.utils.register_class(QuadBridgePreviewsItems)
    bpy.types.WindowManager.quadbridge_previews = bpy.props.PointerProperty(type=QuadBridgePreviewsItems)


def unregister():
    del bpy.types.WindowManager.quadbridge_previews
    QuadBridgePreviews.unregister()
    bpy.utils.unregister_class(QuadBridgePreviewsItems)
    bpy.utils.unregister_class(QuadBridgePanel)
    bpy.utils.unregister_class(QuadBridgeOp)


if __name__ == '__main__':
    register()
