# YouTube视频下载与音视频处理工具集

自用的YouTube视频下载和音视频处理脚本工具集，支持视频下载、音频提取、格式转换等功能。

## 功能特性

- 🎥 **视频下载**: 使用yt-dlp下载YouTube视频，支持最佳质量视频+音频合并
- 🎵 **音频提取**: 从视频文件中提取无损FLAC音频
- 🎬 **格式转换**: 将视频转换为编辑友好格式（ProRes、DNxHD、H.264/H.265等）
- 🔊 **音频压缩**: 将WAV文件压缩为FLAC格式，保持无损音质
- 🖼️ **封面下载**: 自动下载视频封面图片（JPG格式）
- ⚡ **GPU加速**: 支持NVIDIA/AMD/Intel GPU硬件加速编码

## 依赖要求

### 必需工具
- **Python 3.x** - 运行脚本
- **yt-dlp.exe** - YouTube视频下载工具（已包含在项目中）
- **ffmpeg** - 音视频处理工具（需要单独下载）

### 下载ffmpeg
- [ffmpeg官方下载](https://www.gyan.dev/ffmpeg/builds/)
- 下载后解压到项目目录下的 `ffmpeg/` 文件夹中
- 确保 `ffmpeg/bin/` 目录包含 `ffmpeg.exe` 和 `ffprobe.exe`

## 配置文件

项目使用 `config.cfg` 文件进行配置（JSON格式）：

```json
{
    "proxy": "http://127.0.0.1:56056",      // 代理设置（可选）
    "isCombineVideo": true,                  // 是否合并最佳视频+音频
    "sperateAudio": true,                   // 是否额外下载音频文件
    "audioFormat": "flac"                   // 音频格式：flac 或 wav
}
```

### 配置说明
- `proxy`: 代理服务器地址（如不需要可删除此字段）
- `isCombineVideo`: `true` 下载最佳视频+音频并合并，`false` 只下载最佳视频
- `sperateAudio`: `true` 额外下载独立的音频文件，`false` 不下载
- `audioFormat`: 音频格式，支持 `flac`（推荐，压缩无损）或 `wav`（未压缩）

## 使用方法

### 1. 下载视频

下载YouTube视频，自动下载视频、封面图片，并可选择下载音频文件。

```bash
python download_video.py <视频URL>
```

**示例：**
```bash
python download_video.py https://www.youtube.com/watch?v=VIDEO_ID
```

**功能：**
- 自动下载最佳质量视频（根据配置合并视频+音频）
- 自动下载视频封面图片（JPG格式）
- 如果配置了 `sperateAudio: true`，会额外下载无损音频文件
- 文件保存在 `download/<视频名>/` 目录下

### 2. 提取音频

从视频文件中提取音频为FLAC格式。

```bash
python extract_audio.py <视频文件路径> [压缩级别]
```

**示例：**
```bash
python extract_audio.py video.mp4
python extract_audio.py video.mp4 12
python extract_audio.py download/video/video.mp4
```

**参数说明：**
- `视频文件路径`: 视频文件路径（支持相对路径和绝对路径）
- `压缩级别`: FLAC压缩级别（0-12，可选，默认12）
  - `0`: 最快，文件最大
  - `12`: 最慢，文件最小（推荐）

**输出：**
- 音频文件保存在 `download/<视频名>/<视频名>.flac`

### 3. 视频格式转换

将视频转换为编辑友好格式，便于在PR等视频编辑软件中使用。

```bash
python convert_video.py <视频文件路径> [格式类型]
```

**示例：**
```bash
python convert_video.py video.mp4
python convert_video.py video.mp4 h264_gpu
python convert_video.py download/video/video.mp4 h265_gpu
python convert_video.py video.mp4 prores
```

**格式类型选项：**

| 格式 | 说明 | 速度 | 推荐场景 |
|------|------|------|----------|
| `h264_gpu` ⭐ | 快速H.264（GPU加速） | 最快 | 日常编辑（推荐） |
| `h265_gpu` ⭐ | 快速H.265/HEVC（GPU加速） | 快速 | 日常编辑，文件更小 |
| `h264_high` | 快速H.264（CPU编码） | 快 | 无GPU时使用 |
| `prores` | ProRes 422（高质量） | 慢 | 专业编辑软件 |
| `prores_lt` | ProRes 422 LT | 慢 | 专业编辑，文件较小 |
| `dnxhd` | DNxHD 145（1080p） | 慢 | Avid编辑软件 |
| `dnxhr` | DNxHR HQ | 慢 | Avid编辑软件，任意分辨率 |

**注意：**
- 带⭐的格式使用GPU加速，速度最快
- GPU加速需要NVIDIA/AMD/Intel显卡支持
- 如果未检测到GPU，会自动回退到CPU编码
- 视频质量：CQ/CRF 28（较低质量，但编码极快）
- 音频质量：PCM 24bit（完全无损）
- 输出格式：MOV（支持无损音频）

**输出：**
- 转换后的文件保存在源文件同目录，文件名添加 `_editing` 后缀
- 例如：`video.mp4` → `video_editing.mov`

### 4. WAV转FLAC压缩

将WAV文件压缩为FLAC格式，保持无损音质的同时减小文件大小。

```bash
python compress_wav_to_flac.py <WAV文件路径> [压缩级别]
```

**示例：**
```bash
python compress_wav_to_flac.py audio.wav
python compress_wav_to_flac.py audio.wav 12
python compress_wav_to_flac.py download/audio/audio.wav
```

**参数说明：**
- `WAV文件路径`: WAV文件路径（支持相对路径和绝对路径）
- `压缩级别`: FLAC压缩级别（0-12，可选，默认12）
  - `0`: 最快，文件最大
  - `12`: 最慢，文件最小（推荐）

**输出：**
- FLAC文件保存在源文件同目录，扩展名改为 `.flac`
- 显示压缩前后文件大小和压缩率

## 目录结构

```
ytbdownload/
├── download_video.py          # 视频下载脚本
├── extract_audio.py            # 音频提取脚本
├── convert_video.py            # 视频格式转换脚本
├── compress_wav_to_flac.py     # WAV转FLAC压缩脚本
├── config.cfg                  # 配置文件
├── yt-dlp.exe                  # YouTube下载工具
├── ffmpeg/                     # ffmpeg工具目录
│   └── bin/
│       ├── ffmpeg.exe
│       └── ffprobe.exe
└── download/                   # 下载文件保存目录
    └── <视频名>/
        ├── <视频名>.mp4
        ├── <视频名>.jpg
        └── <视频名>.flac
```

## 注意事项

1. **ffmpeg路径**: 脚本会自动查找 `ffmpeg/bin/` 目录，如果找不到会报错
2. **GPU加速**: 视频转换的GPU加速功能需要显卡支持，会自动检测并回退到CPU
3. **文件路径**: 支持相对路径和绝对路径，如果路径包含特殊字符可用引号包裹
4. **代理设置**: 如果无法访问YouTube，需要在 `config.cfg` 中配置代理
5. **文件覆盖**: 如果输出文件已存在，会自动覆盖（不会询问确认）

## 常见问题

**Q: 下载视频时提示找不到ffmpeg？**  
A: 请确保已下载ffmpeg并解压到 `ffmpeg/bin/` 目录，包含 `ffmpeg.exe` 和 `ffprobe.exe`。

**Q: 视频转换很慢？**  
A: 如果支持GPU加速，使用 `h264_gpu` 或 `h265_gpu` 格式会快很多。否则使用CPU编码会较慢。

**Q: 如何只下载音频？**  
A: 在 `config.cfg` 中设置 `"isCombineVideo": false` 和 `"sperateAudio": true`。

**Q: 下载的文件在哪里？**  
A: 所有下载的文件都保存在 `download/` 目录下，按视频名称创建子文件夹。

## 相关链接

- [ffmpeg下载](https://www.gyan.dev/ffmpeg/builds/)
- [yt-dlp项目](https://github.com/yt-dlp/yt-dlp)