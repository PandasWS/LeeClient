# -*- coding: utf-8 -*-

import json
import os

from PyLibs import LeeCommon


class LeeBaseRevert:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.revertDefaultDBPath = None
        self.revertFiles = []

    def clearRevert(self):
        self.revertFiles.clear()

    def loadRevert(self, revertDatabaseLoadpath = None):
        if revertDatabaseLoadpath is None:
            revertDatabaseLoadpath = self.revertDefaultDBPath
        revertDatabaseLoadpath = '%s/%s' % (
            self.leeCommon.utility(withmark=False), revertDatabaseLoadpath
        )
        if not self.leeCommon.isFileExists(revertDatabaseLoadpath):
            return False

        self.revertFiles.clear()
        revertContent = json.load(open(revertDatabaseLoadpath, 'r', encoding = 'utf-8'))
        self.revertFiles = revertContent['files']

        # 标准化处理一下反斜杠, 以便在跨平台备份恢复时可以顺利找到文件
        self.revertFiles = [item.replace('\\', os.path.sep) for item in self.revertFiles]
        return True

    def rememberRevert(self, filepath):
        patchesDir = self.leeCommon.patches()
        self.revertFiles.append(os.path.relpath(filepath, patchesDir).replace('/', '\\'))

    def saveRevert(self, revertDatabaseSavepath = None):
        if revertDatabaseSavepath is None:
            revertDatabaseSavepath = self.revertDefaultDBPath
        revertDatabaseSavepath = '%s/%s' % (
            self.leeCommon.utility(withmark=False), revertDatabaseSavepath
        )
        if self.leeCommon.isFileExists(revertDatabaseSavepath):
            os.remove(revertDatabaseSavepath)
        os.makedirs(os.path.dirname(revertDatabaseSavepath), exist_ok = True)

        # 标准化处理一下反斜杠, 以便在跨平台备份恢复时可以顺利找到文件
        self.revertFiles = [item.replace('/', '\\') for item in self.revertFiles]

        json.dump({
            'files' : self.revertFiles
        }, open(revertDatabaseSavepath, 'w', encoding = 'utf-8'), indent = 4, ensure_ascii = False)

    def canRevert(self, revertDatabaseLoadpath = None):
        if revertDatabaseLoadpath is None:
            revertDatabaseLoadpath = self.revertDefaultDBPath
        self.loadRevert(revertDatabaseLoadpath)
        return len(self.revertFiles) > 0

    def doRevert(self, revertDatabaseLoadpath = None):
        if revertDatabaseLoadpath is None:
            revertDatabaseLoadpath = self.revertDefaultDBPath
        self.loadRevert(revertDatabaseLoadpath)

        patchesDir = self.leeCommon.patches()

        for relpath in self.revertFiles:
            # replace('\\', os.path.sep) 标准化处理一下反斜杠
            fullpath = os.path.abspath('%s/%s' % (patchesDir, relpath.replace('\\', os.path.sep)))
            if self.leeCommon.isFileExists(fullpath):
                os.remove(fullpath)

        if self.leeCommon.isFileExists(revertDatabaseLoadpath):
            os.remove(revertDatabaseLoadpath)

        self.leeCommon.removeEmptyDirectorys(patchesDir)
