import os
import sys

def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f

def str_size(nbyte):
    k = 0
    while nbyte >> (k + 10):
        k += 10
    units = ("B", "KB", "MB", "GB")
    size_by_unit = round(nbyte / (1 << k), 2) if k else nbyte
    return str(size_by_unit) + units[k // 10]

class Tree():
    mode_descriptions = {
        'df': 'Directory First',
        'do': 'Directory Only',
        'ff': 'File First',
        'od': 'Ordered'
    }

    def __init__(self, path, indent=4, mode='ff', layer=0,
        sparse=True, dtail='/', show_hidden=False, show_size=False,
        show_absolute_path_of_rootdir=False):
        indent = min(max(indent, 1), 8)
        self.sparse = sparse
        self.dtail = dtail
        self.layer = layer if layer > 0 else 65535
        self.indent_space = ' ' * indent
        self.down_space = '│' + ' ' * (indent - 1)
        self.vert_horiz = '├' + '─' * (indent - 1)
        self.turn_horiz = '└' + '─' * (indent - 1)

        self.traverses = {
            'df': self.df,
            'do': self.do,
            'ff': self.ff,
            'od': self.od
        }
        self.listdir = os.listdir if show_hidden else listdir_nohidden
        self.show_size = show_size
        self.show_absolute_path_of_rootdir = show_absolute_path_of_rootdir

        self.chmod(mode)
        self.generate(path)

    def write(self, filename):
        with open(filename, 'w+', encoding='utf-8') as fd:
            fd.write('mode: %s\n' % self.mode)
            fd.write('\n')
            fd.write(self.tree)

    def print(self):
        print(self.tree)

    def chmod(self, mode):
        assert mode in self.traverses
        self.traverse = self.traverses[mode]
        self.mode = self.mode_descriptions[mode]

    def generate(self, path):
        """
        metadata: [(path, isfile?, size) or None], maybe use to open file
        size: file size, or number of files in a Directory, is a string
        """
        assert os.path.isdir(path)
        self.metadata = []
        self.lines = [path]
        if not self.show_absolute_path_of_rootdir:
            self.lines[0] = os.path.basename(path)
        self.traverse(path, '', 0)

        if self.lines[-1] == '':
            self.lines.pop()
            self.metadata.pop()

        if self.show_size:
            sep = self.indent_space
            size_len = max(len(md[2]) for md in self.metadata if md)
            for i, mdata in enumerate(self.metadata):
                size = mdata[2] if mdata else ' '
                size = '%*s' % (size_len, size)
                if self.lines[i]:
                    self.lines[i] = size + sep + self.lines[i]

        self.tree = '\n'.join(self.lines) + '\n'

    def get_dirs_files(self, dirpath):
        dirs, files = [], []
        for leaf in self.listdir(dirpath):
            path = os.path.join(dirpath, leaf)
            if os.path.isfile(path):
                files.append((leaf, path))
            else:
                dirs.append((leaf, path))
        self.metadata.append((dirpath, False, str(len(dirs) + len(files))))

        return dirs, files

    def add_dirs(self, dirs, prefix, recursive, layer):
        fprefix = prefix + self.down_space
        dprefix = prefix + self.vert_horiz
        for dirname, path in dirs[:-1]:
            self.lines.append(dprefix + dirname + self.dtail)
            recursive(path, fprefix, layer + 1)

        fprefix = prefix + self.indent_space
        dprefix = prefix + self.turn_horiz
        dirname, path = dirs[-1]
        self.lines.append(dprefix + dirname + self.dtail)
        recursive(path, fprefix, layer + 1)

    def add_files(self, files, fprefix):
        for filename, path in files:
            size = str_size(os.path.getsize(path))
            self.lines.append(fprefix + filename)
            self.metadata.append((path, True, size))
        if self.sparse and files:
            self.lines.append(fprefix.rstrip())
            self.metadata.append(None)

    def df(self, dirpath, prefix, layer):
        dirs, files = self.get_dirs_files(dirpath)
        if layer < self.layer:
            if dirs:
                self.add_dirs(dirs, prefix, self.df, layer)
            self.add_files(files, prefix + self.indent_space)

    def do(self, dirpath, prefix, layer):
        dirs, files = self.get_dirs_files(dirpath)
        if layer < self.layer and dirs:
            self.add_dirs(dirs, prefix, self.do, layer)

    def ff(self, dirpath, prefix, layer):
        dirs, files = self.get_dirs_files(dirpath)
        if layer < self.layer:
            if dirs:
                self.add_files(files, prefix + self.down_space)
                self.add_dirs(dirs, prefix, self.ff, layer)
            else:
                self.add_files(files, prefix + self.indent_space)

    def od(self, dirpath, prefix, layer):
        def add_leaf(leaf):
            path = os.path.join(dirpath, leaf)
            if os.path.isfile(path):
                size = str_size(os.path.getsize(path))
                self.lines.append(dprefix + leaf)
                self.metadata.append((path, True, size))
            if os.path.isdir(path):
                self.lines.append(dprefix + leaf + self.dtail)
                self.od(path, fprefix, layer + 1)

        leaves = list(self.listdir(dirpath))
        self.metadata.append((dirpath, False, str(len(leaves))))

        if layer < self.layer and leaves:
            leaves.sort()

            fprefix = prefix + self.down_space
            dprefix = prefix + self.vert_horiz
            for leaf in leaves[:-1]:
                add_leaf(leaf)

            fprefix = prefix + self.indent_space
            dprefix = prefix + self.turn_horiz
            add_leaf(leaves[-1])
