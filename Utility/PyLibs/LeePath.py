# -*- coding: utf-8 -*-

import os
import sys

class LeePath:
    def __init__(self):
        pass
    
    def __withmark(self, val, withmark = True):
        if os.path.isfile(val):
            return val
        return val if not withmark else val + os.sep

    def utility(self, relpath = '', withmark = True):
        # 之所以需要 .. 是应为当前脚本在 PyLibs 目录下
        # 只有切换到上级目录才是 LeeClientAgent.py 的目录, 即: Utility
        path = os.path.join(os.path.split(os.path.realpath(__file__))[0], '..')
        path = os.path.join(path, relpath)
        return self.__withmark(os.path.abspath(path), withmark)
    
    def client(self, relpath = '', withmark = True):
        path = self.utility('..', withmark)
        path = os.path.join(path, relpath)
        return self.__withmark(os.path.abspath(path), withmark)
    
    def bin(self, relpath = '', withmark = True):
        path = self.utility('Bin', withmark)
        path = os.path.join(path, relpath)
        return self.__withmark(os.path.abspath(path), withmark)
    
    def imports(self, relpath = '', withmark = True):
        path = self.utility('Import', withmark)
        path = os.path.join(path, relpath)
        return self.__withmark(os.path.abspath(path), withmark)
    
    def patches(self, relpath = '', withmark = True):
        path = self.utility('Patches', withmark)
        path = os.path.join(path, relpath)
        return self.__withmark(os.path.abspath(path), withmark)
    
    def resources(self, relpath = '', withmark = True):
        path = self.utility('Resources', withmark)
        path = os.path.join(path, relpath)
        return self.__withmark(os.path.abspath(path), withmark)
    
    def reports(self, relpath = '', withmark = True):
        path = self.utility('Reports', withmark)
        path = os.path.join(path, relpath)
        return self.__withmark(os.path.abspath(path), withmark)

    def special(self, clientver, dirtype, relpath = '', withmark = True):
        if dirtype == 'origin':
            path = '{ver}/Resource/Original'.format(ver=clientver)
            operater = self.patches
        elif dirtype == 'translated':
            path = '{ver}/Resource/Translated'.format(ver=clientver)
            operater = self.patches
        elif dirtype == 'temporary':
            path = '{ver}/Resource/Temporary'.format(ver=clientver)
            operater = self.patches
        elif dirtype == 'build':
            path = '{ver}/Ragexe/Build'.format(ver=clientver)
            operater = self.patches
        elif dirtype == 'import_version':
            path = '{ver}'.format(ver=clientver)
            operater = self.imports
        elif dirtype == 'import_before':
            path = 'Common/BeforePatches'
            operater = self.imports
        elif dirtype == 'import_after':
            path = 'Common/AfterPatches'
            operater = self.imports
        elif dirtype == 'patches_before':
            path = 'Common/BeforePatches'
            operater = self.patches
        elif dirtype == 'patches_after':
            path = 'Common/AfterPatches'
            operater = self.patches
        else:
            print('LeePath: special 函数中 dirtype 参数的值无效.')
            sys.exit(-1)
        
        path = operater(path, False)
        path = os.path.join(path, relpath)
        return self.__withmark(os.path.abspath(path), withmark)
