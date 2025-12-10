#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YouTube视频下载脚本
使用yt-dlp下载视频，支持从config.cfg读取配置
支持 Windows 和 Linux 平台
"""

import json
import os
import sys
import subprocess
import platform
import shutil
import time
import glob
from pathlib import Path

# 导入图像转换函数
try:
    from convert_16_9_to_4_3 import convert_16_9_to_4_3
except ImportError:
    # 如果导入失败，定义占位函数
    def convert_16_9_to_4_3(image_path):
        print(f"警告: 无法导入图像转换模块，跳过封面转换")
        return None


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


def ensure_download_dir(config=None):
    """确保下载目录存在
    
    Args:
        config: 配置字典，可包含 downloadDir 字段指定下载目录
    
    Returns:
        str: 下载目录的绝对路径
    """
    # 从配置中读取下载目录
    if config and config.get("downloadDir"):
        download_path = config.get("downloadDir")
        # 尝试使用配置的路径
        try:
            download_dir = Path(download_path)
            # 如果是相对路径，转换为绝对路径
            if not download_dir.is_absolute():
                download_dir = Path.cwd() / download_dir
            # 确保目录存在
            download_dir.mkdir(parents=True, exist_ok=True)
            # 验证目录是否可写
            if download_dir.exists() and download_dir.is_dir() and os.access(download_dir, os.W_OK):
                return str(download_dir.absolute())
            else:
                print(f"警告: 配置的下载目录无效或不可写 '{download_path}'")
                print("使用默认下载目录: download")
        except (OSError, ValueError, PermissionError) as e:
            print(f"警告: 配置的下载目录无效 '{download_path}': {e}")
            print("使用默认下载目录: download")
    
    # 如果配置无效或未配置，使用默认目录
    download_dir = Path("download")
    download_dir.mkdir(exist_ok=True)
    return str(download_dir.absolute())


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


def find_ytdlp():
    """查找yt-dlp可执行文件"""
    # 首先检查系统 PATH 中是否有 yt-dlp
    ytdlp_cmd = shutil.which("yt-dlp")
    if ytdlp_cmd:
        return ytdlp_cmd
    
    # 检查当前目录下的 yt-dlp.exe (Windows) 或 yt-dlp (Linux)
    is_windows = platform.system() == "Windows"
    exe_ext = ".exe" if is_windows else ""
    ytdlp_exe = Path(f"yt-dlp{exe_ext}")
    
    if ytdlp_exe.exists():
        return str(ytdlp_exe.absolute())
    
    return None


def build_ytdlp_command(video_url, config, download_dir, ffmpeg_path=None, download_video=True):
    """构建yt-dlp命令
    
    Args:
        video_url: 视频URL
        config: 配置字典
        download_dir: 下载目录
        ffmpeg_path: ffmpeg路径
        download_video: 是否下载视频（False时只下载音频）
    """
    ytdlp_cmd = find_ytdlp()
    
    if not ytdlp_cmd:
        print("错误: 未找到 yt-dlp，请确保已安装 yt-dlp")
        sys.exit(1)
    
    cmd = [ytdlp_cmd]
    
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
    
    if download_video:
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
            # Hi-Res无损音质要求：视频中的音频采样率不低于48kHz，位深度不低于24bit
            # 使用ALAC（Apple Lossless Audio Codec）无损编码，支持24bit
            # ALAC是MP4容器支持的无损音频格式，满足Hi-Res要求
            # 设置采样率至少48kHz，位深度24bit（ALAC编码器支持s32p格式，32bit可以包含24bit数据）
            cmd.extend(["--postprocessor-args", "ffmpeg:-c:a alac -ar 48000 -sample_fmt s32p"])
            # 注意：ALAC编码器支持s32p（32bit planar）格式，可以编码24bit无损音频
            # 采样率设置为至少48kHz，如果源音频采样率>48kHz会保持原样，如果<48kHz会提升到48kHz
        else:
            # 只下载最佳视频
            cmd.extend(["-f", "best"])
    else:
        # 只下载音频，不下载视频和封面
        pass
    
    # 添加视频URL
    cmd.append(video_url)
    
    return cmd


def find_thumbnail_files(download_dir, video_url=None):
    """
    查找下载的封面图片文件
    
    参数:
        download_dir: 下载目录路径
        video_url: 视频URL（可选，用于更精确查找）
    
    返回:
        封面文件路径列表
    """
    download_path = Path(download_dir)
    thumbnail_files = []
    
    # 支持的封面文件扩展名
    thumbnail_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    # 视频文件扩展名（用于排除）
    video_extensions = ['.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.m4a', '.mp3', '.flac', '.wav']
    
    # 在下载目录的所有子目录中查找封面文件
    # yt-dlp通常将封面保存在视频标题命名的子目录中
    for ext in thumbnail_extensions:
        # 查找所有子目录中的封面文件
        pattern = f"**/*{ext}"
        found_files = list(download_path.glob(pattern))
        
        for file_path in found_files:
            # 排除已经转换过的文件（文件名包含_4_3）
            if '_4_3' in file_path.stem:
                continue
            
            # 确保是图片文件扩展名
            if file_path.suffix.lower() not in thumbnail_extensions:
                continue
            
            # 检查同目录下是否有同名但不同扩展名的视频文件
            # 如果有，说明这是封面文件（因为视频和封面通常同名）
            is_thumbnail = False
            parent_dir = file_path.parent
            base_name = file_path.stem
            
            # 检查是否有同名的视频文件（说明这是封面）
            for video_ext in video_extensions:
                video_file = parent_dir / f"{base_name}{video_ext}"
                if video_file.exists():
                    is_thumbnail = True
                    break
            
            # 如果没有同名视频文件，但文件在子目录中且最近修改，也可能是封面
            # yt-dlp通常将封面和视频放在同一子目录中
            if not is_thumbnail:
                # 检查是否是最近5分钟内创建的文件（可能是刚下载的封面）
                file_mtime = file_path.stat().st_mtime
                current_time = time.time()
                if current_time - file_mtime < 300:  # 5分钟内
                    # 检查父目录中是否有视频文件（任何扩展名）
                    has_video = any(
                        f.suffix.lower() in video_extensions 
                        for f in parent_dir.iterdir() 
                        if f.is_file()
                    )
                    if has_video:
                        is_thumbnail = True
            
            if is_thumbnail:
                thumbnail_files.append(file_path)
    
    # 去重并按修改时间排序（最新的在前）
    thumbnail_files = sorted(set(thumbnail_files), key=lambda p: p.stat().st_mtime, reverse=True)
    
    return thumbnail_files


def convert_thumbnails_to_4_3(download_dir, video_url=None):
    """
    将下载的封面图片转换为4:3比例
    
    参数:
        download_dir: 下载目录路径
        video_url: 视频URL（可选）
    
    返回:
        成功转换的文件数量
    """
    print("正在查找封面图片...")
    
    # 等待一下，确保文件已完全写入
    time.sleep(1)
    
    thumbnail_files = find_thumbnail_files(download_dir, video_url)
    
    if not thumbnail_files:
        print("未找到封面图片文件")
        return 0
    
    converted_count = 0
    for thumbnail_path in thumbnail_files:
        print(f"正在转换封面图片: {thumbnail_path.name}")
        try:
            result = convert_16_9_to_4_3(thumbnail_path)
            if result:
                converted_count += 1
                print(f"封面转换成功: {Path(result).name}")
            else:
                print(f"封面转换失败: {thumbnail_path.name}")
        except Exception as e:
            print(f"转换封面时出错 {thumbnail_path.name}: {e}")
            # 继续处理其他文件，不中断流程
    
    return converted_count


def extract_audio_from_video(video_path, config, ffmpeg_path=None):
    """从已下载的视频文件中提取音频"""
    if not ffmpeg_path:
        print("错误: 需要 ffmpeg 才能从视频中提取音频")
        return False
    
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"错误: 视频文件不存在: {video_path}")
        return False
    
    # 从配置中读取音频格式
    audio_format = config.get("audioFormat", "flac").lower()
    if audio_format not in ["flac", "wav"]:
        print(f"警告: 不支持的音频格式 {audio_format}，使用 flac")
        audio_format = "flac"
    
    # 构建输出音频文件路径
    audio_file = video_file.parent / f"{video_file.stem}.{audio_format}"
    
    # 如果音频文件已存在，跳过提取
    if audio_file.exists():
        print(f"音频文件已存在，跳过提取: {audio_file.name}")
        return True
    
    # 构建 ffmpeg 命令提取音频
    is_windows = platform.system() == "Windows"
    exe_ext = ".exe" if is_windows else ""
    
    # 尝试从 ffmpeg_path 目录中找到 ffmpeg
    ffmpeg_exe = None
    if ffmpeg_path:
        ffmpeg_exe_path = Path(ffmpeg_path) / f"ffmpeg{exe_ext}"
        if ffmpeg_exe_path.exists():
            ffmpeg_exe = str(ffmpeg_exe_path)
    
    # 如果没找到，尝试从系统 PATH 中查找
    if not ffmpeg_exe:
        ffmpeg_exe = shutil.which("ffmpeg")
    
    if not ffmpeg_exe:
        print("错误: 未找到 ffmpeg 可执行文件")
        return False
    
    # 提取音频命令
    cmd = [str(ffmpeg_exe), "-i", str(video_file), "-vn"]  # 不包含视频
    
    # Hi-Res无损音质要求：采样率不低于48kHz，位深度不低于24bit
    # 设置采样率至少为48kHz（满足Hi-Res最低要求）
    # 注意：如果源文件采样率>48kHz，此参数会降采样到48kHz，但仍满足Hi-Res要求
    cmd.extend(["-ar", "48000"])
    # 设置位深度为24bit
    if audio_format == "flac":
        # FLAC支持24bit，使用sample_fmt s32（32bit可以包含24bit数据，确保兼容性）
        cmd.extend(["-acodec", "flac", "-compression_level", "12", "-sample_fmt", "s32"])
    else:  # wav
        # WAV使用24bit PCM
        cmd.extend(["-acodec", "pcm_s24le"])
    
    cmd.extend(["-y", str(audio_file)])  # 覆盖输出文件
    
    print(f"正在从视频中提取音频: {video_file.name} -> {audio_file.name}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"音频提取成功: {audio_file.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取音频时出错: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False


def find_downloaded_video(download_dir, video_url):
    """查找已下载的视频文件"""
    download_path = Path(download_dir)
    video_extensions = ['.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv']
    
    # 查找最近下载的视频文件（最近5分钟内）
    current_time = time.time()
    recent_videos = []
    
    for ext in video_extensions:
        pattern = f"**/*{ext}"
        found_files = list(download_path.glob(pattern))
        
        for video_file in found_files:
            # 排除音频文件
            if video_file.suffix.lower() in ['.m4a', '.mp3', '.flac', '.wav']:
                continue
            
            # 检查是否是最近下载的（5分钟内）
            file_mtime = video_file.stat().st_mtime
            if current_time - file_mtime < 300:  # 5分钟内
                recent_videos.append(video_file)
    
    # 按修改时间排序，返回最新的
    if recent_videos:
        return sorted(recent_videos, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    return None


def download_audio(video_url, config, download_dir, ffmpeg_path=None):
    """下载音频文件（最高质量无损格式）"""
    ytdlp_cmd = find_ytdlp()
    
    if not ytdlp_cmd:
        print("错误: 未找到 yt-dlp，请确保已安装 yt-dlp")
        sys.exit(1)
    
    cmd = [ytdlp_cmd]
    
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
    
    # Hi-Res无损音质要求：采样率不低于48kHz，位深度不低于24bit
    # 使用postprocessor-args通过ffmpeg参数设置
    # 设置采样率至少为48kHz（满足Hi-Res最低要求）
    # 注意：如果源文件采样率>48kHz，此参数会降采样到48kHz，但仍满足Hi-Res要求
    if audio_format == "flac":
        # FLAC: 采样率至少48kHz，24bit（使用s32格式，32bit可以包含24bit数据）
        cmd.extend(["--postprocessor-args", "ffmpeg:-ar 48000 -sample_fmt s32"])
    else:  # wav
        # WAV: 采样率至少48kHz，24bit PCM
        cmd.extend(["--postprocessor-args", "ffmpeg:-ar 48000 -acodec pcm_s24le"])
    
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
    download_dir = ensure_download_dir(config)
    print(f"下载目录: {download_dir}")
    
    # 构建并执行下载命令
    print(f"正在下载视频和封面图片: {video_url}")
    cmd = build_ytdlp_command(video_url, config, download_dir, ffmpeg_path, download_video=True)
    
    print(f"执行命令: {' '.join(cmd)}")
    downloaded_video_path = None
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("视频和封面图片下载完成！")
        
        # 查找刚下载的视频文件
        downloaded_video_path = find_downloaded_video(download_dir, video_url)
        
        # 自动转换封面图片为4:3比例
        print("\n正在转换封面图片为4:3比例...")
        converted_count = convert_thumbnails_to_4_3(download_dir, video_url)
        if converted_count > 0:
            print(f"封面转换完成！成功转换 {converted_count} 个封面图片")
        else:
            print("未找到需要转换的封面图片")
    except subprocess.CalledProcessError as e:
        print(f"下载视频时出错: {e}")
        sys.exit(1)
    
    # 如果需要分离音频
    if config.get("sperateAudio", False):
        audio_format = config.get("audioFormat", "flac").upper()
        
        # 优化：如果已下载了视频文件，尝试从视频中提取音频，避免重复下载
        if downloaded_video_path and ffmpeg_path:
            print(f"\n检测到已下载的视频文件，尝试从视频中提取音频（格式: {audio_format}）...")
            success = extract_audio_from_video(downloaded_video_path, config, ffmpeg_path)
            if success:
                print(f"音频提取完成！（格式: {audio_format}）")
            else:
                print("从视频提取音频失败，将重新下载音频...")
                # 如果提取失败，回退到下载方式
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
        else:
            # 如果没有找到视频文件或没有ffmpeg，使用原来的下载方式
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

