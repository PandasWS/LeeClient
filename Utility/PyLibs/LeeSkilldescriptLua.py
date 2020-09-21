# -*- coding: utf-8 -*-

import os
import re
from dataclasses import dataclass

from lupa import LuaRuntime

from PyLibs import LeeCommon


@dataclass
class LeeSkilldescriptSingleItem:
    Constant: str
    Description: str

class LeeSkilldescriptLua:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.skilldescriptDict = {}
        self.SKID = []
        self.singleSkilldescriptFormat = '\t[SKID.%s] = {\r\n%s\r\n\t}%s'
        self.skillDescriptFormat = 'SKILL_DESCRIPT = {\r\n%s\r\n}\r\n'

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

    def load(self, filepath):
        self.skilldescriptDict.clear()

        luafile = open(filepath, 'r', encoding = 'latin1')
        content = luafile.read()
        luafile.close()

        # 读取并构建假设的 SKID 常量列表
        SKIDTableContent = self.createLuaTable(
            content, r"[\[|{]\s*SKID\.(.*?)\s*[,|}|\]]", 1, 'SKID'
        )

        # 读取上面构建的常量列表
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(SKIDTableContent)

        # 然后正式载入 skillinfolist 接下来进行处理
        lua.execute(content)

        # 再将信息提取到内存中存储起来
        g = lua.globals()

        for skillFakeID in list(g.SKILL_DESCRIPT):
            skillDescriptLuaObject = g.SKILL_DESCRIPT[skillFakeID]
            skillConstant = self.getSkillConstant(skillFakeID)

            descriptLines = []
            for descriptLine in list(skillDescriptLuaObject):
                descriptLines.append(skillDescriptLuaObject[descriptLine])

            descriptSingleItem = LeeSkilldescriptSingleItem(
                Constant = skillConstant,
                Description = '\r\n'.join(descriptLines)
            )

            self.skilldescriptDict[skillConstant] = descriptSingleItem

    def save(self, savepath):
        fullSkilldescriptText = []

        for skillConstant in self.skilldescriptDict:
            skillDescriptLines = []
            skillDescriptText = self.skilldescriptDict[skillConstant].Description
            skillDescriptList = skillDescriptText.split('\r\n')
            for line in skillDescriptList:
                skillDescriptLines.append('\t\t"%s"%s' % (
                    line,
                    self.leeCommon.isLastReturn(skillDescriptList, line, '', ',')
                ))

            singleSkilldescriptText = self.singleSkilldescriptFormat % (
                skillConstant,
                '\r\n'.join(skillDescriptLines),
                self.leeCommon.isLastReturn(self.skilldescriptDict, skillConstant, '', ',')
            )

            fullSkilldescriptText.append(singleSkilldescriptText)

        luaContent = self.skillDescriptFormat % ('\r\n'.join(fullSkilldescriptText))

        fullSavePath = os.path.abspath(savepath)
        os.makedirs(os.path.dirname(fullSavePath), exist_ok = True)
        luafile = open(fullSavePath, 'w', encoding = 'latin1', newline = '')
        luafile.write(luaContent.replace('\r\r', '\r'))
        luafile.close()

    def clear(self):
        self.skilldescriptDict.clear()

    def items(self):
        return self.skilldescriptDict

    def getSkilldescript(self, skillConstant):
        return None if skillConstant not in self.skilldescriptDict else self.skilldescriptDict[skillConstant]

    def getItemAttribute(self, skillConstant, attribname, dstEncode = 'gbk'):
        try:
            skilldata = self.getSkilldescript(skillConstant)
            if skilldata == None: return None
            value = getattr(skilldata, attribname, None)
            if value == None: return None
            if isinstance(value, list):
                for index, val in enumerate(value):
                    value[index] = val.encode('latin1').decode(dstEncode, errors = 'backslashreplace')
                return value
            else:
                return value.encode('latin1').decode(dstEncode, errors = 'backslashreplace')
        except:
            print('getItemAttribute: 处理 %s 的 %s 字段时出问题, 内容为: \r\n%s', (skillConstant, attribname, value))
            raise

    def setItemAttribute(self, skillConstant, attribname, value, srcEncode = 'gbk'):
        try:
            skilldata = self.getSkilldescript(skillConstant)
            if skilldata == None: return False
            if isinstance(value, list):
                for index, val in enumerate(value):
                    value[index] = val.encode(srcEncode).decode('latin1')
            else:
                value = value.encode(srcEncode).decode('latin1')
            return setattr(self.skilldescriptDict[skillConstant], attribname, value)
        except:
            print('setItemAttribute: 处理 %d 的 %s 字段时出问题, 内容为: \r\n%s', (skillConstant, attribname, value))
            raise
