# -*- coding: utf-8 -*-

from PyLibs import LeeBaseTranslator, LeeSkillinfolistLua


class LeeSkillinfolistTranslator(LeeBaseTranslator):
    def __init__(self):
        LeeBaseTranslator.__init__(self)
        self.leeFileIO = LeeSkillinfolistLua()
        self.translateDefaultDBPath = 'Resources/Databases/SkillDescriptTranslate.json'
        self.reSrcPathPattern = self.leeCommon.normPattern(r'^.*?/Patches/.*?/Resource/Original/data/luafiles514/lua files/skillinfoz/skillinfolist\.(lua|lub)')
        self.reDstPathPattern = self.leeCommon.normPattern(r'(^.*?/Patches/.*?/Resource)/Original/(data/luafiles514/lua files/skillinfoz/skillinfolist\.(lua|lub))')

    def translate(self, srcFilepath, dstFilepath):
        self.leeFileIO.load(srcFilepath)
        for skillConstant in self.leeFileIO.items():
            if str(skillConstant) not in self.translateMap: continue
            skillTranslateData = self.translateMap[str(skillConstant)]
            self.leeFileIO.setItemAttribute(skillConstant, 'SkillName', skillTranslateData['SkillName'])
        self.leeFileIO.save(dstFilepath)
