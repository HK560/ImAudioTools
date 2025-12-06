#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频格式转换脚本
将视频转换为非压缩或低压缩格式，以便于PR等视频编辑软件编辑
支持ProRes、DNxHD/DNxHR等编辑友好格式
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


def check_gpu_encoder(ffmpeg_exe, encoder_name):
    """检查ffmpeg是否支持指定的GPU编码器
    
    Args:
        ffmpeg_exe: ffmpeg可执行文件路径
        encoder_name: 编码器名称（如h264_nvenc, hevc_amf等）
    
    Returns:
        bool: 如果支持返回True，否则返回False
    """
    try:
        result = subprocess.run(
            [str(ffmpeg_exe), "-encoders"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return encoder_name in result.stdout
    except Exception:
        return False


def detect_available_gpu_encoders(ffmpeg_path):
    """检测可用的GPU编码器
    
    Args:
        ffmpeg_path: ffmpeg路径
    
    Returns:
        dict: 包含可用编码器信息的字典
    """
    ffmpeg_exe = Path(ffmpeg_path) / "ffmpeg.exe"
    if not ffmpeg_exe.exists():
        return {}
    
    available = {
        "nvenc": False,      # NVIDIA NVENC
        "amf": False,        # AMD AMF
        "qsv": False,        # Intel QuickSync
    }
    
    # 检查NVENC (NVIDIA)
    if check_gpu_encoder(ffmpeg_exe, "h264_nvenc"):
        available["nvenc"] = True
    
    # 检查AMF (AMD)
    if check_gpu_encoder(ffmpeg_exe, "h264_amf"):
        available["amf"] = True
    
    # 检查QSV (Intel)
    if check_gpu_encoder(ffmpeg_exe, "h264_qsv"):
        available["qsv"] = True
    
    return available


def find_video_file(video_path):
    """查找视频文件，处理路径中的特殊字符和编码问题
    
    Args:
        video_path: 视频文件路径（可能是用户输入的路径）
    
    Returns:
        Path对象，如果找到文件；否则返回None
    """
    # 移除路径中的引号（如果用户用引号包裹路径）
    clean_path = video_path.strip('"\'')
    
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
    
    # 如果路径指向的是目录，尝试在该目录中查找mp4文件
    try:
        test_path = Path(clean_path)
        if test_path.exists() and test_path.is_dir():
            # 查找目录中的所有mp4文件
            mp4_files = list(test_path.glob("*.mp4"))
            if len(mp4_files) == 1:
                print(f"提示: 在目录中找到视频文件: {mp4_files[0]}")
                return mp4_files[0]
            elif len(mp4_files) > 1:
                print(f"提示: 在目录中找到多个mp4文件，使用第一个: {mp4_files[0].name}")
                for i, f in enumerate(mp4_files[:5], 1):  # 只显示前5个
                    print(f"  {i}. {f.name}")
                return mp4_files[0]
    except Exception:
        pass
    
    # 如果路径是文件路径但不存在，尝试在父目录中查找
    try:
        parent_dir = Path(clean_path).parent
        if parent_dir.exists() and parent_dir.is_dir():
            # 查找目录中的所有mp4文件
            mp4_files = list(parent_dir.glob("*.mp4"))
            if len(mp4_files) == 1:
                print(f"提示: 在父目录中找到视频文件: {mp4_files[0]}")
                return mp4_files[0]
            elif len(mp4_files) > 1:
                # 尝试匹配文件名（不区分大小写）
                input_name = Path(clean_path).stem.lower().replace(" ", "").replace("_", "").replace("-", "")
                best_match = None
                best_score = 0
                
                for mp4_file in mp4_files:
                    file_name = mp4_file.stem.lower().replace(" ", "").replace("_", "").replace("-", "")
                    # 计算匹配度
                    if input_name in file_name or file_name in input_name:
                        score = min(len(input_name), len(file_name)) / max(len(input_name), len(file_name), 1)
                        if score > best_score:
                            best_score = score
                            best_match = mp4_file
                
                if best_match:
                    print(f"提示: 找到匹配的视频文件: {best_match}")
                    return best_match
                else:
                    # 如果没找到匹配的，返回第一个
                    print(f"提示: 在父目录中找到多个mp4文件，使用第一个: {mp4_files[0]}")
                    return mp4_files[0]
    except Exception:
        pass
    
    return None


def convert_video_for_editing(video_path, ffmpeg_path=None, format_type="prores", use_gpu=True):
    """将视频转换为编辑友好格式
    
    Args:
        video_path: 视频文件路径
        ffmpeg_path: ffmpeg路径（可选）
        format_type: 输出格式类型
            - "prores": ProRes 422（推荐，质量高，文件较大，CPU编码）
            - "prores_lt": ProRes 422 LT（质量稍低，文件较小，CPU编码）
            - "dnxhd": DNxHD 145（Avid格式，1080p，CPU编码）
            - "dnxhr": DNxHR HQ（Avid格式，支持任意分辨率，CPU编码）
            - "h264_high": 高质量H.264（CPU编码，较慢）
            - "h264_gpu": 高质量H.264（GPU加速，快速，推荐）
            - "h265_gpu": 高质量H.265/HEVC（GPU加速，快速，文件更小）
        use_gpu: 是否尝试使用GPU加速（默认True）
    """
    # 查找视频文件
    video_file = find_video_file(video_path)
    
    if not video_file:
        print(f"错误: 无法找到视频文件: {video_path}")
        print("\n提示:")
        print("  1. 请检查文件路径是否正确")
        print("  2. 确保文件确实存在")
        print("  3. 如果路径包含特殊字符，请使用引号包裹路径")
        print("  4. 可以尝试使用相对路径或只提供目录路径（如果目录中只有一个mp4文件）")
        sys.exit(1)
    
    print(f"找到视频文件: {video_file}")
    
    # 检查视频文件是否存在
    if not video_file.exists():
        print(f"错误: 视频文件不存在: {video_file}")
        sys.exit(1)
    
    # 获取视频文件的绝对路径
    video_abs_path = video_file.resolve()
    
    # 获取视频文件名（不含扩展名）
    video_stem = video_file.stem
    
    # 查找ffmpeg
    if not ffmpeg_path:
        ffmpeg_path = find_ffmpeg_path()
    
    if not ffmpeg_path:
        print("错误: 未找到ffmpeg，无法转换视频")
        sys.exit(1)
    
    ffmpeg_exe = Path(ffmpeg_path) / "ffmpeg.exe"
    if not ffmpeg_exe.exists():
        print(f"错误: ffmpeg.exe不存在: {ffmpeg_exe}")
        sys.exit(1)
    
    # 检测可用的GPU编码器
    gpu_encoders = {}
    if use_gpu:
        print("正在检测GPU加速支持...")
        gpu_encoders = detect_available_gpu_encoders(ffmpeg_path)
        if any(gpu_encoders.values()):
            print("检测到GPU加速支持:")
            if gpu_encoders.get("nvenc"):
                print("  ✓ NVIDIA NVENC (推荐)")
            if gpu_encoders.get("amf"):
                print("  ✓ AMD AMF")
            if gpu_encoders.get("qsv"):
                print("  ✓ Intel QuickSync")
        else:
            print("  未检测到GPU加速支持，将使用CPU编码")
    
    # 根据格式类型构建ffmpeg命令
    format_type = format_type.lower()
    
    # 确定输出文件扩展名
    # 使用无损音频时，MOV格式支持更好
    if format_type in ["h264_high", "h264_gpu", "h265_gpu"]:
        output_ext = "mov"  # 改为MOV以支持无损音频
    else:
        output_ext = "mov"
    
    # 输出文件路径：与源文件同目录，文件名添加_editing后缀
    output_file = video_file.parent / f"{video_stem}_editing.{output_ext}"
    
    # 构建基础命令
    cmd = [str(ffmpeg_exe.absolute())]
    
    # 尝试使用硬件解码加速（如果可用且使用GPU编码）
    if format_type in ["h264_gpu", "h265_gpu"] and use_gpu:
        # 尝试使用硬件解码（nvdec, dxva2等）
        # 这会自动选择可用的硬件解码器
        cmd.extend(["-hwaccel", "auto"])
    
    cmd.extend(["-i", str(video_abs_path)])
    
    if format_type == "prores":
        # ProRes 422（高质量，适合专业编辑，CPU编码）
        cmd.extend([
            "-c:v", "prores_ks",  # ProRes编码器
            "-profile:v", "3",    # ProRes 422
            "-c:a", "pcm_s24le",  # 24位PCM音频（高质量）
        ])
    elif format_type == "prores_lt":
        # ProRes 422 LT（质量稍低，文件较小，CPU编码）
        cmd.extend([
            "-c:v", "prores_ks",
            "-profile:v", "2",    # ProRes 422 LT
            "-c:a", "pcm_s24le",
        ])
    elif format_type == "dnxhd":
        # DNxHD 145（1080p，145 Mbps，CPU编码）
        cmd.extend([
            "-c:v", "dnxhd",
            "-b:v", "145M",       # 145 Mbps
            "-c:a", "pcm_s24le",
        ])
    elif format_type == "dnxhr":
        # DNxHR HQ（支持任意分辨率，CPU编码）
        cmd.extend([
            "-c:v", "dnxhr",
            "-b:v", "220M",       # HQ质量
            "-c:a", "pcm_s24le",
        ])
    elif format_type == "h264_high":
        # 快速H.264（CPU编码，视频质量低，音频无损）
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "ultrafast",  # 最快预设
            "-crf", "28",            # 视频质量低（28是较低质量，但编码极快）
            "-c:a", "pcm_s24le",     # 24位PCM无损音频
        ])
    elif format_type == "h264_gpu":
        # 高质量H.264（GPU加速，快速，推荐）
        if gpu_encoders.get("nvenc"):
            # NVIDIA NVENC（最快，视频质量低，音频无损）
            cmd.extend([
                "-c:v", "h264_nvenc",
                "-preset", "p1",      # p1最快
                "-cq", "28",          # 视频质量低（28是较低质量，但编码极快）
                "-rc", "vbr",         # 可变比特率
                "-b:v", "0",          # 使用CQ模式，不限制比特率
                "-c:a", "pcm_s24le",  # 24位PCM无损音频
            ])
        elif gpu_encoders.get("amf"):
            # AMD AMF（最快，视频质量低，音频无损）
            cmd.extend([
                "-c:v", "h264_amf",
                "-quality", "speed",     # speed最快
                "-rc", "vbr_peak",      # 可变比特率
                "-qmin", "28",          # 视频质量低
                "-qmax", "32",          # 最大质量（更低）
                "-c:a", "pcm_s24le",    # 24位PCM无损音频
            ])
        elif gpu_encoders.get("qsv"):
            # Intel QuickSync（最快，视频质量低，音频无损）
            cmd.extend([
                "-c:v", "h264_qsv",
                "-preset", "veryfast",   # 最快预设
                "-global_quality", "28", # 视频质量低
                "-c:a", "pcm_s24le",     # 24位PCM无损音频
            ])
        else:
            # 如果没有GPU，回退到CPU编码（最快设置）
            print("警告: 未检测到GPU加速，使用CPU编码（最快设置）")
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "ultrafast",  # 最快预设
                "-crf", "28",            # 视频质量低
                "-c:a", "pcm_s24le",     # 24位PCM无损音频
            ])
    elif format_type == "h265_gpu":
        # 高质量H.265/HEVC（GPU加速，快速，文件更小）
        if gpu_encoders.get("nvenc"):
            # NVIDIA NVENC HEVC（最快，视频质量低，音频无损）
            cmd.extend([
                "-c:v", "hevc_nvenc",
                "-preset", "p1",      # p1最快
                "-cq", "28",          # 视频质量低（28是较低质量，但编码极快）
                "-rc", "vbr",         # 可变比特率
                "-b:v", "0",          # 使用CQ模式，不限制比特率
                "-c:a", "pcm_s24le",  # 24位PCM无损音频
            ])
        elif gpu_encoders.get("amf"):
            # AMD AMF HEVC（最快，视频质量低，音频无损）
            cmd.extend([
                "-c:v", "hevc_amf",
                "-quality", "speed",     # speed最快
                "-rc", "vbr_peak",
                "-qmin", "28",          # 视频质量低
                "-qmax", "32",          # 最大质量（更低）
                "-c:a", "pcm_s24le",    # 24位PCM无损音频
            ])
        elif gpu_encoders.get("qsv"):
            # Intel QuickSync HEVC（最快，视频质量低，音频无损）
            cmd.extend([
                "-c:v", "hevc_qsv",
                "-preset", "veryfast",   # 最快预设
                "-global_quality", "28", # 视频质量低
                "-c:a", "pcm_s24le",     # 24位PCM无损音频
            ])
        else:
            # 如果没有GPU，回退到CPU编码（最快设置）
            print("警告: 未检测到GPU加速，使用CPU编码（最快设置）")
            cmd.extend([
                "-c:v", "libx265",
                "-preset", "ultrafast",  # 最快预设
                "-crf", "28",            # 视频质量低
                "-c:a", "pcm_s24le",     # 24位PCM无损音频
            ])
    else:
        print(f"错误: 不支持的格式类型 '{format_type}'")
        print("支持的格式: prores, prores_lt, dnxhd, dnxhr, h264_high, h264_gpu, h265_gpu")
        sys.exit(1)
    
    # 添加输出文件参数
    cmd.extend(["-y", str(output_file.absolute())])
    
    return cmd, str(output_file.absolute())


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python convert_video.py <视频文件路径> [格式类型]")
        print("\n格式类型选项（按速度排序）:")
        print("  h264_gpu    - 快速H.264（GPU加速，最快，推荐）⭐")
        print("  h265_gpu    - 快速H.265/HEVC（GPU加速，快速，文件更小）⭐")
        print("  h264_high   - 快速H.264（CPU编码，最快设置）")
        print("  prores      - ProRes 422（CPU编码，高质量，适合PR等专业软件）")
        print("  prores_lt   - ProRes 422 LT（CPU编码，质量稍低，文件较小）")
        print("  dnxhd       - DNxHD 145（CPU编码，Avid格式，1080p）")
        print("  dnxhr       - DNxHR HQ（CPU编码，Avid格式，支持任意分辨率）")
        print("\n注意:")
        print("  - 带⭐的格式使用GPU加速，速度最快")
        print("  - GPU加速需要NVIDIA/AMD/Intel显卡支持")
        print("  - 如果未检测到GPU，会自动回退到CPU编码")
        print("  - 视频质量：CQ/CRF 28（较低质量，但编码极快）")
        print("  - 音频质量：PCM 24bit（完全无损，绝不降低质量）")
        print("  - 输出格式：MOV（支持无损音频）")
        print("\n示例:")
        print("  python convert_video.py video.mp4")
        print("  python convert_video.py video.mp4 h264_gpu")
        print("  python convert_video.py download/video/video.mp4 h265_gpu")
        print("  python convert_video.py video.mp4 prores")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    # 解析格式类型参数（可选，默认为h264_gpu，如果支持GPU）
    format_type = "h264_gpu"  # 默认使用GPU加速格式
    if len(sys.argv) >= 3:
        format_type = sys.argv[2].lower()
    
    # 查找ffmpeg路径
    print("正在查找ffmpeg...")
    ffmpeg_path = find_ffmpeg_path()
    if ffmpeg_path:
        print(f"找到ffmpeg: {ffmpeg_path}")
    else:
        print("错误: 未找到ffmpeg，无法转换视频")
        sys.exit(1)
    
    # 转换视频
    print(f"正在转换视频: {video_path}")
    print(f"输出格式: {format_type}")
    
    # 只有GPU格式才需要检测GPU
    use_gpu = format_type in ["h264_gpu", "h265_gpu"]
    cmd, output_file = convert_video_for_editing(video_path, ffmpeg_path, format_type, use_gpu=use_gpu)
    
    print(f"输出文件: {output_file}")
    print(f"执行命令: {' '.join(cmd)}")
    
    if format_type in ["h264_gpu", "h265_gpu"]:
        print("\n注意: 使用GPU加速，转换速度会很快...")
    else:
        print("\n注意: 使用CPU编码，转换过程可能需要较长时间，请耐心等待...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n视频转换完成！输出文件: {output_file}")
        print(f"文件大小: {Path(output_file).stat().st_size / (1024*1024):.2f} MB")
    except subprocess.CalledProcessError as e:
        print(f"\n转换视频时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

