import copy

import treelib as tree

from core.source import Source
from core.transmission import Cable
from core.component import Component
from helpers.tree_utils import get_tree_edges, link_into_edge


class Model:

    def __init__(self):
        self._source_index = 0
        self._sink_index = 0
        self._source_list = []
        self._sink_tree = tree.Tree()
        self._sink_tree.create_node("Root", 0, None, Root([0, 0, 0]))
        self.load_case_num = 0

    def solve_model(self, load_cases):
        root_powers = list()
        for load_case in load_cases:
            root_powers.append(self.solve_model_case(load_cases.index(load_case)))
        return root_powers

    def solve_model_case(self, load_case_num):
        # TODO: decide on linking between sink and source roots
        self.load_case_num = load_case_num

        self.reset_components()

        # get root component and update its children
        root_comp = self._sink_tree.get_node(self._sink_tree.root).data
        root_comp.name = "Root"
        children_indices = self._sink_tree.is_branch(root_comp.get_index())
        children = [self._sink_tree.get_node(index).data for index in children_indices]
        root_comp.set_children(children)

        # solve root -> solve tree
        root_power = root_comp.get_power_in(self.load_case_num)
        return root_power

    def import_components(self, components):
        self.initialize_tree(components)

    def import_epla(self, filepath):
        # self.initialize_tree(components)
        pass

    def initialize_tree(self, components):
        # populate trees
        # right now, just connects components in order in a straight line
        # TODO: replace this loop with logic for populating OLD
        for comp in components:
            if isinstance(comp, Source):
                self.add_source(comp)
            else:
                self.add_sink_from_index(comp, self._sink_index)

        self.update_dependencies(components)

    def update_dependencies(self, components):
        # TODO: remove this
        # this is a hasty fix for a more specific problem that every time we update the tree we need
        # to update each component

        # assign parents/children to components
        # this assigns a pointer for each parent and child to each component
        # allowing us to recurse through all the children from the root
        for comp in components:
            children_indices = self._sink_tree.is_branch(comp.get_index())
            children = [self._sink_tree.get_node(index).data for index in children_indices]
            comp.set_children(children)
            if isinstance(comp, Root):
                comp.set_parents(None)
            else:
                parent = self._sink_tree.parent(comp.get_index()).data
                comp.set_parents(parent)

    def reset_components(self):
        components = [node.data for node in self._sink_tree.all_nodes()]
        for comp in components:
            comp.reset()
        self.update_dependencies(components)

    def add_sink(self, new_sink, parent):
        self._sink_index += 1  # index starts at 1
        parent_index = parent.get_index()
        self._sink_tree.create_node(new_sink.name, self._sink_index, parent=parent_index, data=new_sink)
        new_sink.set_index(self._sink_index)
        self.update_dependencies([new_sink])

    def add_sink_from_index(self, new_sink, parent_index):
        self._sink_index += 1  # index starts at 1
        self._sink_tree.create_node(new_sink.name, self._sink_index, parent=parent_index, data=new_sink)
        new_sink.set_index(self._sink_index)
        self.update_dependencies([new_sink])

    def add_source(self, new_source):
        self._source_list.append(new_source)
        self._source_index += 1

    def remove_sink(self, sink):
        if sink.get_index() == 0:
            print("Error: Sink does not exist in tree. No sink removed.")
        self._sink_tree.link_past_node(sink.get_index())

    def remove_source(self, source):
        # TODO: find more robust method for checking if index is valid
        # if source.get_index() == 0:
        #     print("Error: Source does not exist in list. No source removed.")
        self._source_list.pop(source.get_index())

    def add_cables(self):
        # add cables in between all component "edges" (sets of two linked components)
        index = self._sink_tree.size() + 2
        edges = get_tree_edges(self._sink_tree)
        for edge in edges:
            new_node = tree.Node("Cable " + str(self._sink_index),
                                 self._sink_index,
                                 data=Cable([0, 0, 0]))
            index += 1
            tt = link_into_edge(new_node, edge, self._sink_tree)
        self.reset_components()

    def print_tree(self):
        self._sink_tree.show()

    def export_old(self, filepath):
        pass

    def copy(self):
        return copy.copy(self)


class Root(Component):

    def __init__(self, location):
        super().__init__(location)

    def get_power_in(self, load_case_num):
        return self.get_power_out(load_case_num)
