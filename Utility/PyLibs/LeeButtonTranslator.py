# -*- coding: utf-8 -*-

import copy
import glob
import hashlib
import os
import re

from PyLibs import LeeBaseRevert, LeeBaseTranslator, LeeButtonRender


class LeeButtonTranslator(LeeBaseTranslator, LeeBaseRevert):
    def __init__(self):
        LeeBaseTranslator.__init__(self)
        LeeBaseRevert.__init__(self)
        self.leeFileIO = LeeButtonRender()
        self.translateDefaultDBPath = 'Resources/Databases/ButtonTranslate.json'
        self.specifiedClientVer = None
        self.__updateRevertDefaultDBPath()

    def doTranslate(self, specifiedClientVer = None):
        '''
        重写 LeeBaseTranslator 的 doTranslate 方法
        因为翻译按钮时的文件遍历方式与翻译其他单个文件的遍历方式有所不同
        '''
        self.__updateRevertDefaultDBPath(specifiedClientVer)
        leeClientDir = self.leeCommon.client()
        patchesDir = self.leeCommon.patches()
        rePathPattern = self.leeCommon.normPattern(r'^.*?/Patches/.*?/Resource/Original/data/texture/蜡历牢磐其捞胶')
        self.load()
        self.clearRevert()

        # 先确定需要被生成的翻译信息列表（汉化过程实际上是生成按钮图片）
        # 最终存放到 waitingToBuildTranslateInfolist 数组中, 以便后续进行处理
        waitingToBuildTranslateInfolist = []
        for dirpath, _dirnames, filenames in os.walk(patchesDir):
            for filename in filenames:
                fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                if not filename.lower().endswith('.bmp'):
                    continue
                if not re.match(rePathPattern, fullpath, re.I):
                    continue

                relpath = re.search(self.leeCommon.normPattern(r'Original/(.*)$'), fullpath).group(1)
                translateInfo = self.__getTranslateInfo(relpath)
                if not (translateInfo and translateInfo['ButtonText'] and translateInfo['StyleFormat']):
                    continue

                translateInfo['RelativePath'] = relpath
                translateInfo['FullPath'] = fullpath
                translateInfo['ButtonWidth'], translateInfo['ButtonHeight'] = self.leeFileIO.getImageSizeByFilepath(fullpath)
                deepTranslateInfo = copy.deepcopy(translateInfo)
                waitingToBuildTranslateInfolist.append(deepTranslateInfo)

        # 根据汉化信息来逐个生成按钮文件（包括按钮的各个状态）
        btnStateDefine = ['normal', 'hover', 'press', 'disabled']
        for translateInfo in waitingToBuildTranslateInfolist:
            if (specifiedClientVer is not None) and \
               (specifiedClientVer not in translateInfo['FullPath']):
                continue

            resourceDirpath = re.search(
                self.leeCommon.normPattern(r'^(.*)Original/data/texture'),
                translateInfo['FullPath'], re.I
            ).group(1)

            translatedDirpath = resourceDirpath + 'Temporary'
            textureDirpath = '%s/%s' % (
                translatedDirpath, os.path.dirname(translateInfo['RelativePath'])
            )
            os.makedirs(textureDirpath, exist_ok = True)

            _referPostfix, filenameMode, _withDisabled = translateInfo['FilenameMode'].split('#')

            for btnStateIndex, postfix in enumerate(filenameMode.split('|')):
                btnSavePath = '%s/%s%s.bmp' % (textureDirpath, translateInfo['Basename'], postfix)

                print('正在汉化: %s' % os.path.relpath(
                    btnSavePath, leeClientDir
                ).replace('Temporary', 'Original'))

                self.leeFileIO.createButtonBmpFile(
                    translateInfo['StyleFormat'],
                    btnStateDefine[btnStateIndex],
                    translateInfo['ButtonText'],
                    translateInfo['ButtonWidth'],
                    btnSavePath
                )
                self.rememberRevert(btnSavePath)

                print('汉化完毕: %s\r\n' % os.path.relpath(
                    btnSavePath, leeClientDir
                ))

        self.saveRevert()

    def update(self):
        patchesDir = self.leeCommon.patches(withmark=False)
        updTranslateMap = {}

        for dirpath, _dirnames, filenames in os.walk(patchesDir):
            for filename in filenames:
                if not filename.lower().endswith('.bmp'):
                    continue
                if dirpath.lower().find('resource%soriginal' % os.sep) <= 0:
                    continue

                fullpath = '%s/%s' % (dirpath, filename)
                result, realBasename, referPostfix, filenameMode, withDisabled = self.__detectFilemode(fullpath)
                if not result:
                    continue

                relpath = re.search(self.leeCommon.normPattern(r'Original/(.*)$'), fullpath).group(1)
                fullNameMode = '%s#%s#%s' % (referPostfix, filenameMode, withDisabled)
                baseDirectory = (os.path.dirname(relpath).lower() + os.path.sep).replace('\\', '/')
                translateKey = self.__generateKey(baseDirectory, '%s%s' % (realBasename, referPostfix))

                translateItem = {
                    'Directory': baseDirectory,
                    'Basename': realBasename,
                    'FilenameMode': fullNameMode,
                    'StyleFormat': '' if not (translateKey in self.translateMap) else self.translateMap[translateKey]['StyleFormat'],
                    'ButtonText': '' if not (translateKey in self.translateMap) else self.translateMap[translateKey]['ButtonText']
                }

                updTranslateMap[translateKey] = translateItem

        self.translateMap.clear()
        self.translateMap = updTranslateMap

    def doRevert(self, specifiedClientVer = None):
        if specifiedClientVer == 'AllVersions':
            scriptDir = self.leeCommon.utility(withmark=False)
            for filepath in glob.glob('%s/Resources/Databases/RevertData/LeeButtonRevert*.json' % scriptDir):
                relpath = os.path.relpath(filepath, scriptDir)
                LeeBaseRevert.doRevert(self, relpath)
        else:
            self.__updateRevertDefaultDBPath(specifiedClientVer)
            LeeBaseRevert.doRevert(self)

    def __generateKey(self, dirpath, filename):
        hashstr = '%s%s' % (dirpath.replace('\\', '/'), filename)
        return hashlib.md5(hashstr.lower().encode(encoding='utf-8')).hexdigest()

    def __getTranslateInfo(self, relpath):
        dirname = os.path.normpath(os.path.dirname(relpath).lower()) + os.path.sep
        filename = (os.path.splitext(os.path.basename(relpath))[0]).lower()
        translateKey = self.__generateKey(dirname, filename)

        if translateKey not in self.translateMap:
            return None
        return self.translateMap[translateKey]

    def __updateRevertDefaultDBPath(self, specifiedClientVer = None):
        if specifiedClientVer is not None:
            self.specifiedClientVer = specifiedClientVer
        self.revertDefaultDBPath = 'Resources/Databases/RevertData/LeeButtonRevert%s.json' % ('' if self.specifiedClientVer is None else '_%s' % self.specifiedClientVer)

    def __detectFilemode(self, filepath):
        if not filepath.lower().endswith('.bmp'):
            return False, None, None, None, None

        # demo_out.bmp | demo_over.bmp | demo_press.bmp | demo_disable.bmp
        # demo_out.bmp | demo_over.bmp | demo_press.bmp
        # demo.bmp | demo_a.bmp | demo_b.bmp | demo_c.bmp
        # demo.bmp | demo_a.bmp | demo_b.bmp | demo_dis.bmp
        # demo.bmp | demo_a.bmp | demo_b.bmp
        # demo_a.bmp | demo_b.bmp | demo_c.bmp | demo_d.bmp
        # demoa.bmp | demob.bmp

        fileNameModes = [
            { 'base': '_over', 'refer': ['_out', '_press'], 'block': [''], 'disable': '_disable', 'n': '_out|_over|_press', 'd': '_out|_over|_press|_disable' },
            { 'base': '_a', 'refer': ['', '_b'], 'block': ['_c'], 'disable': '_dis', 'n': '|_a|_b', 'd': '|_a|_b|_dis' },
            { 'base': '_a', 'refer': ['', '_b'], 'block': ['_dis'], 'disable': '_c', 'n': '|_a|_b', 'd': '|_a|_b|_c' },
            { 'base': '_b', 'refer': ['_a', '_c'], 'block': [''], 'disable': '_d', 'n': '_a|_b|_c', 'd': '_a|_b|_c|_d' },
            { 'base': 'b', 'refer': ['a', 'c'], 'block': [''], 'disable': '', 'n': 'a|b|c', 'd': ''},
            { 'base': 'b', 'refer': ['a'], 'block': ['c'], 'disable': '', 'n': 'a|b', 'd': ''}
        ]

        dirpath = os.path.dirname(filepath)
        fullBasename = (os.path.splitext(os.path.basename(filepath))[0]).lower()
        realBasename = referPostfix = finallyFilenameMode = ''
        withDisabled = isValid = False

        for fileNameMode in fileNameModes:
            if fullBasename.endswith(fileNameMode['base']):
                isValid = True
        if not isValid:
            return False, None, None, None, None

        for fileNameMode in fileNameModes:
            realBasename = fullBasename[:len(fullBasename) - len(fileNameMode['base'])]
            referPostfix = fileNameMode['base']

            referPass = True
            for refer in fileNameMode['refer']:
                if not self.leeCommon.isFileExists('%s/%s%s.bmp' % (dirpath, realBasename, refer)):
                    referPass = False
            if not referPass:
                continue

            blockPass = True
            for block in fileNameMode['block']:
                if self.leeCommon.isFileExists('%s/%s%s.bmp' % (dirpath, realBasename, block)):
                    blockPass = False
            if not blockPass:
                continue

            withDisabled = self.leeCommon.isFileExists('%s/%s%s.bmp' % (dirpath, realBasename, fileNameMode['disable']))
            finallyFilenameMode = fileNameMode['d'] if withDisabled else fileNameMode['n']
            break

        if not finallyFilenameMode:
            return False, None, None, None, None

        return True, realBasename, referPostfix, finallyFilenameMode, withDisabled
