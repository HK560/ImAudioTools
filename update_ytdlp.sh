#!/bin/bash
# yt-dlp 更新脚本
# 从 GitHub 仓库下载最新版本的 yt-dlp

echo "正在更新 yt-dlp..."

# 下载最新版本
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp

# 设置执行权限
chmod +x /usr/local/bin/yt-dlp

# 显示版本信息
echo "更新完成！"
yt-dlp --version

