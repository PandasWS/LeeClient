# -*- coding: utf-8 -*-

import os
import platform
import re
import shutil
import subprocess

from PyLibs import LeeCommon


class LeeLua:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.sourceDirectory = None
        self.outputDirectory = None
        self.grfCLFilepath = None
        self.baseDirectory = None

    def __getOutputFilePath(self, sourcePath):
        relpath = os.path.relpath(sourcePath, self.sourceDirectory)
        outputpath = os.path.abspath('%s%s%s' % (
            self.outputDirectory, os.path.sep, relpath
        ))
        return outputpath

    def isTrulyLubFile(self, filepath):
        rawfile = open(filepath, 'rb')
        magicHeader = rawfile.read(6)
        rawfile.close()

        return (magicHeader[0] == 0x1B and magicHeader[1] == 0x4C and
                magicHeader[2] == 0x75 and magicHeader[3] == 0x61 and
                magicHeader[4] == 0x51 and magicHeader[5] == 0x00)

    def __replaceFunctionStruct(self, line):
        matches = re.match(r'^(\w*?)\s=\sfunction\((.*?)\)(.*?)$', line)
        if not matches:
            return line
        return 'function {funname}({params})'.format(
            funname = matches.group(1),
            params = matches.group(2)
        )

    def __removeFunctionNote(self, line):
        if line.startswith('-- Function #'):
            return None
        return line

    def __lubAmendmentsByFile(self, filename, content):

        # 移除 GRF Editor Decompiler 标记
        markRemoveIndex = []
        for index, line in enumerate(content):
            if re.match('^-- Using GRF Editor Decompiler.*?$', line):
                content[index] = None
                markRemoveIndex.append(index + 1)
            if index in markRemoveIndex:
                content[index] = None

        # 若文件的末尾没有空行的话, 补加一个空行
        if not content:
            content.append('')
        if str(content[-1]).strip() != '' and not str(content[-1]).endswith('\n'):
            content.append('')

        # if filename.lower() == 'kaframovemapservicelist.lub':
        #     pass

        content = [x for x in content if x is not None]
        return content

    def lubAmendments(self, srcfilepath, dstfilepath):
        encoding = self.leeCommon.getEncodingByFile(srcfilepath)
        encoding = 'latin1' if encoding is None else encoding

        try:
            luafile = open(srcfilepath, 'r', encoding=encoding, newline='')
            content = luafile.readlines()
            luafile.close()

            # 按行进行处理
            content = [x.replace('\r\n', '\n').replace('\n', '') for x in content]
            for index, line in enumerate(content):
                line = self.__replaceFunctionStruct(line)
                line = self.__removeFunctionNote(line)
                content[index] = line
            content = [x for x in content if x is not None]

            # 按文件进行处理
            content = self.__lubAmendmentsByFile(
                os.path.basename(srcfilepath), content
            )

            savefile = open(dstfilepath, 'w', encoding=encoding, newline='')
            savefile.write('\r\n'.join(content))
            savefile.close()
            return True
        except Exception as _err:
            print('对 lub 文件进行处理时发生错误: %s' % srcfilepath)
            raise

    def amendmentsDir(self, lubSourceDirectory, lubOutputDirectory):
        self.sourceDirectory = lubSourceDirectory
        self.outputDirectory = lubOutputDirectory
        self.baseDirectory = os.path.dirname(self.sourceDirectory)

        for dirpath, _dirnames, filenames in os.walk(lubSourceDirectory):
            for filename in filenames:
                fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                destpath = self.__getOutputFilePath(fullpath)
                os.makedirs(os.path.dirname(destpath), exist_ok=True)

                if fullpath.lower().endswith('.lub') and not self.isTrulyLubFile(fullpath):
                    self.lubAmendments(fullpath, destpath)
                    print('整理完毕: ' + os.path.relpath(fullpath, self.baseDirectory))
                else:
                    shutil.copyfile(fullpath, destpath)
                    print('已经复制: ' + os.path.relpath(fullpath, self.baseDirectory))

    def getLubEncoding(self, filepath):
        if not self.isTrulyLubFile(filepath):
            return True, self.leeCommon.getEncodingByFile(filepath)
        else:
            return False, None

    def decodeFile(self, lubSourcePath, lubOutputPath):
        grfCLProc = subprocess.Popen('%s %s' % (
            self.grfCLFilepath,
            '-breakOnExceptions true -lub "%s" "%s"' % (
                lubSourcePath, lubOutputPath
            )
        ), stdout=subprocess.PIPE, cwd = os.path.dirname(self.grfCLFilepath))
        grfCLProc.wait()

        # 确认结果并输出提示信息表示反编译结束
        if grfCLProc.returncode == 0 and self.leeCommon.isFileExists(lubOutputPath):
            print('已输出到: ' + os.path.relpath(lubOutputPath, self.baseDirectory))
            self.lubAmendments(lubOutputPath, lubOutputPath)
            return True

        print('进行反编译时发生错误: ' + os.path.relpath(lubSourcePath, self.baseDirectory))
        return False

    def decodeDir(self, lubSourceDirectory, lubOutputDirectory):
        # 记录到成员变量里面
        self.sourceDirectory = lubSourceDirectory
        self.outputDirectory = lubOutputDirectory
        self.baseDirectory = os.path.dirname(self.sourceDirectory)

        # 确认操作系统平台
        if platform.system() != 'Windows':
            self.leeCommon.exitWithMessage('很抱歉, 此功能目前只能在 Windows 平台上运行.')

        # 确认 GrfCL 所需要的 .net framework 已安装
        if not self.leeCommon.isDotNetFrameworkInstalled('v3.5'):
            print('您必须先安装微软的 .NET Framework v3.5 框架.')
            self.leeCommon.exitWithMessage(
                '下载地址: https://www.microsoft.com/zh-CN/download/details.aspx?id=21'
            )

        # 确认 GrfCL 文件存在
        scriptDir = self.leeCommon.utility(withmark=False)
        self.grfCLFilepath = ('%s/Bin/GrfCL/GrfCL.exe' % scriptDir).replace('/', os.path.sep)
        if not self.leeCommon.isFileExists(self.grfCLFilepath):
            self.leeCommon.exitWithMessage('反编译 lub 文件所需的 GrfCL.exe 程序不存在, 无法执行反编译.')

        for dirpath, _dirnames, filenames in os.walk(lubSourceDirectory):
            for filename in filenames:
                fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                destpath = self.__getOutputFilePath(fullpath)
                os.makedirs(os.path.dirname(destpath), exist_ok=True)

                print('')
                if fullpath.lower().endswith('.lub') and self.isTrulyLubFile(fullpath):
                    print('需反编译: ' + os.path.relpath(fullpath, self.baseDirectory))
                    if not self.decodeFile(fullpath, destpath):
                        print('失败复制: ' + os.path.relpath(fullpath, self.baseDirectory))
                        shutil.copyfile(fullpath, destpath)
                else:
                    print('直接复制: ' + os.path.relpath(fullpath, self.baseDirectory))
                    shutil.copyfile(fullpath, destpath)
