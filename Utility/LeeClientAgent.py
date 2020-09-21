#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import timeit

from PyLibs import (LeeButtonTranslator, LeeCommon, LeeIteminfoTranslator,
                    LeeLua, LeePatchManager, LeePublisher,
                    LeeSkilldescriptTranslator, LeeSkillinfolistTranslator,
                    LeeTowninfoTranslator, LeeVerifier)

# ==============================================================================
# 类的定义和实现
# ==============================================================================

class LeeMenu:
    def __init__(self):
        self.patchManager = LeePatchManager()
        self.buttonTranslator = LeeButtonTranslator()
        self.leeVerifier = LeeVerifier()
        self.leeCommon = LeeCommon()

    def menufuncResetWorkshop(self):
        '''
        重置 LeeClient 客户端环境
        为接下来切换其他版本的客户端做好准备
        '''
        try:
            print('正在重置按钮汉化文件 ...')
            self.buttonTranslator.doRevert('AllVersions')

            print('正在重置其他客户端资源 ...')
            self.patchManager.doRevertPatch()

            leeClientDir = self.leeCommon.client(withmark=False)
            if self.leeCommon.isFileExists('%s/data.grf' % leeClientDir):
                os.remove('%s/data.grf' % leeClientDir)

            # 移除各个 Patches 版本目录中的 Temporary 目录
            clientList = self.leeCommon.getRagexeClientList(self.leeCommon.patches())
            for x in clientList:
                temporaryDir = self.leeCommon.special(x, 'temporary')
                self.leeCommon.removeDirectory(temporaryDir)

            print('正在删除空目录 ...')
            self.leeCommon.removeEmptyDirectorys(leeClientDir)

            print('已成功重置 LeeClient 客户端环境')
        except Exception as _err:
            print('很抱歉, 重置 LeeClient 客户端环境的过程中发生了意外, 请检查结果')
            raise

    def menufuncSwitchWorkshop(self, clientver):
        '''
        重置工作区, 并切换 LeeClient 到指定的客户端版本
        '''
        if self.patchManager.canRevert():
            self.leeCommon.confirm(
                [
                    '在切换版本之前, 需要将 LeeClient 客户端恢复到干净状态',
                    '请将自己添加的额外重要文件移出 LeeClient 目录, 避免被程序误删'
                ],
                title='切换主程序版本到 %s' % clientver,
                prompt='是否立刻执行重置操作?',
                inject=self,
                cancelExec='inject.menuitemExitAgent()',
                evalcmd='inject.menufuncResetWorkshop()'
            )
            print('----------------------------------------------------------------')

        # 先执行与此版本相关的汉化工作
        print('正在汉化 iteminfo ...')
        LeeIteminfoTranslator().doTranslate(clientver)

        print('正在汉化 towninfo ...')
        LeeTowninfoTranslator().doTranslate(clientver)

        print('正在汉化 skillinfolist ...')
        LeeSkillinfolistTranslator().doTranslate(clientver)

        print('正在汉化 skilldescript ...')
        LeeSkilldescriptTranslator().doTranslate(clientver)

        print('正在汉化 客户端按钮 ...')
        LeeButtonTranslator().doTranslate(clientver)

        # 将对应的资源覆盖到 LeeClient 主目录
        print('正在切换版本, 请耐心等待...')
        if not self.patchManager.doApplyPatch(clientver):
            print('很抱歉, 切换仙境传说的主程序到 %s 版本的时发生错误, 请检查结果' % clientver)
        else:
            print('已切换仙境传说的主程序到 %s 版本\r\n' % clientver)

    def menufuncPackageSourceToZipfile(self, packageSourceDirname):
        '''
        将指定的打包源压缩成一个 ZIP 文件
        '''
        leeClientParantDir = self.leeCommon.client('..', withmark=False)
        packageSourceDirpath = '%s/%s' % (leeClientParantDir, packageSourceDirname)

        zipFilename = LeePublisher().getZipFilename(packageSourceDirpath)
        if not LeePublisher().makeZip(packageSourceDirpath, zipFilename):
            print('很抱歉, 压缩 ZIP 文件时发生错误, 请检查结果')
        else:
            print('已压缩为 ZIP 文件: %s\r\n' % (zipFilename))

    def menufuncPackageSourceToSetup(self, packageSourceDirname):
        '''
        将指定的打包源制作成一个 Setup 安装程序
        '''
        leeClientParantDir = self.leeCommon.client('..', withmark=False)
        packageSourceDirpath = '%s/%s' % (leeClientParantDir, packageSourceDirname)
        outputDirpath = './Output/%s' % packageSourceDirname

        if not LeePublisher().makeSetup(packageSourceDirpath, outputDirpath):
            print('很抱歉, 制作 Setup 安装程序时发生错误, 请检查结果')
        else:
            print('\r\n已制作完毕的 Setup 安装程序存放在: %s 目录中, 请确认.\r\n' % (os.path.abspath(outputDirpath)))

    def menufuncUpdateButtonTranslateDB(self):
        '''
        根据目前各个客户端的 Resource/Original 目录中的最新文件
        来更新目前正在使用的按钮汉化数据库文件
        '''
        print('正在读取数据库...')
        self.buttonTranslator.load()
        print('正在根据目前 Patches 的内容升级数据库...')
        self.buttonTranslator.update()
        print('正在保存数据库...')
        self.buttonTranslator.save()
        print('更新操作已经完成, 请确认文件的变更内容...\r\n')

    def menufuncClientResourceVerifier(self):
        '''
        对客户端进行资源完整性校验
        '''
        self.leeVerifier.runVerifier()
        print('客户端文件完整性校验已结束\r\n')

    def menufuncBatchDecompileLub(self, lubSourceDirectory):
        '''
        将某个目录下的 lub 文件批量反编译
        需要让用户来选择这个目录的所在位置, 而不是一个固定位置
        '''
        print('您指定的目录为: %s' % lubSourceDirectory)

        if not self.leeCommon.isDirectoryExists(lubSourceDirectory):
            self.leeCommon.exitWithMessage('很抱歉, 你指定的目录不存在, 程序终止')

        if lubSourceDirectory.endswith('/') or lubSourceDirectory.endswith('\\'):
            lubSourceDirectory = lubSourceDirectory[:-1]

        lubOutputDirectory = '%s%s%s' % (
            os.path.dirname(lubSourceDirectory), os.path.sep,
            os.path.basename(lubSourceDirectory) + '_output'
        )
        print('计划的输出目录: %s' % lubOutputDirectory)

        if self.leeCommon.isDirectoryExists(lubOutputDirectory):
            self.leeCommon.exitWithMessage('发现输出目录已经存在, 请先手动删除后重试..')

        print('')
        LeeLua().decodeDir(lubSourceDirectory, lubOutputDirectory)

    def menufuncBatchAmendmentsLub(self):
        '''
        将 Patches 目录下的 lub 文件批量进行整理
        '''
        patchesDir = self.leeCommon.patches()

        for dirpath, _dirnames, filenames in os.walk(patchesDir):
            for filename in filenames:
                fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                if not filename.lower().endswith('.lub'):
                    continue
                if LeeLua().isTrulyLubFile(fullpath):
                    continue
                if not LeeLua().lubAmendments(fullpath, fullpath):
                    self.leeCommon.exitWithMessage('整理 %s 时发生错误, 请确认.' % fullpath)
                else:
                    print('已整理: %s' % os.path.relpath(fullpath, patchesDir))

    def menufuncDetectLubCompiled(self):
        '''
        扫描整个 Patches 目录下的 lub 文件
        检测他们的是否已经被反编译, 并将没有被反编译的 lub 文件列出
        '''
        patchesDir = self.leeCommon.patches()

        print('正在扫描, 可能会花几分钟时间, 请耐心等待...')
        print('')
        work_start = timeit.default_timer()

        for dirpath, _dirnames, filenames in os.walk(patchesDir):
            for filename in filenames:
                fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                if not filename.lower().endswith('.lub'):
                    continue

                if LeeLua().isTrulyLubFile(fullpath):
                    print('尚未反编译 - %s' % (
                        os.path.relpath(fullpath, patchesDir)
                    ))

        work_elapsed = (timeit.default_timer() - work_start)

        print('扫描并检测完毕, 耗时: %0.2f 秒' % work_elapsed)
        print('')

    def menufuncDetectNonAnsiLub(self):
        '''
        扫描整个 Patches 目录下的 lub 文件
        检测他们的文件编码, 并列出非 ANSI 编码的文件
        '''
        patchesDir = self.leeCommon.patches()
        allowANSI = [
            'ASCII', 'EUC-KR', 'LATIN1', 'GBK',
            'GB2312', 'CP949', 'ISO-8859-1', 'WINDOWS-1252'
        ]

        print('正在扫描, 可能会花几分钟时间, 请耐心等待...')
        print('')
        work_start = timeit.default_timer()

        for dirpath, _dirnames, filenames in os.walk(patchesDir):
            for filename in filenames:
                fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                if not filename.lower().endswith('.lub'):
                    continue

                result, encoding = LeeLua().getLubEncoding(fullpath)
                if result and encoding not in allowANSI:
                    print('%s - %s' % (
                        encoding, os.path.relpath(fullpath, patchesDir)
                    ))

        work_elapsed = (timeit.default_timer() - work_start)

        print('扫描并检测完毕, 耗时: %0.2f 秒' % work_elapsed)
        print('')

    def menuitemUpdateButtonTranslateDB(self):
        '''
        菜单处理函数
        当选择“进行一些开发者维护工作 -> 汉化管理 - 更新按钮汉化数据库”时执行
        '''
        self.leeCommon.confirm(
            [
                '已汉化的内容将会被自动继承, 请不用担心',
                '涉及的数据库文件为: Resources/Databases/ButtonTranslate.json'
            ],
            title='更新客户端按钮的翻译数据库',
            prompt='是否执行更新操作?',
            inject=self,
            cancelExec='inject.menuitemExitAgent()',
            evalcmd='inject.menufuncUpdateButtonTranslateDB()'
        )

    def menuitemStatisticsTranslateCoverage(self):
        '''
        菜单处理函数
        当选择“进行一些开发者维护工作 -> 汉化管理 - 汉化覆盖率统计”时执行
        '''
        self.leeCommon.exitWithMessage('此功能目前还在规划中, 待实现...')

    def menuitemClientResourceVerifier(self):
        '''
        菜单处理函数
        当选择“进行一些开发者维护工作 -> 资源管理 - 校验客户端资源完整性”时执行
        '''
        self.leeCommon.confirm(
            [
                '此过程可以协助排除可能的一些图档丢失情况.',
                '不过由于需要对客户端的大量文件进行判断, 时间可能会比较长.'
            ],
            title='对客户端资源进行完整性校验',
            prompt='是否确认执行?',
            inject=self,
            cancelExec='inject.menuitemExitAgent()',
            evalcmd='inject.menufuncClientResourceVerifier()'
        )

    def menuitemBatchDecompileLub(self):
        '''
        菜单处理函数
        当选择“进行一些开发者维护工作 -> 脚本管理 - 批量反编译某个目录中的 lub 文件”时执行
        '''
        self.leeCommon.input(
            [
                '您不能指望反编译后的 lua 文件可被 RO 客户端无错运行.',
                '反编译 lua 的函数时, 转换后的结果常出问题(语法错误), 需手动修正.',
                '',
                '请填写一个包含 lub 文件的 luafiles514 目录的完整路径.',
                '程序只转换后缀为 lub 的文件, 并将反编译后的文件保存到平级目录下.',
                '',
                '比如你填写的路径是: C:\\luafiles 那么输出会在 C:\\luafiles_output',
                '程序会将无需反编译的文件, 也一起复制到输出目录(保持目录结构).'
            ],
            title='批量反编译指定目录下的 lub 文件',
            prompt='请填写目录路径',
            inject=self,
            evalcmd='inject.menufuncBatchDecompileLub(user_input)'
        )

    def menuitemBatchAmendmentsLub(self):
        '''
        菜单处理函数
        当选择“进行一些开发者维护工作 -> 脚本管理 - 批量整理某个目录中的 lub 文件”时执行
        '''
        self.leeCommon.confirm(
            [
                '此操作会将 Patches 目录中的 lub 文件全部找出',
                '然后移除 lub 文件中的一些多余的注释, 并纠正一些格式错误等等.',
                '',
                '程序只转换后缀为 lub 的文件, 并将处理后的文件直接进行替换.',
                '注意: 由于会直接进行替换, 所以请您一定先自己做好备份! 避免意外.',
            ],
            title='批量整理所有 lub 文件的内容',
            prompt='是否立刻执行整理操作?',
            inject=self,
            cancelExec='inject.menuitemExitAgent()',
            evalcmd='inject.menufuncBatchAmendmentsLub()'
        )

    def menuitemDetectLubCompiled(self):
        '''
        菜单处理函数
        当选择“进行一些开发者维护工作 -> 脚本管理 - 扫描并列出所有未被反编译的 lub 文件”时执行
        '''
        self.leeCommon.confirm(
            [
                '此操作会将 Patches 目录中的 lub 文件全部找出',
                '然后判断其是否已经被反编译, 并将没有被反编译的 lub 全部列出.',
                '',
                '注意: 为了提高效率, 我们只对文件后缀为 lub 的文件进行判断.'
            ],
            title='扫描并列出所有未被反编译的 lub 文件',
            prompt='是否立刻执行扫描操作?',
            inject=self,
            cancelExec='inject.menuitemExitAgent()',
            evalcmd='inject.menufuncDetectLubCompiled()'
        )

    def menuitemDetectNonAnsiLub(self):
        '''
        菜单处理函数
        当选择“进行一些开发者维护工作 -> 脚本管理 - 扫描并列出所有非 ANSI 编码的 lub 文件”时执行
        '''
        self.leeCommon.confirm(
            [
                '此操作会将 Patches 目录中的 lub 文件全部找出',
                '然后探测其文件编码, 将所有非 ANSI 类型编码的文件都列出来.',
                '',
                '注意: GBK 和 EUC-KR 都属于 ANSI 类型编码, 而 UTF8 则不是.',
                '这里的 lub 文件实际上是 lua 的明文脚本文件.'
            ],
            title='扫描并列出所有非 ANSI 编码的 lub 文件',
            prompt='是否立刻执行扫描操作?',
            inject=self,
            cancelExec='inject.menuitemExitAgent()',
            evalcmd='inject.menufuncDetectNonAnsiLub()'
        )
    
    def menuitemBuildSourceUseGRF(self):
        '''
        菜单处理函数
        当选择“生成 / 打包 / 制作客户端安装程 -> 将当前客户端状态导出成打包源 ->
        将 data 目录压缩成 GRF (推荐)”时执行
        '''
        LeePublisher().makeSource(True)
    
    def menuitemBuildSourceDontUseGRF(self):
        '''
        菜单处理函数
        当选择“生成 / 打包 / 制作客户端安装程 -> 将当前客户端状态导出成打包源 ->
        不压缩 data 目录中的文件, 保持零散小文件状态 (不推荐)”时执行
        '''
        LeePublisher().makeSource(False)

    def menuitemConfrimDataFolderType(self):
        '''
        菜单处理函数
        当选择“生成 / 打包 / 制作客户端安装程 -> 将当前客户端状态导出成打包源”时执行
        '''
        self.leeCommon.menu(
            [
                ['将 data 目录压缩成 GRF (推荐, 仅 Windows 支持)', 'inject.menuitemBuildSourceUseGRF()'],
                ['不压缩 data 目录中的文件, 保持零散小文件状态 (不推荐)', 'inject.menuitemBuildSourceDontUseGRF()']
            ],
            title='生成打包源时, 您希望如何处理 data 目录:',
            inject=self
        )

    def menuitemPackageSourceToZipfile(self):
        '''
        菜单处理函数
        当选择“生成 / 打包 / 制作客户端安装程 -> 选择一个打包源, 压缩成 ZIP 包”时执行
        '''
        packageSourceDirnameList = LeePublisher().getPackageSourceList(
            self.leeCommon.client('..')
        )
        if packageSourceDirnameList is None:
            self.leeCommon.exitWithMessage('很抱歉, 无法获取打包源列表, 程序终止')

        if not packageSourceDirnameList:
            self.leeCommon.exitWithMessage('没有发现任何可用的打包源, 请先生成一个吧')

        self.leeCommon.menu(
            [
                [x, 'inject.menufuncPackageSourceToZipfile(\'%s\')' % x]
                for x in packageSourceDirnameList
            ],
            title='将指定的打包源压缩成 ZIP 文件',
            prompt='请选择你想压缩的打包源目录',
            inject=self,
            cancelExec='inject.entrance()',
            withCancel=True
        )

    def menuitemPackageSourceToSetup(self):
        '''
        菜单处理函数
        当选择“生成 / 打包 / 制作客户端安装程 -> 选择一个打包源, 制作游戏安装程序”时执行
        '''
        packageSourceDirnameList = LeePublisher().getPackageSourceList(
            self.leeCommon.client('..')
        )
        if packageSourceDirnameList is None:
            self.leeCommon.exitWithMessage('很抱歉, 无法获取打包源列表, 程序终止')

        if not packageSourceDirnameList:
            self.leeCommon.exitWithMessage('没有发现任何可用的打包源, 请先生成一个吧')

        self.leeCommon.menu(
            [
                [x, 'inject.menufuncPackageSourceToSetup(\'%s\')' % x]
                for x in packageSourceDirnameList
            ],
            title='将指定的打包源制作成安装程序',
            prompt='请选择你想制作的打包源目录',
            inject=self,
            cancelExec='inject.entrance()',
            withCancel=True
        )

    def menuitemSwitchWorkshop(self):
        '''
        菜单处理函数
        当选择“切换客户端到指定版本”时执行
        '''
        clientList = self.leeCommon.getRagexeClientList(self.leeCommon.patches())
        if clientList is None:
            self.leeCommon.exitWithMessage('很抱歉, 无法获取客户端版本列表, 程序终止')

        menus = [['切换到 %s 版本' % x, 'inject.menufuncSwitchWorkshop(\'%s\')' % x] for x in clientList]
        menus.insert(0, ['将客户端重置回干净状态', 'inject.menuitemResetWorkshop()'])

        self.leeCommon.menu(
            items=menus,
            title='切换客户端到指定版本, 以便与服务端配套工作:',
            inject=self,
            cancelExec='inject.entrance()',
            withCancel=True
        )

    def menuitemResetWorkshop(self):
        '''
        菜单处理函数
        当选择“切换客户端到指定版本 -> 将客户端重置回干净状态”时执行
        '''
        if self.patchManager.canRevert():
            self.leeCommon.confirm(
                [
                    '此操作可以将 LeeClient 客户端恢复到干净状态',
                    '请将自己添加的额外重要文件移出 LeeClient 目录, 避免被程序误删.',
                    '',
                    '提醒: 此操作不会删除 Utility/Import 目录下的文件, 请放心.'
                ],
                title='将客户端重置回干净状态',
                prompt='是否立刻执行重置操作?',
                inject=self,
                cancelExec='inject.menuitemExitAgent()',
                evalcmd='inject.menufuncResetWorkshop()'
            )
        else:
            self.leeCommon.exitWithMessage('您的客户端环境看起来十分干净, 不需要再进行清理了.')

    def menuitemMaintenance(self):
        '''
        菜单处理函数
        当选择“进行一些开发者维护工作”时执行
        '''
        self.leeCommon.menu(
            [
                ['汉化管理 - 更新按钮汉化数据库', 'inject.menuitemUpdateButtonTranslateDB()'],
                ['汉化管理 - 汉化覆盖率统计（计划实现）', 'inject.menuitemStatisticsTranslateCoverage()'],
                ['资源管理 - 校验客户端资源完整性', 'inject.menuitemClientResourceVerifier()'],
                ['脚本管理 - 批量反编译某个目录中的 lub 文件', 'inject.menuitemBatchDecompileLub()'],
                ['脚本管理 - 批量整理某个目录中的 lub 文件', 'inject.menuitemBatchAmendmentsLub()'],
                ['脚本管理 - 扫描并列出所有未被反编译的 lub 文件', 'inject.menuitemDetectLubCompiled()'],
                ['脚本管理 - 扫描并列出所有非 ANSI 编码的 lub 文件', 'inject.menuitemDetectNonAnsiLub()']
            ],
            title='以下是一些开发者维护工作, 请选择您需要的操作:',
            inject=self
        )

    def menuitemMakePackageOrSetup(self):
        '''
        菜单处理函数
        当选择“生成 / 打包 / 制作客户端安装程序”时执行
        '''
        self.leeCommon.menu(
            [
                ['将当前客户端状态导出成打包源', 'inject.menuitemConfrimDataFolderType()'],
                ['选择一个打包源, 压缩成 ZIP 包', 'inject.menuitemPackageSourceToZipfile()'],
                ['选择一个打包源, 制作游戏安装程序 (仅 Windows 平台支持)', 'inject.menuitemPackageSourceToSetup()']
            ],
            title='生成 / 打包 / 制作客户端安装程序, 请选择您需要的操作:',
            inject=self
        )

    def menuitemExitAgent(self):
        '''
        菜单处理函数
        当选择“退出程序”时执行
        '''
        self.leeCommon.exitWithMessage('感谢您的使用, 再见')

    def entrance(self):
        '''
        菜单处理函数
        这里是主菜单的入口处
        '''
        self.leeCommon.menu(
            [
                ['切换客户端到指定版本', 'inject.menuitemSwitchWorkshop()'],
                ['生成 / 打包 / 制作客户端安装程序', 'inject.menuitemMakePackageOrSetup()'],
                ['进行一些开发者维护工作', 'inject.menuitemMaintenance()'],
                ['退出程序', 'inject.menuitemExitAgent()']
            ],
            title='您好, 欢迎使用 LeeClientAgent 来管理您的客户端!',
            inject=self
        )

def main():
    '''
    LeeClientAgent 的主入口函数
    '''
    # 显示欢迎信息
    LeeCommon().welcome()

    # 验证程序所在位置是否正确
    LeeCommon().verifyAgentLocation()

    # 进入主菜单
    LeeMenu().entrance()

    # Windows 上用户按一下再终止
    LeeCommon().pauseScreen()

if __name__ == '__main__':
    main()
