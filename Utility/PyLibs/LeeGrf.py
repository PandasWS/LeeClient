# -*- coding: utf-8 -*-

import os
import platform
import subprocess
import sys
import glob

from PyLibs import LeeCommon, LeePatchManager


class LeeGrf:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.patchManager = LeePatchManager()
    
    def isGrfExists(self):
        leeClientDir = self.leeCommon.client(withmark=False)
        grfFiles = glob.glob('%s/*.grf' % leeClientDir)
        return len(grfFiles) > 0

    def makeGrf(self, dataDirpath, grfOutputPath):
        # 确认操作系统平台
        if platform.system() != 'Windows':
            self.leeCommon.exitWithMessage('很抱歉, 此功能目前只能在 Windows 平台上运行.')

        # 确认 GrfCL 所需要的 .net framework 已安装
        if not self.leeCommon.isDotNetFrameworkInstalled('v3.5'):
            print('您必须先安装微软的 .NET Framework v3.5 框架.')
            self.leeCommon.exitWithMessage(
                '下载地址: https://www.microsoft.com/zh-CN/download/details.aspx?id=21'
            )

        # 确认已经切换到了需要的客户端版本
        if not self.patchManager.canRevert():
            self.leeCommon.exitWithMessage('请先将 LeeClient 切换到某个客户端版本, 以便制作出来的 grf 文件内容完整.')

        # 确认有足够的磁盘剩余空间进行压缩
        currentDriver = self.leeCommon.utility()[0]
        currentFreeSpace = self.leeCommon.getDiskFreeSpace(currentDriver)
        if currentFreeSpace <= 1024 * 1024 * 1024 * 3:
            self.leeCommon.exitWithMessage('磁盘 %s: 的空间不足 3GB, 请清理磁盘释放更多空间.' % currentDriver)

        # 确认 GrfCL 文件存在
        scriptDir = self.leeCommon.utility(withmark=False)
        grfCLFilepath = ('%s/Bin/GrfCL/GrfCL.exe' % scriptDir).replace('/', os.path.sep)
        if not self.leeCommon.isFileExists(grfCLFilepath):
            self.leeCommon.exitWithMessage('制作 grf 文件所需的 GrfCL.exe 程序不存在, 无法执行压缩.')

        # data.grf 文件若存在则进行覆盖确认
        if self.leeCommon.isFileExists(grfOutputPath):
            lines = [
                '发现客户端目录中已存在 %s 文件,' % os.path.basename(grfOutputPath),
                '若继续将会先删除此文件, 为避免文件被误删, 请您进行确认.'
            ]
            title = '文件覆盖提示'
            prompt = '是否删除文件并继续?'
            if not self.leeCommon.confirm(lines, title, prompt, None, None, None):
                self.leeCommon.exitWithMessage('由于您放弃继续, 程序已自动终止.')
            os.remove(grfOutputPath)

        # 执行压缩工作（同步等待）
        grfCLProc = subprocess.Popen('%s %s' % (
            grfCLFilepath,
            '-breakOnExceptions true -makeGrf "%s" "%s"' % (
                os.path.relpath(grfOutputPath, os.path.dirname(grfCLFilepath)),
                os.path.relpath(dataDirpath, os.path.dirname(grfCLFilepath))
            )
        ), stdout = sys.stdout, cwd = os.path.dirname(grfCLFilepath))
        grfCLProc.wait()

        # 确认结果并输出提示信息表示压缩结束
        if grfCLProc.returncode == 0 and self.leeCommon.isFileExists(grfOutputPath):
            print('已经将 data 目录压缩为 data.grf 并存放到根目录.')
            print('')
            self.leeCommon.printSmallCutLine()
            print('')
        else:
            self.leeCommon.exitWithMessage('进行压缩工作的时候发生错误, 请发 Issue 进行反馈.')
