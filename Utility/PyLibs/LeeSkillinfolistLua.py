# -*- coding: utf-8 -*-

import copy
import os
import re
from dataclasses import dataclass

from lupa import LuaRuntime

from PyLibs import LeeCommon


@dataclass
class LeeNeedSkillItem:
    Constant: str
    SkillFakeID: int
    RequireLv: int

@dataclass
class LeeSkillScaleItem:
    lv: int
    x: int
    y: int

@dataclass
class LeeSkillinfoSingleItem:
    Constant: str
    SkillName: str
    MaxLv: int
    Type: str
    SpAmount: list
    bSeperateLv: bool
    AttackRange: list
    _NeedSkillList: list
    NeedSkillList: dict
    SkillScale: list


class LeeSkillinfolistLua:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.skillinfolistDict = {}
        self.SKID = []
        self.JOBID = []

        self.singleSkillinfoFormat = \
'''	[SKID.%s] = {
		"%s",
		SkillName = "%s",
		MaxLv = %s,
		SpAmount = { %s },
		bSeperateLv = %s,
		AttackRange = { %s }%s
	}%s'''.replace('\n', '\r\n').replace('\r\r', '\r')

        self._neeskillListFormat = ',\r\n\t\t_NeedSkillList = {\r\n%s\r\n\t\t}'
        self.neeskillListFormat = ',\r\n\t\tNeedSkillList = {\r\n%s\r\n\t\t}'
        self.jobDepentFormat = '\t\t\t[JOBID.%s] = {\r\n%s\r\n\t\t\t}%s'

        self.skillScaleListFormat = ',\r\n\t\tSkillScale = {\r\n%s\r\n\t\t}'
        self.skillScaleItemFormat = '\t\t\t[%s] = { x = %s, y = %s }%s'
        self.skillinfoListFormat = 'SKILL_INFO_LIST = {\r\n%s\r\n}\r\n'

    def createLuaTable(self, luaContent, regex, pos, tableName):
        matches = re.finditer(regex, luaContent, re.MULTILINE | re.IGNORECASE | re.DOTALL)

        tables = []
        for match in matches:
            tables.append(match.group(pos))

        tables = set(tables)
        setattr(self, tableName, list(tables))

        contentList = []
        for num, item in enumerate(tables):
            contentList.append('%s = %s' % (item, num + 1))

        return '%s = { %s }' % (tableName, ', '.join(contentList))

    def getSkillConstant(self, skillFakeID):
        return self.SKID[skillFakeID - 1]

    def getJobIdConstant(self, jobFakeID):
        return self.JOBID[jobFakeID - 1]

    def load(self, filepath):
        self.skillinfolistDict.clear()

        luafile = open(filepath, 'r', encoding = 'latin1')
        content = luafile.read()
        luafile.close()

        # 读取并构建假设的 SKID 常量列表
        SKIDTableContent = self.createLuaTable(
            content, r"[\[|{]\s*SKID\.(.*?)\s*[,|}|\]]", 1, 'SKID'
        )

        # 读取并构建假设的 JOBID 常量列表
        JOBIDTableContent = self.createLuaTable(
            content, r"[\[|{]\s*JOBID\.(.*?)\s*[,|}|\]]", 1, 'JOBID'
        )

        # 读取上面构建的两个常量列表
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(SKIDTableContent)
        lua.execute(JOBIDTableContent)

        # 然后正式载入 skillinfolist 接下来进行处理
        lua.execute(content)

        # 再将信息提取到内存中存储起来
        g = lua.globals()

        dummyClass = LeeSkillinfoSingleItem(
            Constant = '',
            SkillName = '',
            MaxLv = 0,
            Type = '',
            SpAmount = [],
            bSeperateLv = False,
            AttackRange = [],
            _NeedSkillList = [],
            NeedSkillList = {},
            SkillScale = []
        )

        for skillFakeID in list(g.SKILL_INFO_LIST):
            dummyClass.SpAmount.clear()
            dummyClass.AttackRange.clear()
            dummyClass._NeedSkillList.clear()
            dummyClass.NeedSkillList.clear()
            dummyClass.SkillScale.clear()

            skillItemLuaObject = g.SKILL_INFO_LIST[skillFakeID]
            skillConstant = self.getSkillConstant(skillFakeID)

            for attributeName in list(skillItemLuaObject):
                if attributeName == 1:
                    dummyClass.Constant = skillItemLuaObject[attributeName]
                elif attributeName in ['SkillName']:
                    dummyClass.SkillName = skillItemLuaObject[attributeName]
                elif attributeName in ['SpAmount', 'AttackRange']:
                    strValueList = []
                    for key in list(skillItemLuaObject[attributeName]):
                        strValueList.append(str(skillItemLuaObject[attributeName][key]))
                    setattr(dummyClass, attributeName, strValueList)
                elif attributeName in ['_NeedSkillList']:
                    for needID in list(skillItemLuaObject[attributeName]):
                        needItem = skillItemLuaObject[attributeName][needID]
                        needSkillItem = LeeNeedSkillItem(
                            Constant = self.getSkillConstant(needItem[1]),
                            SkillFakeID = needItem[1],
                            RequireLv = needItem[2]
                        )
                        dummyClass._NeedSkillList.append(needSkillItem)
                elif attributeName in ['SkillScale']:
                    for scaleLevel in list(skillItemLuaObject[attributeName]):
                        scaleInfoItems = skillItemLuaObject[attributeName][scaleLevel]
                        scaleInfo = LeeSkillScaleItem(
                            lv = scaleLevel,
                            x = scaleInfoItems['x'],
                            y = scaleInfoItems['y']
                        )
                        dummyClass.SkillScale.append(scaleInfo)
                elif attributeName in ['NeedSkillList']:
                    for jobID in list(skillItemLuaObject[attributeName]):
                        jobConstant = self.getJobIdConstant(jobID)
                        jobItems = skillItemLuaObject[attributeName][jobID]
                        jobNeedSkillList = []
                        for needID in list(jobItems):
                            needItem = jobItems[needID]
                            needSkillItem = LeeNeedSkillItem(
                                Constant = self.getSkillConstant(needItem[1]),
                                SkillFakeID = needItem[1],
                                RequireLv = needItem[2]
                            )
                            jobNeedSkillList.append(needSkillItem)
                        dummyClass.NeedSkillList[jobConstant] = jobNeedSkillList
                elif hasattr(dummyClass, attributeName):
                    setattr(dummyClass, attributeName, skillItemLuaObject[attributeName])
                else:
                    self.leeCommon.exitWithMessage('技能 %s 存在未知的属性 "%s", 请进行处理' % (
                        self.getSkillConstant(skillFakeID), attributeName
                    ))

            self.skillinfolistDict[skillConstant] = copy.deepcopy(dummyClass)

    def save(self, savepath):
        fullSkillinfolistText = []

        for skillConstant in self.skillinfolistDict:
            _needSkillContent = []
            for needskill in self.skillinfolistDict[skillConstant]._NeedSkillList:
                _needSkillContent.append('\t\t\t{ SKID.%s, %s }%s' % (
                    needskill.Constant, needskill.RequireLv,
                    self.leeCommon.isLastReturn(self.skillinfolistDict[skillConstant]._NeedSkillList, needskill, '', ',')
                ))
            _needSkillListText = '' if len(self.skillinfolistDict[skillConstant]._NeedSkillList) <= 0 else \
            self._neeskillListFormat % (
                '\r\n'.join(_needSkillContent)
            )

            ###

            needSkillContent = []
            for jobConstant in self.skillinfolistDict[skillConstant].NeedSkillList:
                jobNeedSkillText = []
                for needskill in self.skillinfolistDict[skillConstant].NeedSkillList[jobConstant]:
                    jobNeedSkillText.append('\t\t\t\t{ SKID.%s, %s }%s' % (
                        needskill.Constant, needskill.RequireLv,
                        self.leeCommon.isLastReturn(self.skillinfolistDict[skillConstant].NeedSkillList[jobConstant], needskill, '', ',')
                    ))
                jobDependText = self.jobDepentFormat % (
                    jobConstant,
                    '\r\n'.join(jobNeedSkillText),
                    self.leeCommon.isLastReturn(self.skillinfolistDict[skillConstant].NeedSkillList, jobConstant, '', ',')
                )
                needSkillContent.append(jobDependText)

            needSkillListText = '' if len(self.skillinfolistDict[skillConstant].NeedSkillList) <= 0 else \
            self.neeskillListFormat % (
                '\r\n'.join(needSkillContent)
            )

            ###

            skillScaleContent = []
            for scaleInfo in self.skillinfolistDict[skillConstant].SkillScale:
                skillScaleItemText = self.skillScaleItemFormat % (
                    scaleInfo.lv, scaleInfo.x, scaleInfo.y,
                    self.leeCommon.isLastReturn(self.skillinfolistDict[skillConstant].SkillScale, scaleInfo, '', ',')
                )
                skillScaleContent.append(skillScaleItemText)

            skillScaleText = '' if len(self.skillinfolistDict[skillConstant].SkillScale) <= 0 else \
            self.skillScaleListFormat % (
                '\r\n'.join(skillScaleContent)
            )

            ###

            singleItemText = self.singleSkillinfoFormat % (
                self.skillinfolistDict[skillConstant].Constant,
                self.skillinfolistDict[skillConstant].Constant,
                self.skillinfolistDict[skillConstant].SkillName,
                self.skillinfolistDict[skillConstant].MaxLv,
                ', '.join(self.skillinfolistDict[skillConstant].SpAmount),
                str(self.skillinfolistDict[skillConstant].bSeperateLv).lower(),
                ', '.join(self.skillinfolistDict[skillConstant].AttackRange),
                _needSkillListText + needSkillListText + skillScaleText,
                self.leeCommon.isLastReturn(self.skillinfolistDict, skillConstant, '', ',')
            )
            singleItemText = singleItemText.replace('{  }', '{ }')
            fullSkillinfolistText.append(singleItemText)

        luaContent = self.skillinfoListFormat % ('\r\n'.join(fullSkillinfolistText))

        fullSavePath = os.path.abspath(savepath)
        os.makedirs(os.path.dirname(fullSavePath), exist_ok = True)
        luafile = open(fullSavePath, 'w', encoding = 'latin1', newline = '')
        luafile.write(luaContent.replace('\r\r', '\r'))
        luafile.close()

    def clear(self):
        self.skillinfolistDict.clear()

    def items(self):
        return self.skillinfolistDict

    def getSkillinfo(self, skillConstant):
        return None if skillConstant not in self.skillinfolistDict else self.skillinfolistDict[skillConstant]

    def getItemAttribute(self, skillConstant, attribname, dstEncode = 'gbk'):
        try:
            skilldata = self.getSkillinfo(skillConstant)
            if skilldata == None: return None
            value = getattr(skilldata, attribname, None)
            if value == None: return None
            return value.encode('latin1').decode(dstEncode, errors = 'backslashreplace')
        except:
            print('getItemAttribute: 处理 %s 的 %s 字段时出问题, 内容为: \r\n%s', (skillConstant, attribname, value))
            raise

    def setItemAttribute(self, skillConstant, attribname, value, srcEncode = 'gbk'):
        try:
            skilldata = self.getSkillinfo(skillConstant)
            if skilldata == None: return False
            value = value.encode(srcEncode).decode('latin1')
            return setattr(self.skillinfolistDict[skillConstant], attribname, value)
        except:
            print('setItemAttribute: 处理 %d 的 %s 字段时出问题, 内容为: \r\n%s', (skillConstant, attribname, value))
            raise
