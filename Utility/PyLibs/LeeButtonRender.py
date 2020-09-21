# -*- coding: utf-8 -*-

import contextlib
import json
import os
import shutil
import tempfile

from PIL import Image, ImageChops

from PyLibs import LeeCommon

with contextlib.redirect_stdout(None):
    import pygame

class LeeButtonRender:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.btnConfigure = {}
        self.fontPathMap = {}
        pygame.font.init()

    def autoCrop(self, image, backgroundColor = None):
        '''Intelligent automatic image cropping.
            This functions removes the usless "white" space around an image.
            If the image has an alpha (tranparency) channel, it will be used
            to choose what to crop.
            Otherwise, this function will try to find the most popular color
            on the edges of the image and consider this color "whitespace".
            (You can override this color with the backgroundColor parameter)
            Input:
                image (a PIL Image object): The image to crop.
                backgroundColor (3 integers tuple): eg. (0,0,255)
                    The color to consider "background to crop".
                    If the image is transparent, this parameters will be ignored.
                    If the image is not transparent and this parameter is not
                    provided, it will be automatically calculated.
            Output:
                a PIL Image object : The cropped image.
        '''

        def mostPopularEdgeColor(image):
            ''' Compute who's the most popular color on the edges of an image.
                (left,right,top,bottom)
                Input:
                    image: a PIL Image object
                Ouput:
                    The most popular color (A tuple of integers (R,G,B))
            '''
            im = image
            if im.mode != 'RGB':
                im = image.convert('RGB')
            # Get pixels from the edges of the image:
            width,height = im.size
            left  = im.crop((0,1,1,height-1))
            right = im.crop((width-1,1,width,height-1))
            top  = im.crop((0,0,width,1))
            bottom = im.crop((0,height-1,width,height))
            pixels = left.tostring() + right.tostring() + top.tostring() + bottom.tostring()
            # Compute who's the most popular RGB triplet
            counts = {}
            for i in range(0,len(pixels),3):
                RGB = pixels[i]+pixels[i+1]+pixels[i+2]
                if RGB in counts:
                    counts[RGB] += 1
                else:
                    counts[RGB] = 1
            # Get the colour which is the most popular:
            mostPopularColor = sorted(
                [(count,rgba) for (rgba,count) in counts.items()], reverse=True
            )[0][1]
            return ord(mostPopularColor[0]),ord(mostPopularColor[1]),ord(mostPopularColor[2])
        bbox = None
        # If the image has an alpha (tranparency) layer, we use it to crop the image.
        # Otherwise, we look at the pixels around the image (top, left, bottom and right)
        # and use the most used color as the color to crop.
        # --- For transparent images -----------------------------------------------
        if 'A' in image.getbands(): # If the image has a transparency layer, use it.
            # This works for all modes which have transparency layer
            bbox = image.split()[list(image.getbands()).index('A')].getbbox()
        # --- For non-transparent images -------------------------------------------
        elif image.mode=='RGB':
            if not backgroundColor:
                backgroundColor = mostPopularEdgeColor(image)
            # Crop a non-transparent image.
            # .getbbox() always crops the black color.
            # So we need to substract the "background" color from our image.
            bg = Image.new('RGB', image.size, backgroundColor)
            diff = ImageChops.difference(image, bg) # Substract background color from image
            bbox = diff.getbbox() # Try to find the real bounding box of the image.
        else:
            raise NotImplementedError(
                "Sorry, this function is not implemented yet for images in mode '%s'." % image.mode
            )
        if bbox:
            image = image.crop(bbox)
        return image

    def createButtonImage(self, tplName, btnState, btnText, btnWidth):
        self.btnConfigure = self.__loadButtonConfigure(tplName)
        globalOffsetX = int(self.__getButtonConfigureValue(btnState, 'globalOffset').split(',')[0])
        globalOffsetY = int(self.__getButtonConfigureValue(btnState, 'globalOffset').split(',')[1])

        imgButton = self.createButtonBackgroundImage(tplName, btnState, btnWidth)
        imgText = self.createTextImage(btnText, btnState)

        imgButtonWidth, imgButtonHeight = imgButton.size
        imgTextWidth, imgTextHeight = imgText.size

        pasteRect = (
            ((imgButtonWidth - imgTextWidth) // 2) + globalOffsetX,
            ((imgButtonHeight - imgTextHeight) // 2) + globalOffsetY,
            (((imgButtonWidth - imgTextWidth) // 2) + imgTextWidth) + globalOffsetX,
            (((imgButtonHeight - imgTextHeight) // 2) + imgTextHeight) + globalOffsetY
        )

        imgButton = imgButton.convert('RGB')
        imgButton.paste(imgText, pasteRect, mask = imgText)

        return imgButton

    def createButtonBmpFile(self, tplName, btnState, btnText, btnWidth, savePath):
        btnImage = self.createButtonImage(tplName, btnState, btnText, btnWidth)
        btnImage.save(os.path.abspath(savePath), 'bmp')
        return True

    def createButtonBackgroundImage(self, tplName, btnState, btnWidth):
        pathLeftPiece = self.getButtonTemplatePath(tplName, btnState, 'left')
        pathMidPiece = self.getButtonTemplatePath(tplName, btnState, 'mid')
        pathRightPiece = self.getButtonTemplatePath(tplName, btnState, 'right')

        imgLeftPiece = Image.open(pathLeftPiece)
        imgMidPiece = Image.open(pathMidPiece)
        imgRightPiece = Image.open(pathRightPiece)

        imgLeftWidth, imgLeftHeight = imgLeftPiece.size
        imgMidWidth, imgMidHeight = imgMidPiece.size
        imgRightWidth, imgRightHeight = imgRightPiece.size

        if not imgLeftHeight == imgMidHeight == imgRightHeight:
            print('左中右三张切图文件的高度必须完全匹配')

        # 解析来开始拼接按钮的背景图片
        # 建立一个 btnWidth x imgLeftHeight 的图片对象, 底色用 RO 的透明色 FF40FF
        imgButton = Image.new('RGBA', (btnWidth, imgLeftHeight), '#FF40FF')

        # 将中间的图片填满除了左右两侧之外的中央的区域
        midSpace = btnWidth - imgLeftWidth - imgRightWidth
        repeatTime = 0
        while midSpace > 0:
            left = imgLeftWidth + (imgMidWidth * repeatTime)
            imgButton.paste(imgMidPiece, (left, 0, left + imgMidWidth, imgMidHeight))
            repeatTime = repeatTime + 1
            midSpace = midSpace - imgMidWidth

        # 将左侧的图片填充到按钮背景的最左侧
        imgButton.paste(imgLeftPiece, (0, 0, imgLeftWidth, imgLeftHeight))

        # 将右侧的图片填充到按钮背景的最右侧
        imgButton.paste(imgRightPiece, (btnWidth - imgRightWidth, 0, btnWidth, imgRightHeight))

        # 尝试进行一些资源文件的释放, 但这里不会去释放 imgButton
        imgLeftPiece.close()
        imgMidPiece.close()
        imgRightPiece.close()

        return imgButton

    def createTextImage(self, btnText, btnState):
        fontName, fontSize = self.__getButtonFontInfomation()
        fontPath = self.getFontPath(fontName)
        foreFontColor = self.leeCommon.strHexToRgb(
            self.__getButtonConfigureValue(btnState, 'fontColor')
        )
        shadowFontColor = self.leeCommon.strHexToRgb(
            self.__getButtonConfigureValue(btnState, 'shadowColor')
        )
        shadowFontAlpha = int(self.__getButtonConfigureValue(btnState, 'shadowAlpha'))

        # 根据不同的阴影类型, 进行渲染
        if self.__getButtonConfigureValue(btnState, 'shadowMode') == 'offset':

            # 进行前端文字的渲染
            pygameForeFont = pygame.font.Font(fontPath, fontSize)
            pygameForeText = pygameForeFont.render(btnText, True, foreFontColor)
            pyForeTextStor = pygame.image.tostring(pygameForeText, 'RGBA', False)
            imgForeText = Image.frombytes('RGBA', pygameForeText.get_size(), pyForeTextStor)
            imgForeText = self.autoCrop(imgForeText)

            # 进行阴影字体的渲染
            pygameBackFont = pygame.font.Font(fontPath, fontSize)
            pygameBackText = pygameBackFont.render(btnText, True, shadowFontColor)
            pyBackTextStor = pygame.image.tostring(pygameBackText, 'RGBA', False)
            imgBackText = Image.frombytes('RGBA', pygameBackText.get_size(), pyBackTextStor)
            imgBackText = self.autoCrop(imgBackText)

            # 对阴影字体应用指定透明度
            _red, _green, _blue, alpha = imgBackText.split()
            alpha = alpha.point(lambda i: i > 0 and (255 / 100) * shadowFontAlpha)
            imgBackText.putalpha(alpha)

            # 文字的阴影的偏移叠加处理过程
            shadowOffsetX = int(self.__getButtonConfigureValue(
                btnState, 'shadowOffset'
            ).split(',')[0])
            shadowOffsetY = int(self.__getButtonConfigureValue(
                btnState, 'shadowOffset'
            ).split(',')[1])
            boardWidth = imgForeText.size[0] + abs(shadowOffsetX)
            boardHeight = imgForeText.size[1] + abs(shadowOffsetY)
            foreOffsetX = 0 if self.leeCommon.isPositive(shadowOffsetX) else abs(shadowOffsetX)
            foreOffsetY = 0 if self.leeCommon.isPositive(shadowOffsetY) else abs(shadowOffsetY)
            shadowOffsetX = 0 if not self.leeCommon.isPositive(shadowOffsetX) else shadowOffsetX
            shadowOffsetY = 0 if not self.leeCommon.isPositive(shadowOffsetY) else shadowOffsetY

            imgMergeText = Image.new('RGBA', (boardWidth, boardHeight), (0,0,0,0))
            imgMergeText.paste(imgBackText, (shadowOffsetX, shadowOffsetY))
            imgMergeText.paste(imgForeText, (foreOffsetX, foreOffsetY), mask = imgForeText)

            return imgMergeText

        elif self.__getButtonConfigureValue(btnState, 'shadowMode') == 'outline':

            outFont = pygame.font.Font(fontPath, fontSize + 2)
            imgSurface = pygame.Surface(outFont.size(btnText), pygame.SRCALPHA)
            innerFont = pygame.font.Font(fontPath, fontSize)
            outline = innerFont.render(btnText, 1, shadowFontColor)

            w, h = imgSurface.get_size()
            ww, hh = outline.get_size()
            cx = w/2 - ww/2
            cy = h/2 - hh/2

            for x in range(-1,2):
                for y in range(-1,2):
                    imgSurface.blit(outline, (x+cx, y+cy))

            imgSurface.blit(innerFont.render(btnText, 1, foreFontColor), (cx,cy))
            imgSurfaceTextStor = pygame.image.tostring(imgSurface, 'RGBA', False)
            imgFinalText = Image.frombytes('RGBA', imgSurface.get_size(), imgSurfaceTextStor)
            imgFinalText = self.autoCrop(imgFinalText)

            return imgFinalText

    def getButtonTemplatePath(self, tplName, btnState, piece):
        return os.path.abspath('%s/Resources/Texture/Button/Style_%s/%s_%s.png' % (
            self.leeCommon.utility(withmark=False), tplName, btnState, piece
        ))

    def getFontPath(self, fontFilename):
        if fontFilename in self.fontPathMap:
            return self.fontPathMap[fontFilename]

        fontOriginPath = os.path.abspath('%s/Resources/Fonts/%s' % (
            self.leeCommon.utility(withmark=False), fontFilename
        ))

        # 把字体文件复制到系统临时目录, 以便确保路径没有任何中文
        fontTempPath = tempfile.mktemp(prefix = 'leefont_', suffix = '.ttc')
        shutil.copyfile(fontOriginPath, fontTempPath)

        # 记住临时字体文件的路径避免重复复制
        self.fontPathMap[fontFilename] = fontTempPath
        return fontTempPath

    def getImageSizeByFilepath(self, filepath):
        img = Image.open(filepath)
        imgsize = img.size
        img.close()
        return imgsize

    def __loadButtonConfigure(self, tplName):
        configurePath = (
            '%s/Resources/Texture/Button/Style_%s/configure.json' % (
                self.leeCommon.utility(withmark=False), tplName
            )
        )
        return (
            json.load(open(configurePath, 'r'))
            if self.leeCommon.isFileExists(configurePath) else None
        )

    def __getButtonFontInfomation(self):
        if self.btnConfigure:
            return self.btnConfigure['fontName'], int(self.btnConfigure['fontSize'])
        else:
            self.leeCommon.exitWithMessage('__getButtonFontInfomation: 无法加载字体的配置信息')
            return None, None

    def __getButtonConfigureValue(self, btnState, attrib):
        if self.btnConfigure:
            return self.btnConfigure[btnState][attrib]
        else:
            self.leeCommon.exitWithMessage('__getButtonConfigureValue: 无法加载字体的配置信息')
            return None, None
