import os
import sublime
import sublime_plugin
from .tree import Tree


class SidebarMakeTreeCommand(sublime_plugin.WindowCommand):
    def get_tree_settings(self):
        settings = sublime.load_settings(
            'SublimeDirectoryTree.sublime-settings')
        tree_settings = settings.get('args', {
            "mode": "ff",
            "indent": 4,
            "sparse": False,
            "dir_tail_character": "",
            "show_hidden": False
        })
        tree_settings['dtail'] = tree_settings.pop("dir_tail_character")
        return tree_settings

    def is_visible(self, paths):
        return len(paths) == 1 and os.path.isdir(paths[0])

    def run(self, paths):
        tree_settings = self.get_tree_settings()
        tree = Tree(paths[0], **tree_settings)
        text = "mode: %s\n\n" % tree.mode_descriptions[tree.mode]
        text += tree.tree

        view = self.window.new_file()
        view.assign_syntax("tree.sublime-syntax")
        view.set_name("%s.tr" % os.path.basename(paths[0]))
        view.settings().set("font_face", "Lucida Console")
        view.settings().set("word_wrap", False)
        view.settings().set("translate_tabs_to_spaces", True)
        view.run_command("append", {"characters": text})
        view.set_scratch(True)
        view.set_read_only(True)


class SidebarMakeTreeAndSendToClipboardCommand(SidebarMakeTreeCommand):
    def run(self, paths):
        tree_settings = self.get_tree_settings()
        tree = Tree(paths[0], **tree_settings)

        sublime.set_clipboard(tree.tree)

