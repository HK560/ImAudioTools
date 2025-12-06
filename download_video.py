#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YouTube视频下载脚本
使用yt-dlp.exe下载视频，支持从config.cfg读取配置
"""

import json
import os
import sys
import subprocess
from pathlib import Path


def load_config(config_path="config.cfg"):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 移除末尾可能的逗号，修复JSON格式
            content = content.rstrip()
            if content.endswith(',}'):
                content = content[:-2] + '}'
            elif content.endswith(',\n}'):
                content = content[:-3] + '\n}'
            config = json.loads(content)
        return config
    except FileNotFoundError:
        print(f"错误: 配置文件 {config_path} 不存在")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件格式不正确: {e}")
        sys.exit(1)


def ensure_download_dir():
    """确保下载目录存在"""
    download_dir = Path("download")
    download_dir.mkdir(exist_ok=True)
    return str(download_dir.absolute())


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


def build_ytdlp_command(video_url, config, download_dir, ffmpeg_path=None):
    """构建yt-dlp命令"""
    ytdlp_exe = Path("yt-dlp.exe")
    
    if not ytdlp_exe.exists():
        print(f"错误: {ytdlp_exe} 不存在")
        sys.exit(1)
    
    cmd = [str(ytdlp_exe.absolute())]
    
    # 设置代理
    if config.get("proxy"):
        cmd.extend(["--proxy", config["proxy"]])
    
    # 设置ffmpeg路径（如果找到）
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
    
    # 设置输出目录和文件名格式
    # 格式: download/<视频名>/<视频名>.<扩展名>
    # yt-dlp会自动创建文件夹并清理文件名中的非法字符（保留中文等字符）
    cmd.extend(["-o", os.path.join(download_dir, "%(title)s", "%(title)s.%(ext)s")])
    
    # 下载视频封面图片（最佳质量）
    cmd.append("--write-thumbnail")
    # 将缩略图转换为JPG格式（更通用）
    cmd.extend(["--convert-thumbnails", "jpg"])
    
    # 如果isCombineVideo为True，下载最佳视频+音频并合并
    if config.get("isCombineVideo", False):
        # 下载最佳视频格式（视频+音频合并）
        cmd.extend(["-f", "bestvideo+bestaudio/best"])
        # 确保合并视频
        cmd.append("--merge-output-format")
        cmd.append("mp4")
    else:
        # 只下载最佳视频
        cmd.extend(["-f", "best"])
    
    # 如果sperateAudio为True，额外下载音频文件
    if config.get("sperateAudio", False):
        # 先下载视频
        # 然后下载音频
        # 由于yt-dlp一次只能执行一个操作，我们需要两次调用
        # 或者使用postprocessor，但更简单的方法是先下载视频，再下载音频
        pass  # 这个会在主函数中处理
    
    # 添加视频URL
    cmd.append(video_url)
    
    return cmd


def download_audio(video_url, config, download_dir, ffmpeg_path=None):
    """下载音频文件（最高质量无损格式）"""
    ytdlp_exe = Path("yt-dlp.exe")
    cmd = [str(ytdlp_exe.absolute())]
    
    # 设置代理
    if config.get("proxy"):
        cmd.extend(["--proxy", config["proxy"]])
    
    # 设置ffmpeg路径（如果找到）
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
    
    # 获取最佳音频质量
    # 优先选择最高比特率的音频格式（m4a通常质量最高），然后回退到其他最佳格式
    # 使用 abr>128 确保选择高质量音频
    cmd.extend(["-f", "bestaudio[ext=m4a][abr>128]/bestaudio[abr>128]/bestaudio[ext=m4a]/bestaudio/best"])
    
    # 提取音频，转换为无损格式
    # 从配置中读取音频格式，默认为flac（压缩无损，文件更小）
    audio_format = config.get("audioFormat", "flac").lower()
    if audio_format not in ["flac", "wav"]:
        print(f"警告: 不支持的音频格式 {audio_format}，使用 flac")
        audio_format = "flac"
    
    cmd.extend(["-x", "--audio-format", audio_format])
    
    # 确保最高质量（对无损格式可能不需要，但加上更保险）
    cmd.extend(["--audio-quality", "0"])
    
    # 设置输出目录和文件名格式
    # 格式: download/<视频名>/<视频名>.<扩展名>
    # yt-dlp会自动创建文件夹并清理文件名中的非法字符（保留中文等字符）
    cmd.extend(["-o", os.path.join(download_dir, "%(title)s", "%(title)s.%(ext)s")])
    
    # 添加视频URL
    cmd.append(video_url)
    
    return cmd


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python download_video.py <视频URL>")
        print("示例: python download_video.py https://www.youtube.com/watch?v=VIDEO_ID")
        sys.exit(1)
    
    video_url = sys.argv[1]
    
    # 加载配置
    print("正在加载配置...")
    config = load_config()
    
    # 查找ffmpeg路径
    print("正在查找ffmpeg...")
    ffmpeg_path = find_ffmpeg_path()
    if ffmpeg_path:
        print(f"找到ffmpeg: {ffmpeg_path}")
    else:
        print("警告: 未找到ffmpeg，视频合并和音频转换功能可能无法使用")
    
    # 确保下载目录存在
    download_dir = ensure_download_dir()
    print(f"下载目录: {download_dir}")
    
    # 构建并执行下载命令
    print(f"正在下载视频和封面图片: {video_url}")
    cmd = build_ytdlp_command(video_url, config, download_dir, ffmpeg_path)
    
    print(f"执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("视频和封面图片下载完成！")
    except subprocess.CalledProcessError as e:
        print(f"下载视频时出错: {e}")
        sys.exit(1)
    
    # 如果需要分离音频
    if config.get("sperateAudio", False):
        audio_format = config.get("audioFormat", "flac").upper()
        print(f"正在下载最高质量无损音频文件（格式: {audio_format}）...")
        if not ffmpeg_path:
            print("警告: 未找到ffmpeg，无法转换为无损格式，将下载原始音频")
        audio_cmd = download_audio(video_url, config, download_dir, ffmpeg_path)
        print(f"执行命令: {' '.join(audio_cmd)}")
        try:
            result = subprocess.run(audio_cmd, check=True, capture_output=False)
            print(f"无损音频下载完成！（格式: {audio_format}）")
        except subprocess.CalledProcessError as e:
            print(f"下载音频时出错: {e}")
            # 音频下载失败不影响主流程，只警告


if __name__ == "__main__":
    main()

