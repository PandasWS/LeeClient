# -*- coding: utf-8 -*-

from PyLibs import LeeBaseTranslator, LeeSkilldescriptLua


class LeeSkilldescriptTranslator(LeeBaseTranslator):
    def __init__(self):
        LeeBaseTranslator.__init__(self)
        self.leeFileIO = LeeSkilldescriptLua()
        self.translateDefaultDBPath = 'Resources/Databases/SkillDescriptTranslate.json'
        self.reSrcPathPattern = self.leeCommon.normPattern(r'^.*?/Patches/.*?/Resource/Original/data/luafiles514/lua files/skillinfoz/skilldescript\.(lua|lub)')
        self.reDstPathPattern = self.leeCommon.normPattern(r'(^.*?/Patches/.*?/Resource)/Original/(data/luafiles514/lua files/skillinfoz/skilldescript\.(lua|lub))')

    def translate(self, srcFilepath, dstFilepath):
        self.leeFileIO.load(srcFilepath)
        for skillConstant in self.leeFileIO.items():
            if str(skillConstant) not in self.translateMap: continue
            skillTranslateData = self.translateMap[str(skillConstant)]
            if 'Description' in skillTranslateData:
                skillDescriptText = '\r\n'.join(skillTranslateData['Description'])
                self.leeFileIO.setItemAttribute(skillConstant, 'Description', skillDescriptText)
        self.leeFileIO.save(dstFilepath)
