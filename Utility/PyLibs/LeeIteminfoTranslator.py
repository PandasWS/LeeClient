# -*- coding: utf-8 -*-

from PyLibs import LeeBaseTranslator, LeeIteminfoLua


class LeeIteminfoTranslator(LeeBaseTranslator):
    def __init__(self):
        LeeBaseTranslator.__init__(self)
        self.leeFileIO = LeeIteminfoLua()
        self.translateDefaultDBPath = 'Resources/Databases/IteminfoTranslate.json'
        self.reSrcPathPattern = self.leeCommon.normPattern(
            r'^.*?/Patches/.*?/Resource/Original/System/iteminfo.*?\.(lua|lub)'
        )
        self.reDstPathPattern = self.leeCommon.normPattern(
            r'(^.*?/Patches/.*?/Resource)/Original/(System/iteminfo.*?\.(lua|lub))'
        )

    def create(self, srcIteminfoPath, translateDBPath = None):
        if translateDBPath is None:
            translateDBPath = self.translateDefaultDBPath
        self.clear()
        self.leeFileIO.clear()
        self.leeFileIO.load(srcIteminfoPath)
        for itemID in self.leeFileIO.items():
            unidentifiedDescriptionName = self.leeFileIO.getItemAttribute(
                itemID, 'unidentifiedDescriptionName'
            )
            identifiedDescriptionName = self.leeFileIO.getItemAttribute(
                itemID, 'identifiedDescriptionName'
            )
            self.translateMap[itemID] = {
                'unidentifiedDisplayName' : self.leeFileIO.getItemAttribute(
                    itemID, 'unidentifiedDisplayName'
                ),
                'unidentifiedDescriptionName' : (
                    [] if unidentifiedDescriptionName is None else \
                    unidentifiedDescriptionName.split('\r\n')
                ),
                'identifiedDisplayName' : self.leeFileIO.getItemAttribute(
                    itemID, 'identifiedDisplayName'
                ),
                'identifiedDescriptionName' : (
                    [] if identifiedDescriptionName is None else \
                    identifiedDescriptionName.split('\r\n')
                )
            }
        self.save(translateDBPath)

    def translate(self, srcFilepath, dstFilepath):
        self.leeFileIO.load(srcFilepath)
        for itemID in self.leeFileIO.items():
            if str(itemID) not in self.translateMap:
                continue
            itemTranslateData = self.translateMap[str(itemID)]
            if not self.leeCommon.isEmpty(itemTranslateData['unidentifiedDisplayName']):
                self.leeFileIO.setItemAttribute(
                    itemID, 'unidentifiedDisplayName',
                    itemTranslateData['unidentifiedDisplayName']
                )
            if not self.leeCommon.isEmpty(itemTranslateData['unidentifiedDescriptionName']):
                self.leeFileIO.setItemAttribute(
                    itemID, 'unidentifiedDescriptionName',
                    '\r\n'.join(itemTranslateData['unidentifiedDescriptionName'])
                )
            if not self.leeCommon.isEmpty(itemTranslateData['identifiedDisplayName']):
                self.leeFileIO.setItemAttribute(
                    itemID, 'identifiedDisplayName',
                    itemTranslateData['identifiedDisplayName']
                )
            if not self.leeCommon.isEmpty(itemTranslateData['identifiedDescriptionName']):
                self.leeFileIO.setItemAttribute(
                    itemID, 'identifiedDescriptionName',
                    '\r\n'.join(itemTranslateData['identifiedDescriptionName'])
                )
        self.leeFileIO.save(dstFilepath)
