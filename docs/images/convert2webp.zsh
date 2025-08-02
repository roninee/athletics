#!/bin/zsh

# 设置转换质量，0-100，默认80
QUALITY=80

echo "开始将当前目录下所有JPEG/JPG/PNG图片转换为WebP格式..."
echo "转换质量设置为: $QUALITY"

# 查找所有jpeg、jpg和png文件
for img_file in *.jpeg *.jpg *.png; do
    # 检查文件是否存在，防止没有匹配文件时脚本报错
    if [[ -f "$img_file" ]]; then
        # 构建输出文件名，将扩展名改为.webp
        output_file="${img_file%.*}.webp"

        echo "正在转换: $img_file -> $output_file"
        
        # 使用cwebp进行转换，-q 设置质量
        cwebp -q $QUALITY "$img_file" -o "$output_file"
        
        if [[ $? -eq 0 ]]; then
            echo "成功转换: $output_file"
        else
            echo "转换失败: $img_file"
        fi
    fi
done

echo "所有图片转换完成。"
