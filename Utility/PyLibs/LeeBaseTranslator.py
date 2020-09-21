# -*- coding: utf-8 -*-

import json
import os
import re

from PyLibs import LeeCommon


class LeeBaseTranslator:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.leeFileIO = None
        self.translateDefaultDBPath = None
        self.translateMap = {}
        self.reSrcPathPattern = None
        self.reDstPathPattern = None

    def clear(self):
        self.translateMap.clear()

    def load(self, translateDBPath = None):
        self.clear()
        if translateDBPath is None:
            translateDBPath = self.translateDefaultDBPath
        translatePath = '%s/%s' % (self.leeCommon.utility(withmark=False), translateDBPath)
        if not self.leeCommon.isFileExists(translatePath):
            return False
        try:
            self.translateMap = json.load(open(translatePath, 'r', encoding = 'utf-8'))
            return True
        except FileNotFoundError as _err:
            print('很抱歉, 无法打开翻译数据库文件: %s' % translatePath)
            raise

    def save(self, translateDBPath = None):
        if translateDBPath is None:
            translateDBPath = self.translateDefaultDBPath
        savePath = self.leeCommon.utility(translateDBPath)
        json.dump(
            self.translateMap, open(savePath, 'w', encoding = 'utf-8', newline = '\n'),
            indent = 4, ensure_ascii = False
        )
        return True

    def doTranslate(self, specifiedClientVer = None):
        leeClientDir = self.leeCommon.client()
        patchesDir = self.leeCommon.patches()

        if self.reSrcPathPattern is None:
            return False
        if self.reDstPathPattern is None:
            return False

        sourceFilepathList = []
        for dirpath, _dirnames, filenames in os.walk(patchesDir):
            for filename in filenames:
                fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                if not re.match(self.reSrcPathPattern, fullpath, re.I):
                    continue
                sourceFilepathList.append(fullpath)

        self.load()

        for sourceFilepath in sourceFilepathList:
            if (specifiedClientVer is not None) and (specifiedClientVer not in sourceFilepath):
                continue
            print('正在汉化, 请稍候: %s' % os.path.relpath(sourceFilepath, leeClientDir))
            match = re.search(
                self.reDstPathPattern, sourceFilepath, re.MULTILINE | re.IGNORECASE | re.DOTALL
            )
            if match is None:
                self.leeCommon.exitWithMessage('无法确定翻译后的文件的存放位置, 程序终止')
            destinationPath = '%s/Temporary/%s' % (match.group(1), match.group(2))
            self.translate(sourceFilepath, destinationPath)
            print('汉化完毕, 保存到: %s\r\n' % os.path.relpath(destinationPath, leeClientDir))

        return True

    def translate(self, srcFilepath, dstFilepath):
        pass
