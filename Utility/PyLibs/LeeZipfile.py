# -*- coding: utf-8 -*-

import os
import zipfile

class LeeZipfile:
    def __init__(self):
        pass

    def zip(self, sourceDirpath, zipSavePath, topLevelDirName = None, stepCallback = None):
        if not (sourceDirpath.endswith('\\') or sourceDirpath.endswith('/')):
            sourceDirpath = '%s%s' % (sourceDirpath, os.path.sep)

        sourceParentDir = os.path.abspath('%s..%s' % (sourceDirpath, os.path.sep))

        zfile = zipfile.ZipFile(zipSavePath, 'w', zipfile.ZIP_DEFLATED)
        for dirpath, _dirnames, filenames in os.walk(sourceDirpath):
            for filename in filenames:
                fullpath = os.path.join(dirpath, filename)

                # 用于保存到 zip 文件中的相对路径
                relSavedPath = fullpath[len(sourceParentDir) + 1:]

                # 先剔除 sourceDirpath 末尾的斜杠
                sourceDirpathWithoutBackslashed = sourceDirpath if not (sourceDirpath.endswith('\\') or sourceDirpath.endswith('/')) else sourceDirpath[:-1]

                # 只取最后一段的目录名, 如: LeeClient_Release_20181002_121313
                dirname = os.path.basename(sourceDirpathWithoutBackslashed)

                # 如果需要处理保存到 ZIP 中的第一级目录名的话, 对 relSavedPath 进行处理即可
                if topLevelDirName is not None:
                    relSavedPath = '%s%s' % (topLevelDirName, relSavedPath[len(relSavedPath.split(os.path.sep)[0]):])
                    relDisplayName = relSavedPath[len(topLevelDirName) + 1:]
                else:
                    relDisplayName = relSavedPath[len(dirname) + 1:]

                print('正在压缩: %s' % relDisplayName)
                zfile.write(fullpath, relSavedPath)
        zfile.close()

        return True

    def unzip(self, zipFilepath, targetDirpath, stepCallback = None):
        pass
