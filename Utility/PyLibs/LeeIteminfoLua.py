# -*- coding: utf-8 -*-

import os
from dataclasses import dataclass

from lupa import LuaRuntime

from PyLibs import LeeCommon


@dataclass
class LeeIteminfoSingleItem:
    itemID: int
    unidentifiedDisplayName: str
    unidentifiedResourceName: str
    unidentifiedDescriptionName: str
    identifiedDisplayName: str
    identifiedResourceName: str
    identifiedDescriptionName: str
    slotCount: int
    ClassNum: int

class LeeIteminfoLua:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.itemInfoDict = {}

        self.singleItemFormat = \
'''	[%s] = {
		unidentifiedDisplayName = "%s",
		unidentifiedResourceName = "%s",
		unidentifiedDescriptionName = {
%s
		},
		identifiedDisplayName = "%s",
		identifiedResourceName = "%s",
		identifiedDescriptionName = {
%s
		},
		slotCount = %s,
		ClassNum = %s
	}%s'''.replace('\n', '\r\n').replace('\r\r', '\r')

        self.itemInfoFormat = \
'''tbl = {
%s
}

main = function()
	for ItemID,DESC in pairs(tbl) do
		result, msg = AddItem(ItemID, DESC.unidentifiedDisplayName, DESC.unidentifiedResourceName, DESC.identifiedDisplayName, DESC.identifiedResourceName, DESC.slotCount, DESC.ClassNum)
		if not result then
			return false, msg
		end
		for k,v in pairs(DESC.unidentifiedDescriptionName) do
			result, msg = AddItemUnidentifiedDesc(ItemID, v)
			if not result then
				return false, msg
			end
		end
		for k,v in pairs(DESC.identifiedDescriptionName) do
			result, msg = AddItemIdentifiedDesc(ItemID, v)
			if not result then
				return false, msg
			end
		end
	end
	return true, "good"
end
'''.replace('\n', '\r\n').replace('\r\r', '\r')

    def __normdesc(self, desc):
        descLines = []
        for lineNo in desc:
            descLines.append(desc[lineNo])
        return None if not descLines else '\r\n'.join(descLines)

    def __quotedesc(self, descLines):
        if descLines is None:
            return ''
        descLines = descLines.replace('\r\n', '\n').split('\n')
        for index, line in enumerate(descLines):
            line = line.replace('"', r'\"').replace(r'\\', '\\')
            descLines[index] = '\t\t\t"%s"%s' % (line, ',' if (index + 1) < len(descLines) else '')
        return '' if not descLines else '\r\n'.join(descLines)

    def load(self, filepath):
        self.itemInfoDict.clear()

        try:
            luafile = open(filepath, 'r', encoding = 'latin1')
            content = luafile.read()
            luafile.close()

            lua = LuaRuntime(unpack_returned_tuples=True)
            lua.execute(content)
            g = lua.globals()
        except Exception as _err:
            print('解析文件时发生了错误: %s' % filepath)
            raise

        for itemID in list(g.tbl):
            try:
                singleItem = LeeIteminfoSingleItem(
                    itemID = itemID,
                    unidentifiedDisplayName = g.tbl[itemID]['unidentifiedDisplayName'],
                    unidentifiedResourceName = g.tbl[itemID]['unidentifiedResourceName'],
                    unidentifiedDescriptionName = self.__normdesc(
                        g.tbl[itemID]['unidentifiedDescriptionName']
                    ),
                    identifiedDisplayName = g.tbl[itemID]['identifiedDisplayName'],
                    identifiedResourceName = g.tbl[itemID]['identifiedResourceName'],
                    identifiedDescriptionName = self.__normdesc(
                        g.tbl[itemID]['identifiedDescriptionName']
                    ),
                    slotCount = g.tbl[itemID]['slotCount'],
                    ClassNum = g.tbl[itemID]['ClassNum'],
                )
                self.itemInfoDict[self.leeCommon.atoi(itemID)] = singleItem
            except Exception as _err:
                print('Error Item ID = %d' % itemID)
                raise

    def save(self, savepath):
        # 构建表格主体部分, 先定义一下格式部分
        fullItemText = []    # 保存每一个道具完整的文本段

        for itemID in sorted(self.itemInfoDict):
            singleItemText = self.singleItemFormat % (
                self.itemInfoDict[itemID].itemID,
                self.itemInfoDict[itemID].unidentifiedDisplayName,
                self.itemInfoDict[itemID].unidentifiedResourceName,
                self.__quotedesc(self.itemInfoDict[itemID].unidentifiedDescriptionName),
                self.itemInfoDict[itemID].identifiedDisplayName,
                self.itemInfoDict[itemID].identifiedResourceName,
                self.__quotedesc(self.itemInfoDict[itemID].identifiedDescriptionName),
                self.itemInfoDict[itemID].slotCount,
                self.itemInfoDict[itemID].ClassNum,
                self.leeCommon.isLastReturn(sorted(self.itemInfoDict), itemID, '', ',')
            )
            fullItemText.append(singleItemText)

        luaContent = self.itemInfoFormat % ('\r\n'.join(fullItemText))

        fullSavePath = os.path.abspath(savepath)
        os.makedirs(os.path.dirname(fullSavePath), exist_ok = True)
        luafile = open(fullSavePath, 'w', encoding = 'latin1', newline = '')
        luafile.write(luaContent.replace('\r\r', '\r'))
        luafile.close()

    def items(self):
        return self.itemInfoDict

    def getIteminfo(self, itemID):
        return None if itemID not in self.itemInfoDict else self.itemInfoDict[itemID]

    def getItemAttribute(self, itemID, attribname, dstEncode = 'gbk'):
        try:
            itemdata = self.getIteminfo(itemID)
            if itemdata is None:
                return None
            value = getattr(itemdata, attribname, None)
            if value is None:
                return None
            if isinstance(value, list):
                for index, val in enumerate(value):
                    value[index] = val.encode('latin1').decode(dstEncode)
                return value
            else:
                return value.encode('latin1').decode(dstEncode)
        except:
            print('getItemAttribute: 处理 %d 的 %s 字段时出问题, 内容为: \r\n%s', (itemID, attribname, value))
            raise

    def setItemAttribute(self, itemID, attribname, value, srcEncode = 'gbk'):
        try:
            itemdata = self.getIteminfo(itemID)
            if itemdata is None:
                return False
            if isinstance(value, list):
                for index, val in enumerate(value):
                    value[index] = val.encode(srcEncode).decode('latin1')
            else:
                value = value.encode(srcEncode).decode('latin1')
            return setattr(self.itemInfoDict[itemID], attribname, value)
        except:
            print('setItemAttribute: 处理 %d 的 %s 字段时出问题, 内容为: \r\n%s', (itemID, attribname, value))
            raise

    def clear(self):
        self.itemInfoDict.clear()
