#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频音频提取脚本
使用ffmpeg从视频文件中提取音频，输出为无损FLAC格式
"""

import os
import sys
import subprocess
from pathlib import Path


def find_ffmpeg_path():
    """查找ffmpeg路径"""
    # 常见的ffmpeg路径位置
    possible_paths = [
        Path("ffmpeg/bin"),  # 当前目录下的ffmpeg/bin
        Path("ffmpeg"),      # 当前目录下的ffmpeg
        Path("bin"),         # 当前目录下的bin
    ]
    
    # 检查每个可能的路径
    for path in possible_paths:
        ffmpeg_exe = path / "ffmpeg.exe"
        ffprobe_exe = path / "ffprobe.exe"
        if ffmpeg_exe.exists() and ffprobe_exe.exists():
            return str(path.absolute())
    
    # 如果在常见位置找不到，尝试搜索整个目录
    current_dir = Path(".")
    for ffmpeg_dir in current_dir.rglob("ffmpeg.exe"):
        parent_dir = ffmpeg_dir.parent
        if (parent_dir / "ffprobe.exe").exists():
            return str(parent_dir.absolute())
    
    return None


def ensure_download_dir():
    """确保下载目录存在"""
    download_dir = Path("download")
    download_dir.mkdir(exist_ok=True)
    return str(download_dir.absolute())


def extract_audio_from_video(video_path, ffmpeg_path=None, compression_level=12):
    """从视频文件中提取音频为FLAC格式
    
    Args:
        video_path: 视频文件路径
        ffmpeg_path: ffmpeg路径（可选）
        compression_level: FLAC压缩级别（0-12，默认12，12是最高压缩/最小文件）
    """
    video_file = Path(video_path)
    
    # 检查视频文件是否存在
    if not video_file.exists():
        print(f"错误: 视频文件不存在: {video_path}")
        sys.exit(1)
    
    # 获取视频文件的绝对路径
    video_abs_path = video_file.resolve()
    
    # 获取视频文件名（不含扩展名）作为输出文件夹名
    video_stem = video_file.stem
    
    # 确保download目录存在
    download_dir = Path(ensure_download_dir())
    
    # 创建输出目录: download/<源文件名>
    output_dir = download_dir / video_stem
    output_dir.mkdir(exist_ok=True)
    
    # 输出文件路径: download/<源文件名>/<源文件名>.flac
    output_file = output_dir / f"{video_stem}.flac"
    
    # 查找ffmpeg
    if not ffmpeg_path:
        ffmpeg_path = find_ffmpeg_path()
    
    if not ffmpeg_path:
        print("错误: 未找到ffmpeg，无法提取音频")
        sys.exit(1)
    
    ffmpeg_exe = Path(ffmpeg_path) / "ffmpeg.exe"
    if not ffmpeg_exe.exists():
        print(f"错误: ffmpeg.exe不存在: {ffmpeg_exe}")
        sys.exit(1)
    
    # 验证压缩级别
    compression_level = max(0, min(12, int(compression_level)))
    
    # 构建ffmpeg命令
    # -i: 输入文件
    # -vn: 不包含视频流
    # -c:a flac: 使用flac编码器
    # -compression_level: FLAC压缩级别（0-12，12是最高压缩/最小文件，但处理时间最长）
    # -y: 如果输出文件已存在则覆盖
    cmd = [
        str(ffmpeg_exe.absolute()),
        "-i", str(video_abs_path),
        "-vn",  # 不包含视频
        "-c:a", "flac",  # 音频编码器为flac
        "-compression_level", str(compression_level),  # FLAC压缩级别（0-12）
        "-y",  # 覆盖已存在的输出文件
        str(output_file.absolute())
    ]
    
    return cmd, str(output_file.absolute())


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python extract_audio.py <视频文件路径> [压缩级别]")
        print("示例: python extract_audio.py video.mp4")
        print("示例: python extract_audio.py download/video/video.mp4")
        print("示例: python extract_audio.py video.mp4 12")
        print("\n压缩级别说明:")
        print("  0-12: FLAC压缩级别（默认12）")
        print("  0: 最快，文件最大")
        print("  12: 最慢，文件最小（推荐）")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
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
        print("错误: 未找到ffmpeg，无法提取音频")
        sys.exit(1)
    
    # 提取音频
    print(f"正在从视频文件提取音频: {video_path}")
    print(f"压缩级别: {compression_level} (0=最快/最大文件, 12=最慢/最小文件)")
    cmd, output_file = extract_audio_from_video(video_path, ffmpeg_path, compression_level)
    
    print(f"输出文件: {output_file}")
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"音频提取完成！输出文件: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"提取音频时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

