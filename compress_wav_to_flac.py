#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WAV转FLAC压缩脚本
将WAV文件压缩为FLAC格式，保持无损音质的同时减小文件大小
支持 Windows 和 Linux 平台
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


def find_ffmpeg_path():
    """查找ffmpeg路径"""
    is_windows = platform.system() == "Windows"
    exe_ext = ".exe" if is_windows else ""
    
    # 首先检查系统 PATH 中是否有 ffmpeg
    ffmpeg_cmd = shutil.which("ffmpeg")
    ffprobe_cmd = shutil.which("ffprobe")
    if ffmpeg_cmd and ffprobe_cmd:
        # 如果系统中有 ffmpeg，返回其目录
        return os.path.dirname(ffmpeg_cmd)
    
    # 常见的ffmpeg路径位置
    possible_paths = [
        Path("ffmpeg/bin"),  # 当前目录下的ffmpeg/bin
        Path("ffmpeg"),      # 当前目录下的ffmpeg
        Path("bin"),         # 当前目录下的bin
    ]
    
    # 检查每个可能的路径
    for path in possible_paths:
        ffmpeg_exe = path / f"ffmpeg{exe_ext}"
        ffprobe_exe = path / f"ffprobe{exe_ext}"
        if ffmpeg_exe.exists() and ffprobe_exe.exists():
            return str(path.absolute())
    
    # 如果在常见位置找不到，尝试搜索整个目录
    current_dir = Path(".")
    for ffmpeg_file in current_dir.rglob(f"ffmpeg{exe_ext}"):
        parent_dir = ffmpeg_file.parent
        if (parent_dir / f"ffprobe{exe_ext}").exists():
            return str(parent_dir.absolute())
    
    return None


def find_wav_file(wav_path):
    """查找WAV文件，处理路径中的特殊字符和编码问题
    
    Args:
        wav_path: WAV文件路径（可能是用户输入的路径）
    
    Returns:
        Path对象，如果找到文件；否则返回None
    """
    # 移除路径中的引号（如果用户用引号包裹路径）
    clean_path = wav_path.strip('"\'')
    
    # 尝试多种方法查找文件
    methods = [
        # 方法1: 直接使用路径
        lambda: Path(clean_path) if Path(clean_path).exists() and Path(clean_path).is_file() else None,
        # 方法2: 使用绝对路径
        lambda: Path(clean_path).resolve() if Path(clean_path).resolve().exists() and Path(clean_path).resolve().is_file() else None,
        # 方法3: 使用os.path规范化（对Windows路径更友好）
        lambda: Path(os.path.normpath(clean_path)) if Path(os.path.normpath(clean_path)).exists() and Path(os.path.normpath(clean_path)).is_file() else None,
    ]
    
    for method in methods:
        try:
            result = method()
            if result:
                return result
        except Exception:
            continue
    
    # 如果路径指向的是目录，尝试在该目录中查找wav文件
    try:
        test_path = Path(clean_path)
        if test_path.exists() and test_path.is_dir():
            # 查找目录中的所有wav文件
            wav_files = list(test_path.glob("*.wav"))
            if len(wav_files) == 1:
                print(f"提示: 在目录中找到WAV文件: {wav_files[0]}")
                return wav_files[0]
            elif len(wav_files) > 1:
                print(f"提示: 在目录中找到多个WAV文件，使用第一个: {wav_files[0].name}")
                for i, f in enumerate(wav_files[:5], 1):  # 只显示前5个
                    print(f"  {i}. {f.name}")
                return wav_files[0]
    except Exception:
        pass
    
    # 如果路径是文件路径但不存在，尝试在父目录中查找
    try:
        parent_dir = Path(clean_path).parent
        if parent_dir.exists() and parent_dir.is_dir():
            # 查找目录中的所有wav文件
            wav_files = list(parent_dir.glob("*.wav"))
            if len(wav_files) == 1:
                print(f"提示: 在父目录中找到WAV文件: {wav_files[0]}")
                return wav_files[0]
            elif len(wav_files) > 1:
                # 尝试匹配文件名（不区分大小写）
                input_name = Path(clean_path).stem.lower().replace(" ", "").replace("_", "").replace("-", "")
                best_match = None
                best_score = 0
                
                for wav_file in wav_files:
                    file_name = wav_file.stem.lower().replace(" ", "").replace("_", "").replace("-", "")
                    # 计算匹配度
                    if input_name in file_name or file_name in input_name:
                        score = min(len(input_name), len(file_name)) / max(len(input_name), len(file_name), 1)
                        if score > best_score:
                            best_score = score
                            best_match = wav_file
                
                if best_match:
                    print(f"提示: 找到匹配的WAV文件: {best_match}")
                    return best_match
                else:
                    # 如果没找到匹配的，返回第一个
                    print(f"提示: 在父目录中找到多个WAV文件，使用第一个: {wav_files[0]}")
                    return wav_files[0]
    except Exception:
        pass
    
    return None


def compress_wav_to_flac(wav_path, ffmpeg_path=None, compression_level=12):
    """将WAV文件压缩为FLAC格式
    
    Args:
        wav_path: WAV文件路径
        ffmpeg_path: ffmpeg路径（可选）
        compression_level: FLAC压缩级别（0-12，默认12，12是最高压缩/最小文件）
    """
    # 查找WAV文件
    wav_file = find_wav_file(wav_path)
    
    if not wav_file:
        print(f"错误: 无法找到WAV文件: {wav_path}")
        print("\n提示:")
        print("  1. 请检查文件路径是否正确")
        print("  2. 确保文件确实存在")
        print("  3. 如果路径包含特殊字符，请使用引号包裹路径")
        print("  4. 可以尝试使用相对路径或只提供目录路径（如果目录中只有一个wav文件）")
        sys.exit(1)
    
    print(f"找到WAV文件: {wav_file}")
    
    # 检查WAV文件是否存在
    if not wav_file.exists():
        print(f"错误: WAV文件不存在: {wav_file}")
        sys.exit(1)
    
    # 获取WAV文件的绝对路径
    wav_abs_path = wav_file.resolve()
    
    # 获取WAV文件名（不含扩展名）
    wav_stem = wav_file.stem
    
    # 查找ffmpeg
    if not ffmpeg_path:
        ffmpeg_path = find_ffmpeg_path()
    
    if not ffmpeg_path:
        print("错误: 未找到ffmpeg，无法压缩WAV文件")
        sys.exit(1)
    
    is_windows = platform.system() == "Windows"
    exe_ext = ".exe" if is_windows else ""
    ffmpeg_exe = Path(ffmpeg_path) / f"ffmpeg{exe_ext}"
    
    # 如果路径是目录，检查其中的可执行文件
    if not ffmpeg_exe.exists():
        # 可能 ffmpeg_path 本身就是可执行文件的路径
        if os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
            ffmpeg_exe = Path(ffmpeg_path)
        else:
            print(f"错误: ffmpeg{exe_ext}不存在: {ffmpeg_exe}")
            sys.exit(1)
    
    # 验证压缩级别
    compression_level = max(0, min(12, int(compression_level)))
    
    # 输出文件路径：与源文件同目录，扩展名改为.flac
    output_file = wav_file.parent / f"{wav_stem}.flac"
    
    # 构建ffmpeg命令
    # -i: 输入文件
    # -c:a flac: 使用flac编码器
    # -compression_level: FLAC压缩级别（0-12，12是最高压缩/最小文件，但处理时间最长）
    # -y: 如果输出文件已存在则覆盖
    cmd = [
        str(ffmpeg_exe.absolute()),
        "-i", str(wav_abs_path),
        "-c:a", "flac",  # 音频编码器为flac
        "-compression_level", str(compression_level),  # FLAC压缩级别（0-12）
        "-y",  # 覆盖已存在的输出文件
        str(output_file.absolute())
    ]
    
    return cmd, str(output_file.absolute())


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python compress_wav_to_flac.py <WAV文件路径> [压缩级别]")
        print("示例: python compress_wav_to_flac.py audio.wav")
        print("示例: python compress_wav_to_flac.py audio.wav 12")
        print("示例: python compress_wav_to_flac.py download/audio/audio.wav")
        print("\n压缩级别说明:")
        print("  0-12: FLAC压缩级别（默认12）")
        print("  0: 最快，文件最大")
        print("  12: 最慢，文件最小（推荐）")
        sys.exit(1)
    
    wav_path = sys.argv[1]
    
    # 解析压缩级别参数（可选）
    compression_level = 12  # 默认最高压缩级别
    if len(sys.argv) >= 3:
        try:
            compression_level = int(sys.argv[2])
            if compression_level < 0 or compression_level > 12:
                print(f"警告: 压缩级别必须在0-12之间，使用默认值12")
                compression_level = 12
        except ValueError:
            print(f"警告: 无效的压缩级别 '{sys.argv[2]}'，使用默认值12")
            compression_level = 12
    
    # 查找ffmpeg路径
    print("正在查找ffmpeg...")
    ffmpeg_path = find_ffmpeg_path()
    if ffmpeg_path:
        print(f"找到ffmpeg: {ffmpeg_path}")
    else:
        print("错误: 未找到ffmpeg，无法压缩WAV文件")
        sys.exit(1)
    
    # 压缩WAV文件
    print(f"正在压缩WAV文件: {wav_path}")
    print(f"压缩级别: {compression_level} (0=最快/最大文件, 12=最慢/最小文件)")
    cmd, output_file = compress_wav_to_flac(wav_path, ffmpeg_path, compression_level)
    
    print(f"输出文件: {output_file}")
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        # 显示文件大小信息
        if Path(output_file).exists():
            wav_size = Path(wav_path).stat().st_size / (1024 * 1024)
            flac_size = Path(output_file).stat().st_size / (1024 * 1024)
            compression_ratio = (1 - flac_size / wav_size) * 100 if wav_size > 0 else 0
            
            print(f"\n压缩完成！")
            print(f"输出文件: {output_file}")
            print(f"原始大小: {wav_size:.2f} MB")
            print(f"压缩后大小: {flac_size:.2f} MB")
            print(f"压缩率: {compression_ratio:.1f}%")
    except subprocess.CalledProcessError as e:
        print(f"\n压缩WAV文件时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

