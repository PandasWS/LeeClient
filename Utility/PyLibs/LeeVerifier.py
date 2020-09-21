# -*- coding: utf-8 -*-

import glob
import os
import re
import struct
import time
import timeit

from PyLibs import LeeCommon, LeeIteminfoLua

class LeeStructParser:
    '''
    这个操作类不对外开放, 仅在本文件中被 LeeVerifier 使用
    它负责将各种不同文件格式中所需要的图档路径信息提取出来, 并以数组方式返回
    '''
    def __init__(self):
        self.leeCommon = LeeCommon()

    def __bytesToString(self, bytesArray, targetCode = 'gbk'):
        '''
        将以 0 结尾的 bytes 数组转成字符串对象

        Args:
            bytesArray: 以 0 结尾的 bytes 数组
            targetCode: 转换成功之后的字符串编码, 默认用 gbk 编码

        Returns:
            转换后的字符串
        '''
        zeroEndBytes = 0
        for x in range(len(bytesArray)):
            zeroEndBytes = x
            if bytesArray[zeroEndBytes] == 0:
                break
        asciiString = bytesArray.decode('latin1')[:zeroEndBytes]
        return asciiString.encode('latin1').decode(targetCode)

    def __readFormatVersionInfo(self, f):
        '''
        根据打开的文件对象获取其版本信息
        直接读取接下来的 2 个字节来获得版本信息, 要求指针紧跟在 Magic Bytes 后面

        Args:
            f: 已经打开的文件对象 (RSW 或 RSM 文件)

        Returns:
            此函数包括三个返回值, 需要使用多个变量来接收函数返回的内容

            Major: 主版本号
            Minor: 子版本号
            Version: 2 个字节连在一起的版本号数值
        '''
        Major, Minor = struct.unpack("2b", f.read(struct.calcsize("2b")))
        f.seek(-2, 1)
        Version = struct.unpack("1h", f.read(struct.calcsize("1h")))[0]
        # ShowDebug('Major %d | Minor %d | Version %d' % (Major, Minor, Version))
        return Major, Minor, Version

    def parseGndFile(self, gndfilepath):
        '''
        读取 GND 文件, 并获取它所有相关的贴图地址
        读取到的贴图地址相对于 data/texture/ 目录, 如: data/texture/BACKSIDE.BMP

        Returns:
            此函数包括两个返回值, 需要使用多个变量来接收函数返回的内容

            result: Boolean 执行成功与否
            texturePathList: List 保存着贴图文件路径的数组, 相对于 data/texture/ 目录
        '''
        if not self.leeCommon.isFileExists(gndfilepath):
            print('读取 Gnd 文件失败, 文件不存在: %s' % gndfilepath)
            return False, None

        try:
            gndfile = open(gndfilepath, "rb")
            gndfile.seek(len(b'GRGN\x01\x07')) # Magic Bytes

            _Width, _Height, _Ratio, TextureCount, TextureSize = struct.unpack("5I", gndfile.read(struct.calcsize("5I")))
            # ShowDebug("parseGnd_GetTexturePathList: Width %d | Height %d | Ratio %d | TextureCount %d | TextureSize %d" % (_Width, _Height, _Ratio, TextureCount, TextureSize))

            texturePathList = []
            for _i in range(TextureCount):
                fmt = "%ds" % TextureSize
                TexturePath = struct.unpack(fmt, gndfile.read(struct.calcsize(fmt)))[0]
                texturePathList.append(self.__bytesToString(TexturePath))
                # print(self.__bytesToString(TexturePath))

            gndfile.close()
        except Exception as _err:
            print('处理 gnd 文件时出错了: %s' % gndfilepath)
            raise

        return True, texturePathList

    def parseRswFile(self, rswfilepath):
        '''
        读取 RSW 文件, 并获取它所有相关的 RSM 模型地址
        读取到的模型地址相对于 data/model/ 目录, 如: data/model/malaya/龋荐唱公03.rsm

        Args:
            rswfilepath: RSW 文件的路径

        Returns:
            此函数包括两个返回值, 需要使用多个变量来接收函数返回的内容

            result: Boolean 执行成功与否
            modelPathList: List 保存着 Rsm 模型文件路径的数组, 相对于 data/model/ 目录
        '''
        if not self.leeCommon.isFileExists(rswfilepath):
            print('读取 Rsw 文件失败, 文件不存在: %s' % rswfilepath)
            return False, None

        rswfile = open(rswfilepath, 'rb')
        rswfile.seek(len(b'GRSW'))     # Magic Bytes
        fmtMajor, fmtMinor, _Version = self.__readFormatVersionInfo(rswfile)

        def isCompatible(major, minor):
            return fmtMajor > major or (fmtMajor == major and fmtMinor >= minor)

        _IniFilename = rswfile.read(struct.calcsize("40s"))
        _GndFilename = rswfile.read(struct.calcsize("40s"))
        _GatFilename = '' if not isCompatible(1, 4) else rswfile.read(struct.calcsize("40s"))
        _ScrFilename = rswfile.read(struct.calcsize("40s"))

        # ==================== WaterData ====================

        _Level = 0.0
        _Type = 0
        _WaveHeight = 0.2
        _WaveSpeed = 2.0
        _WavePitch = 50.0
        _AnimSpeed = 3

        if isCompatible(1, 3):
            _Level = struct.unpack("1f", rswfile.read(struct.calcsize("1f")))[0]

        if isCompatible(1, 8):
            _Type, _WaveHeight, _WaveSpeed, _WavePitch = struct.unpack("1I3f", rswfile.read(struct.calcsize("1I3f")))

        if isCompatible(1, 9):
            _AnimSpeed = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]

        # ShowInfo('WaterData: Level %f | Type %d | WaveHeight %f | WaveSpeed %f | WavePitch %f | AnimSpeed %d' %
        #     (_Level, _Type, _WaveHeight, _WaveSpeed, _WavePitch, _AnimSpeed))

        # ==================== LightData ====================

        _Longitude = 45
        _Latitude = 45
        _DiffuseColor = [1.0, 1.0, 1.0]
        _AmbientColor = [0.3, 0.3, 0.3]
        _Opacity = 1.0

        if isCompatible(1, 5):
            _Longitude, _Latitude = struct.unpack("2I", rswfile.read(struct.calcsize("2I")))
            _DiffuseColor[0], _DiffuseColor[1], _DiffuseColor[2] = struct.unpack("3f", rswfile.read(struct.calcsize("3f")))
            _AmbientColor[0], _AmbientColor[1], _AmbientColor[2] = struct.unpack("3f", rswfile.read(struct.calcsize("3f")))

        if isCompatible(1, 7):
            _Opacity = struct.unpack("1f", rswfile.read(struct.calcsize("1f")))[0]

        # ShowInfo('LightData: Longitude %d | Latitude %d | Opacity %f' % (_Longitude, _Latitude, _Opacity))
        # ShowInfo('LightData: DiffuseColorRed %f | DiffuseColorGreen %f | DiffuseColorBlue %f' % (_DiffuseColor[0], _DiffuseColor[1], _DiffuseColor[2]))
        # ShowInfo('LightData: AmbientColorRed %f | AmbientColorGreen %f | AmbientColorBlue %f' % (_AmbientColor[0], _AmbientColor[1], _AmbientColor[2]))

        # ==================== GroundData ====================

        _Top = -500
        _Bottom = 500
        _Left = -500
        _Right = 500

        if isCompatible(1, 6):
            _Top, _Bottom, _Left, _Right = struct.unpack("4I", rswfile.read(struct.calcsize("4I")))

        # ShowInfo('GroundData: Top %d | Bottom %d | Left %d | Right %d' % (_Top, _Bottom, _Left, _Right))

        # ==================== MapObject ====================

        objectCount = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]

        modelPathList = []
        for _i in range(objectCount):
            objectType = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]

            if objectType == 1: # Model - 关注会加载的 RSM 模型
                if isCompatible(1, 3):
                    _ModelName = self.__bytesToString(struct.unpack("40s", rswfile.read(struct.calcsize("40s")))[0])
                    _AnimationType = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]
                    _AnimationSpeed = struct.unpack("1f", rswfile.read(struct.calcsize("1f")))[0]
                    _BlockType = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]

                modelFilename = self.__bytesToString(struct.unpack("80s", rswfile.read(struct.calcsize("80s")))[0])
                _ModelNodeName = self.__bytesToString(struct.unpack("80s", rswfile.read(struct.calcsize("80s")))[0])

                modelPathList.append(modelFilename)
                # ShowInfo("[RSM Model] Path = %s" % modelFilename)

        rswfile.close()
        return True, modelPathList

    def parseRsmFile(self, rsmfilepath):
        '''
        读取 RSM 文件, 并获取它所有相关的贴图地址
        读取到的贴图地址相对于 data/texture/ 目录, 如: data/texture/eclage/ecl_obj15.bmp

        Args:
            rsmfilepath: RSM 文件的路径

        Returns:
            此函数包括两个返回值, 需要使用多个变量来接收函数返回的内容

            result: Boolean 执行成功与否
            texturePathList: List 保存着贴图文件路径的数组, 相对于 data/texture/ 目录
        '''

        def isCompatible(major, minor):
            return (
                fmtMajor > major or (fmtMajor == major and fmtMinor >= minor)
            )

        try:
            if not self.leeCommon.isFileExists(rsmfilepath):
                print("读取 Rsm 文件失败, 文件不存在: %s" % rsmfilepath)
                return False, None

            rsmfile = open(rsmfilepath, "rb")
            rsmfile.seek(len(b'GRSM')) # Magic Bytes
            fmtMajor, fmtMinor, _Version = self.__readFormatVersionInfo(rsmfile)

            _AnimationLength, _ShadeType = struct.unpack("2I", rsmfile.read(struct.calcsize("2I")))
            _Alpha = 0 if not isCompatible(1, 4) else struct.unpack("1b", rsmfile.read(struct.calcsize("1b")))[0]
            _unknow = struct.unpack("16s", rsmfile.read(struct.calcsize("16s")))[0]
            textureCount = struct.unpack("1I", rsmfile.read(struct.calcsize("1I")))[0]

            texturePathList = []
            for _i in range(textureCount):
                texturePath = self.__bytesToString(struct.unpack("40s", rsmfile.read(struct.calcsize("40s")))[0])
                texturePathList.append(texturePath)

            rsmfile.close()
        except Exception as _err:
            print('处理 rsm 文件时出错了: %s' % rsmfilepath)
            raise

        return True, texturePathList

    def parseStrFile(self, strfilepath):
        '''
        读取 STR 文件, 并获取它所有相关的贴图地址
        读取到的贴图地址相对于 STR 文件所在目录, 如: data/texture/effect/magnus/ff.bmp

        Args:
            strfilepath: STR 文件的路径

        Returns:
            此函数包括两个返回值, 需要使用多个变量来接收函数返回的内容

            result: Boolean 执行成功与否
            texturePathList: List 保存着贴图文件路径的数组, 相对于 STR 文件所在目录
        '''
        if not self.leeCommon.isFileExists(strfilepath):
            print("读取 Str 文件失败, 文件不存在: %s" % strfilepath)
            return False, None

        strfile = open(strfilepath, "rb")
        strfile.seek(len(b'STRM')) # Magic Bytes
        _Version, _FPS, _frameCount, layerCount, _Reserved = struct.unpack("4I16s", strfile.read(struct.calcsize("4I16s")))

        texturePathList = []
        for _i in range(layerCount):
            textureCount = struct.unpack("1I", strfile.read(struct.calcsize("1I")))[0]
            for _k in range(textureCount):
                textureName = self.__bytesToString(struct.unpack("128s", strfile.read(struct.calcsize("128s")))[0])
                texturePathList.append(textureName)

            keyFrameCount = struct.unpack("1I", strfile.read(struct.calcsize("1I")))[0]
            for _k in range(keyFrameCount):
                struct.unpack("2I19f1I6f3I", strfile.read(struct.calcsize("2I19f1I6f3I")))

        strfile.close()
        return True, texturePathList

    def parseIteminfo(self, iteminfofilepath):
        '''
        读取 iteminfo 文件, 并获取它所有相关的贴图和 ACT&SPR 图档地址

        Args:
            strfilepath: iteminfo 文件的路径

        Returns:
            此函数包括三个返回值, 需要使用多个变量来接收函数返回的内容

            result: Boolean 执行成功与否
            texturePathList: List 保存着贴图文件路径的数组, 相对于 data/texture/ 目录
            spritePathList: List 保存着 ACT&SPR 图档路径的数组, 相对于 data/sprite/ 目录
        '''
        if not self.leeCommon.isFileExists(iteminfofilepath):
            print("读取 Iteminfo 文件失败, 文件不存在: %s" % iteminfofilepath)
            return False, None, None

        itemLua = LeeIteminfoLua()
        itemLua.load(iteminfofilepath)

        texturePathList = []
        spritePathList = []

        for itemID in itemLua.items():
            unidentifiedResourceName = itemLua.getItemAttribute(itemID, 'unidentifiedResourceName')
            if unidentifiedResourceName.strip() != '':
                texturePathList.append('蜡历牢磐其捞胶/collection/%s.bmp' % unidentifiedResourceName)
                texturePathList.append('蜡历牢磐其捞胶/item/%s.bmp' % unidentifiedResourceName)
                spritePathList.append('酒捞袍/%s.spr' % unidentifiedResourceName)
                spritePathList.append('酒捞袍/%s.act' % unidentifiedResourceName)

            identifiedResourceName = itemLua.getItemAttribute(itemID, 'identifiedResourceName')
            if identifiedResourceName.strip() != '':
                texturePathList.append('蜡历牢磐其捞胶/collection/%s.bmp' % identifiedResourceName)
                texturePathList.append('蜡历牢磐其捞胶/item/%s.bmp' % identifiedResourceName)
                spritePathList.append('酒捞袍/%s.spr' % identifiedResourceName)
                spritePathList.append('酒捞袍/%s.act' % identifiedResourceName)

        texturePathList = list(set(texturePathList))
        spritePathList = list(set(spritePathList))

        return True, texturePathList, spritePathList


class LeeVerifier:
    '''
    此操作类用于验证客户端的文件是否完整
    '''
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.leeParser = LeeStructParser()
        self.textureDirs = ['data/texture']
        self.modelDirs = ['data/model']
        self.spriteDirs = ['data/sprite']

        self.reportInfo = []
        self.reportStartTime = 0    # 用于记录当前检测项目的启动时间
        self.reportFileCount = 0    # 记录本次检测项目中, 丢失了资源的文件数量
        self.reportMissCount = 0    # 记录本次检测项目中, 累计丢失的资源文件数量

    def __verifyGnd(self, gndfilepath, priorityDataDir = None):
        result, texturePathList = self.leeParser.parseGndFile(gndfilepath)
        if not result:
            return None, None

        missTexturePathList = []
        existsTexturePathList = []
        leeClientDir = self.leeCommon.client(withmark=False)

        for texturePath in texturePathList:
            if priorityDataDir:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/texture/%s' % (leeClientDir, priorityDataDir, texturePath)
                )
                # print(fullpath)
                if self.leeCommon.isFileExists(fullpath):
                    existsTexturePathList.append(fullpath)
                    continue
            for textureDir in self.textureDirs:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/%s' % (leeClientDir, textureDir, texturePath)
                )
                if self.leeCommon.isFileExists(fullpath):
                    existsTexturePathList.append(fullpath)
                    break
            else:
                # print(texturePath)
                missTexturePathList.append(fullpath)

        return existsTexturePathList, missTexturePathList

    def __verifyRsw(self, rswfilepath, priorityDataDir = None):
        result, modelPathList = self.leeParser.parseRswFile(rswfilepath)
        if not result:
            return None, None

        missModelPathList = []
        existsModelPathList = []
        leeClientDir = self.leeCommon.client(withmark=False)

        for modelPath in modelPathList:
            if priorityDataDir:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/model/%s' % (leeClientDir, priorityDataDir, modelPath)
                )
                # print(fullpath)
                if self.leeCommon.isFileExists(fullpath):
                    existsModelPathList.append(fullpath)
                    continue
            for modelDir in self.modelDirs:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/%s' % (leeClientDir, modelDir, modelPath)
                )
                if self.leeCommon.isFileExists(fullpath):
                    # print('existsModelPathList: %s' % modelPath)
                    existsModelPathList.append(fullpath)
                    break
            else:
                # print('missModelPathList: %s' % modelPath)
                missModelPathList.append(fullpath)

        return existsModelPathList, missModelPathList

    def __verifyRsm(self, rsmfilepath, priorityDataDir = None):
        result, texturePathList = self.leeParser.parseRsmFile(rsmfilepath)
        if not result:
            return None, None

        missTexturePathList = []
        existsTexturePathList = []
        leeClientDir = self.leeCommon.client(withmark=False)

        for texturePath in texturePathList:
            if priorityDataDir:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/texture/%s' % (leeClientDir, priorityDataDir, texturePath)
                )
                # print(fullpath)
                if self.leeCommon.isFileExists(fullpath):
                    existsTexturePathList.append(fullpath)
                    continue
            for textureDir in self.textureDirs:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/%s' % (leeClientDir, textureDir, texturePath)
                )
                if self.leeCommon.isFileExists(fullpath):
                    existsTexturePathList.append(fullpath)
                    break
            else:
                # print(texturePath)
                missTexturePathList.append(fullpath)

        return existsTexturePathList, missTexturePathList

    def __verifyStr(self, strfilepath, priorityDataDir = None):
        result, texturePathList = self.leeParser.parseStrFile(strfilepath)
        if not result:
            return None, None
        texturePathList = list(set(texturePathList))    # 文件名消重(str解析出来重复的图档文件名太多)

        missTexturePathList = []
        existsTexturePathList = []

        leeClientDir = self.leeCommon.client(withmark=False)
        leeClientCommonDataDir = '%s/data' % leeClientDir
        isPatchStrFile = leeClientCommonDataDir.lower() not in strfilepath.lower()

        dataPostion = strfilepath.lower().rfind('data/')
        strfileDirBaseonData = os.path.dirname(strfilepath[dataPostion:])

        if priorityDataDir is not None and priorityDataDir.lower().endswith('/data'):
            priorityDataDir = priorityDataDir[:-len('/data')]

        for texturePath in texturePathList:
            if isPatchStrFile and priorityDataDir is not None:
                # leeClientDir + priorityDataDir + strfileDirBaseonData + 文件名
                fullpath = self.leeCommon.normpath('%s/%s/%s/%s' % (
                    leeClientDir, priorityDataDir, strfileDirBaseonData, texturePath
                ))
                if self.leeCommon.isFileExists(fullpath):
                    existsTexturePathList.append(fullpath)
                    continue

                # leeClientDir + priorityDataDir + self.textureDirs + '/effect' + 文件名
                isFound = False
                for textureDir in self.textureDirs:
                    fullpath = self.leeCommon.normpath('%s/%s/%s/effect/%s' % (
                        leeClientDir, priorityDataDir, textureDir, texturePath
                    ))
                    if self.leeCommon.isFileExists(fullpath):
                        existsTexturePathList.append(fullpath)
                        isFound = True
                        break
                if isFound:
                    continue

            # leeClientDir + strfileDirBaseonData + 文件名
            fullpath = self.leeCommon.normpath('%s/%s/%s' % (
                leeClientDir, strfileDirBaseonData, texturePath
            ))
            if self.leeCommon.isFileExists(fullpath):
                existsTexturePathList.append(fullpath)
                continue

            # leeClientDir + self.textureDirs + '/effect'
            isFound = False
            for textureDir in self.textureDirs:
                fullpath = self.leeCommon.normpath('%s/%s/effect/%s' % (
                    leeClientDir, textureDir, texturePath
                ))
                if self.leeCommon.isFileExists(fullpath):
                    existsTexturePathList.append(fullpath)
                    isFound = True
                    break
            if not isFound:
                missTexturePathList.append(fullpath)

        return existsTexturePathList, missTexturePathList

    def __verifyIteminfo(self, iteminfofilepath, priorityDataDir = None):
        result, texturePathList, spritePathList = self.leeParser.parseIteminfo(iteminfofilepath)
        if not result:
            return None, None

        leeClientDir = self.leeCommon.client(withmark=False)

        missTexturePathList = []
        for texturePath in texturePathList:
            if priorityDataDir:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/texture/%s' % (leeClientDir, priorityDataDir, texturePath)
                )
                # print(fullpath)
                if self.leeCommon.isFileExists(fullpath):
                    continue
            for textureDir in self.textureDirs:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/%s' % (leeClientDir, textureDir, texturePath)
                )
                if self.leeCommon.isFileExists(fullpath):
                    break
            else:
                # print('missTexturePathList: %s' % texturePath)
                missTexturePathList.append(fullpath)

        missSpritePathList = []
        for spritePath in spritePathList:
            if priorityDataDir:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/sprite/%s' % (leeClientDir, priorityDataDir, spritePath)
                )
                # print(fullpath)
                if self.leeCommon.isFileExists(fullpath):
                    continue
            for spriteDir in self.spriteDirs:
                fullpath = self.leeCommon.normpath(
                    '%s/%s/%s' % (leeClientDir, spriteDir, spritePath)
                )
                if self.leeCommon.isFileExists(fullpath):
                    break
            else:
                # print('missSpritePathList: %s' % spritePath)
                missSpritePathList.append(fullpath)

        return missTexturePathList, missSpritePathList

    def __resetReport(self):
        self.reportInfo.clear()

    def __appendReportMessage(self, mesType, message):
        if mesType.lower() == 'header':
            self.reportInfo.append('=============================================')
            self.reportInfo.append(message)
            self.reportInfo.append('=============================================')
            # 启动一个计时器和一个 __appendReportData 计数器
            self.reportFileCount = self.reportMissCount = 0
            self.reportStartTime = timeit.default_timer()
        elif mesType.lower() == 'footer':
            # 总结耗时以及写入一些统计信息
            spendTime = timeit.default_timer() - self.reportStartTime
            resourceInfo = '非常好, 此项目无任何文件缺失!' if self.reportFileCount == 0 else '有 %d 个文件共计缺失 %d 个资源' % (
                self.reportFileCount, self.reportMissCount
            )
            self.reportInfo.append('%s / 耗时: %.2f 秒' % (resourceInfo, spendTime))
            self.reportInfo.append('=============================================')
            self.reportInfo.append('')
            self.reportInfo.append('')

    def __appendReportData(self, sourceFile, missFilesList):
        leeClientDir = self.leeCommon.client()
        relSourceFile = os.path.relpath(sourceFile, leeClientDir)

        missFileCount = 0
        for fileslist in missFilesList:
            if not fileslist or not fileslist['files']:
                continue
            missFileCount = missFileCount + len(fileslist['files'])

        if not missFileCount:
            return

        self.reportInfo.append(
            '>>> %s (缺失 %d 个文件)' % (
                relSourceFile, missFileCount
            )
        )

        for fileslist in missFilesList:
            if not fileslist:
                continue
            for missFile in fileslist['files']:
                self.reportInfo.append(
                    '    缺失%s: %s' % (
                        fileslist['name'],
                        os.path.relpath(missFile, leeClientDir)
                    )
                )

        self.reportInfo.append('')
        self.reportFileCount = self.reportFileCount + 1
        self.reportMissCount = self.reportMissCount + missFileCount

    def __saveReport(self):
        reportTime = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        savePath = '%s/Reports/VerifyRpt_%s.txt' % (
            self.leeCommon.utility(withmark=False), reportTime
        )
        savePath = self.leeCommon.normpath(savePath)
        os.makedirs(os.path.dirname(savePath), exist_ok = True)

        rptfile = open(savePath, 'w+', encoding = 'utf-8', newline = '')
        rptfile.write('\r\n'.join(self.reportInfo))

        print('校验结果已保存到 : %s' % os.path.relpath(savePath, self.leeCommon.client()))

    def __getFilesInfo(self, glob_or_re, reWalkDir, pattern, baseDir_or_reGroupID,
                       baseDir_append = None):
        filesinfo = []

        if glob_or_re == 'glob':
            for filepath in glob.glob(pattern):
                datadir = baseDir_or_reGroupID
                if baseDir_append:
                    datadir = datadir + baseDir_append
                filesinfo.append({
                    'datadir' : datadir,
                    'filepath': filepath
                })
        elif glob_or_re == 're':
            pattern = self.leeCommon.normPattern(pattern)
            for dirpath, _dirnames, filenames in os.walk(reWalkDir):
                for filename in filenames:
                    fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                    matches = re.match(pattern, fullpath, re.I)
                    if not matches:
                        continue

                    datadir = None
                    if baseDir_or_reGroupID is not None:
                        datadir = matches.group(baseDir_or_reGroupID)
                    if datadir and baseDir_append:
                        datadir = datadir + baseDir_append

                    filesinfo.append({
                        'datadir' : datadir,
                        'filepath': fullpath
                    })
        else:
            self.leeCommon.exitWithMessage('指定的 glob_or_re 的值无效, 程序终止')

        return filesinfo

    def __subVerifier(self, filesinfo, parsefunc, subject, returnPathListIndex = None,
                      reportMissInfo = None):

        if filesinfo is None:
            return None

        self.__appendReportMessage('header', '%s - 共 %d 个' % (subject, len(filesinfo)))
        print('正在%s - 共 %d 个' % (subject, len(filesinfo)))

        if filesinfo and not isinstance(filesinfo[0], dict):
            restructFilesinfo = []
            for filepath in filesinfo:
                restructFilesinfo.append({
                    'filepath' : filepath,
                    'datadir' : None
                })
            filesinfo = restructFilesinfo

        for fileinfo in filesinfo:
            filepath = fileinfo['filepath']
            datadir = fileinfo['datadir']
            parsefuncResult = parsefunc(filepath, datadir)

            if not reportMissInfo:
                continue

            needReportFilelist = []
            for missinfo in reportMissInfo:
                needReportFilelist.append({
                    'name' : missinfo['name'],
                    'files' : parsefuncResult[missinfo['resultIndex']]
                })

            self.__appendReportData(filepath, needReportFilelist)
        self.__appendReportMessage('footer', '')

        if returnPathListIndex is None:
            return None
        return parsefuncResult[returnPathListIndex]

    def __globalResourceVerifier(self):
        leeClientDir = self.leeCommon.client(withmark=False)

        # 校验公用目录中地图文件所需的图档文件
        # =====================================================================

        # 校验地图的 gnd 文件（纹理层）

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 'glob',
                reWalkDir = None,
                pattern = '%s/data/*.gnd' % leeClientDir,
                baseDir_or_reGroupID = None,
                baseDir_append = None
            ),
            parsefunc = self.__verifyGnd,
            subject = '校验通用资源目录中的 gnd 文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : '地表贴图', 'resultIndex' : 1 }
            ]
        )

        # 校验地图的 rsw 文件（模型层）

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 'glob',
                reWalkDir = None,
                pattern = '%s/data/*.rsw' % leeClientDir,
                baseDir_or_reGroupID = None,
                baseDir_append = None
            ),
            parsefunc = self.__verifyRsw,
            subject = '校验通用资源目录中的 rsw 文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : 'RSM模型文件', 'resultIndex' : 1 }
            ]
        )

        # 校验地图中 rsm 模型文件的贴图

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 're',
                reWalkDir = '%s/data' % leeClientDir,
                pattern = r'^.*?/data/.*?\.(rsm)',
                baseDir_or_reGroupID = None,
                baseDir_append = None
            ),
            parsefunc = self.__verifyRsm,
            subject = '校验通用资源目录中的 rsm 模型的贴图文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : 'RSM模型文件的贴图文件', 'resultIndex' : 1 }
            ]
        )

        # 校验公用目录中动画效果索引文件 str 中所需的贴图
        # =====================================================================

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 're',
                reWalkDir = '%s/data' % leeClientDir,
                pattern = r'^.*?/data/.*?\.(str)',
                baseDir_or_reGroupID = None,
                baseDir_append = None
            ),
            parsefunc = self.__verifyStr,
            subject = '校验通用资源目录中 str 文档所需的贴图文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : '动画索引贴图文件', 'resultIndex' : 1 }
            ]
        )

        # 校验各个补丁目录中 Iteminfo 文件中所需的贴图
        # =====================================================================

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 're',
                reWalkDir = '%s/System' % leeClientDir,
                pattern = r'^.*?/iteminfo.*?\.(lua|lub)',
                baseDir_or_reGroupID = None,
                baseDir_append = None
            ),
            parsefunc = self.__verifyIteminfo,
            subject = '校验通用资源目录中的 iteminfo 道具描述文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : '道具图片', 'resultIndex' : 0 },
                { 'name' : '掉落和拖动时的图档', 'resultIndex' : 1 }
            ]
        )

    def __patchesResourceVerifier(self):
        patchesDir = self.leeCommon.patches()

        # 校验各个补丁目录中地图文件所需的图档文件
        # =====================================================================

        # 校验地图的 gnd 文件（纹理层）

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 're',
                reWalkDir = patchesDir,
                pattern = r'^.*?/(Utility/Patches/.*?/Resource/Original/data)/.*?\.(gnd)',
                baseDir_or_reGroupID = 1,
                baseDir_append = None
            ),
            parsefunc = self.__verifyGnd,
            subject = '校验各补丁目录中的 gnd 文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : '地表贴图', 'resultIndex' : 1 }
            ]
        )

        # 校验地图的 rsw 文件（模型层）

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 're',
                reWalkDir = patchesDir,
                pattern = r'^.*?/(Utility/Patches/.*?/Resource/Original/data)/.*?\.(rsw)',
                baseDir_or_reGroupID = 1,
                baseDir_append = None
            ),
            parsefunc = self.__verifyRsw,
            subject = '校验各补丁目录中的 rsw 文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : 'RSM模型文件', 'resultIndex' : 1 }
            ]
        )

        # 校验地图中 rsm 模型文件的贴图

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 're',
                reWalkDir = patchesDir,
                pattern = r'^.*?/(Utility/Patches/.*?/Resource/Original/data)/.*?\.(rsm)',
                baseDir_or_reGroupID = 1,
                baseDir_append = None
            ),
            parsefunc = self.__verifyRsm,
            subject = '校验各补丁目录中的 rsm 模型的贴图文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : 'RSM模型文件的贴图文件', 'resultIndex' : 1 }
            ]
        )

        # 校验各个补丁目录中动画效果索引文件 str 中所需的贴图
        # =====================================================================

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 're',
                reWalkDir = patchesDir,
                pattern = r'^.*?/(Utility/Patches/.*?/Resource/Original/data)/.*?\.(str)',
                baseDir_or_reGroupID = 1,
                baseDir_append = None
            ),
            parsefunc = self.__verifyStr,
            subject = '校验各补丁目录中 str 文档所需的贴图文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : '动画索引贴图文件', 'resultIndex' : 1 }
            ]
        )

        # 校验各个补丁目录中 Iteminfo 文件中所需的贴图
        # =====================================================================

        self.__subVerifier(
            filesinfo = self.__getFilesInfo(
                glob_or_re = 're',
                reWalkDir = patchesDir,
                pattern = r'^.*?/(Utility/Patches/.*?/Resource/Original)/System/' +
                r'iteminfo.*?\.(lua|lub)',
                baseDir_or_reGroupID = 1,
                baseDir_append = '/data'
            ),
            parsefunc = self.__verifyIteminfo,
            subject = '校验各补丁目录中的 iteminfo 道具描述文件',
            returnPathListIndex = None,
            reportMissInfo = [
                { 'name' : '道具图片', 'resultIndex' : 0 },
                { 'name' : '掉落和拖动时的图档', 'resultIndex' : 1 }
            ]
        )

    def runVerifier(self):
        self.__resetReport()
        self.__globalResourceVerifier()
        self.__patchesResourceVerifier()
        self.__saveReport()
