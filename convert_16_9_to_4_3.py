#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图像比例转换工具
将16:9的图片转换为4:3比例，使用背景模糊效果
处理方法：将原图放大填满4:3画幅并模糊化作为背景，然后将原图适应放在中间位置
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageFilter


def convert_16_9_to_4_3(image_path):
    """
    将16:9的图片转换为4:3比例
    
    参数:
        image_path: 图片路径（字符串或Path对象）
    
    返回:
        输出文件的路径，如果失败返回None
    """
    # 转换为Path对象
    image_path = Path(image_path)
    
    # 检查文件是否存在
    if not image_path.exists():
        print(f"错误：文件不存在 - {image_path}")
        return None
    
    # 检查是否为图片文件
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif'}
    if image_path.suffix.lower() not in valid_extensions:
        print(f"错误：不支持的图片格式 - {image_path.suffix}")
        return None
    
    try:
        # 打开原始图片
        original_image = Image.open(image_path)
        original_width, original_height = original_image.size
        
        # 计算原始图片的宽高比
        original_ratio = original_width / original_height
        
        # 计算目标4:3比例的尺寸
        # 保持原图的高度，计算4:3的宽度
        target_ratio = 4 / 3
        
        if original_ratio > target_ratio:
            # 原图更宽，以高度为准
            target_height = original_height
            target_width = int(target_height * target_ratio)
        else:
            # 原图更高，以宽度为准
            target_width = original_width
            target_height = int(target_width / target_ratio)
        
        # 创建4:3的画布
        canvas = Image.new('RGB', (target_width, target_height), (0, 0, 0))
        
        # 步骤1：将原图放大填满4:3画幅（作为背景）
        # 计算缩放比例，使图片能够完全覆盖4:3画幅
        scale_x = target_width / original_width
        scale_y = target_height / original_height
        scale = max(scale_x, scale_y)  # 取较大的缩放比例以确保完全覆盖
        
        background_width = int(original_width * scale)
        background_height = int(original_height * scale)
        
        # 放大原图作为背景
        background = original_image.resize(
            (background_width, background_height),
            Image.Resampling.LANCZOS
        )
        
        # 居中裁剪背景到目标尺寸
        left = (background_width - target_width) // 2
        top = (background_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        background = background.crop((left, top, right, bottom))
        
        # 步骤2：模糊化背景
        background = background.filter(ImageFilter.GaussianBlur(radius=20))
        
        # 将模糊的背景粘贴到画布上
        canvas.paste(background, (0, 0))
        
        # 步骤3：将原图适应放在中间位置
        # 计算原图在4:3画幅中的适应尺寸（保持宽高比，尽可能大但不超出画幅）
        if original_ratio > target_ratio:
            # 原图更宽，以宽度为准适应（确保不超出画幅宽度）
            fit_width = int(target_width * 0.95)  # 留5%边距
            fit_height = int(fit_width / original_ratio)
        else:
            # 原图更高，以高度为准适应（确保不超出画幅高度）
            fit_height = int(target_height * 0.95)  # 留5%边距
            fit_width = int(fit_height * original_ratio)
        
        # 调整原图大小以适应
        fitted_image = original_image.resize(
            (fit_width, fit_height),
            Image.Resampling.LANCZOS
        )
        
        # 计算居中位置
        paste_x = (target_width - fit_width) // 2
        paste_y = (target_height - fit_height) // 2
        
        # 将原图粘贴到画布中间（如果原图有透明通道，需要处理）
        if fitted_image.mode == 'RGBA':
            canvas.paste(fitted_image, (paste_x, paste_y), fitted_image)
        else:
            canvas.paste(fitted_image, (paste_x, paste_y))
        
        # 生成输出文件名（在原文件名基础上添加后缀）
        output_path = image_path.parent / f"{image_path.stem}_4_3{image_path.suffix}"
        
        # 保存图片
        canvas.save(output_path, quality=95)
        
        print(f"成功：已生成4:3比例的图片 - {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"错误：处理图片时发生异常 - {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python convert_16_9_to_4_3.py <图片路径>")
        print("示例: python convert_16_9_to_4_3.py /path/to/image.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    result = convert_16_9_to_4_3(image_path)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

