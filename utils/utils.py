import os
import platform
import matplotlib.pyplot as plt
import pandas as pd
import warnings
import subprocess
from datetime import datetime, timedelta
import os
# ========== 保存HTML到本地并自动打开 ==========

def generate_fund_html(raw_data):
    html_head = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            .group-title {font-size: 14px; font-weight: bold; margin: 10px 0 5px 0; color: #2d3748;}
            .table-wrap {width: 100%; overflow-x: auto; margin-bottom: 15px;}
            table {border-collapse: collapse; min-width: 500px;}
            th {background: #4299e1; color: white; padding: 8px; border: 1px solid #ddd; font-size: 12px;}
            td {padding: 8px; text-align: center; border: 1px solid #ddd; font-size: 11px;}
            .rise {color: red; font-weight: bold;}
            .fall {color: green; font-weight: bold;}
            .flat {color: #718096;}
        </style>
    </head>
    <body>
        <h3 style="font-size: 16px; color: #2d3748; margin: 0 0 10px 0;">📊 基金数据汇总</h3>
    """

    html_body = ""
    for group_name,fund_list in raw_data.items():
        html_body += f"<div class='group-title'>{group_name}</div>"
        html_body += "<div class='table-wrap'><table>"
        html_body += "<tr><th>基金代码</th><th>基金名称</th><th>最新净值</th><th>涨跌幅</th><th>更新时间</th></tr>"

        for fund in fund_list:
            code = fund.get('code', '--')
            name = fund.get('name', '--')
            net = f"{fund.get('net')}元" if fund.get('net') is not None else "None元"
            time = fund.get('time', 'None') if fund.get('time') != "" else "None"

            # ========== 核心优化：数字判断涨跌 ==========
            pct_chg = fund.get('pct_chg')
            # 1. 先处理空值
            if pct_chg is None or pd.isna(pct_chg):
                pct_chg_str = "--"
                pct_class = "flat"
            else:
                # 2. 转成普通数字（兼容numpy.float64）
                pct_chg_num = float(pct_chg)
                # 3. 数字判断正负（核心逻辑）
                if pct_chg_num > 0:
                    pct_class = "rise"  # 涨
                elif pct_chg_num < 0:
                    pct_class = "fall"  # 跌
                else:
                    pct_class = "flat"  # 平
                # 4. 格式化展示字符串（补%符号）
                pct_chg_str = f"{pct_chg_num}%"

            html_body += f"""
            <tr>
                <td>{code}</td>
                <td>{name}</td>
                <td>{net}</td>
                <td class='{pct_class}'>{pct_chg_str}</td>
                <td>{time}</td>
            </tr>
            """

        html_body += "</table></div>"

    html_foot = "</body></html>"
    full_html = (html_head + html_body + html_foot).replace('\n', '').strip()
    return full_html

def save_and_open_html(html_content, file_name="fund_report.html"):
    # 保存文件（确保中文编码正确）
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 获取文件绝对路径
    file_path = os.path.abspath(file_name)
    print(f"✅ HTML文件已保存至：{file_path}")

    # 自动打开文件（跨平台兼容）
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open {file_path}")
        else:  # Linux
            os.system(f"xdg-open {file_path}")
        print("✅ 已自动打开HTML文件")
    except Exception as e:
        print(f"⚠️ 自动打开失败，请手动打开：{file_path} | 错误：{str(e)}")

    return file_path


##############################################################
# 设置中文字体（避免乱码）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号乱码
# 禁用Matplotlib的字体缺失警告（只针对特殊符号如📊）
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')


def generate_fund_image(raw_data):
    # ========== 1. 整理数据：按分组拆分，添加分组行 ==========
    col_labels = ["代码", "基金名称", "涨跌幅", "与30天高点%差", "与30天低点%差", "连续趋势", "最新净值"]
    n_cols = len(col_labels)
    table_data = [col_labels]  # 表头行
    total_data_rows = 0  # 纯数据行数
    group_row_count = len(raw_data)  # 分组行数量

    # 遍历分组，先加分组行，再加数据行
    for group_name, fund_list in raw_data.items():
        # 分组行：第二列显示group_name，其他列空字符串
        group_row = ["", group_name, "", "", "", "", ""]
        table_data.append(group_row)
        # 添加该分组的基金数据行
        for fund in fund_list:
            high_diff = fund.get('与30天高点%差', '--')
            low_diff = fund.get('与30天低点%差', '--')
            row = [
                fund.get('code', '--'),
                fund.get('name', '--'),
                fund.get('ratio', '--'),
                f"{float(high_diff)}%" if high_diff != '--' and high_diff is not None else "--",
                f"{float(low_diff)}%" if low_diff != '--' and low_diff is not None else "--",
                fund.get('trend', '--'),
                f"{fund.get('net', '--')}元" if fund.get('net') is not None else "--"
            ]
            table_data.append(row)
            total_data_rows += 1

    # ========== 2. 自适应画布尺寸（包含分组行） ==========
    FIXED_ROW_HEIGHT_SCALE = 0.7  # 行高固定值
    HEIGHT_PER_ROW = 0.3  # 每行对应的画布高度系数
    WIDTH_BY_CONTENT = 10  # 按列内容固定宽度

    # 总表格行 = 表头(1) + 分组行 + 数据行
    total_table_rows = 1 + group_row_count + total_data_rows
    fig_height = total_table_rows * HEIGHT_PER_ROW
    fig_height = max(2, fig_height)  # 最小高度2，避免过短
    fig, ax = plt.subplots(figsize=(WIDTH_BY_CONTENT, fig_height))
    ax.axis('tight')
    ax.axis('off')  # 隐藏坐标轴

    # ========== 3. 绘制表格 ==========
    table = ax.table(
        cellText=table_data,
        cellLoc='center',
        loc='center',
        bbox=[0, 0, 1, 1]
    )

    # 基础样式设置
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, FIXED_ROW_HEIGHT_SCALE)

    # ========== 4. 固定列宽 ==========
    col_widths = [0.1, 0.25, 0.14, 0.14, 0.14, 0.12, 0.11]
    for col in range(n_cols):
        for row in range(len(table_data)):
            table[(row, col)].set_width(col_widths[col])
            # 全局去掉边框：所有单元格设置线宽为0，边框颜色为空
            table[(row, col)].set_linewidth(0)
            table[(row, col)].set_edgecolor('none')

    # ========== 5. 美化样式 ==========
    # 1. 表头样式
    for col in range(n_cols):
        cell = table[(0, col)]
        cell.set_facecolor('#5C6E83')  # 表头背景色
        cell.get_text().set_weight('heavy')  # 加粗
        cell.get_text().set_color('white')

    # 2. 分组行样式（第二列显示分组名，背景色突出）
    row_idx = 1  # 表头是0行，第一个分组行是1行
    for group_name, fund_list in raw_data.items():
        # 分组行整行设置背景色
        for col in range(n_cols):
            cell = table[(row_idx, col)]
            cell.set_facecolor('#B4C5D4')  # 分组行背景色
            # 只有第二列显示分组名，且设置为白色加粗
            if col == 1:
                cell.get_text().set_fontsize(6)  # 分组名字体稍小
            else:
                cell.get_text().set_visible(False)  # 隐藏其他列的空文本
        row_idx += (len(fund_list) + 1)  # 跳到下一个分组行（当前分组行+数据行数）

    # 3. 数据行涨跌幅标色（从第一个数据行开始）
    # 先找到所有数据行的起始索引：表头(0) + 分组行数量 + 前面的分组数据行
    data_row_start = 1 + group_row_count
    for row in range(1, len(table_data)):
        # 跳过分组行（分组行背景色已设置，无需处理）
        if table[(row, 0)].get_facecolor() == table[(1, 0)].get_facecolor():
            continue

        # 涨跌幅列（列2）标色
        pct_cell = table[(row, 2)]
        pct_value = table_data[row][2]

        if pct_value != '--' and isinstance(pct_value, (int, float)):
            # 转普通数字（兼容numpy.float64）
            pct_num = float(pct_value)
            # 统一加%符号
            pct_cell.get_text().set_text(f"{pct_num}%")
            # 判断正负标色（基于原始数字，无需解析字符串）
            if pct_value < 0:
                pct_cell.set_facecolor('#d1e7dd')
                pct_cell.get_text().set_color('green')
            elif pct_value > 0:
                pct_cell.set_facecolor('#f8d7da')
                pct_cell.get_text().set_color('red')
            else:
                pct_cell.set_facecolor('#f5f5f5')
        else:
            pct_cell.set_facecolor('#f5f5f5')

    # ========== 6. 保存图片 ==========
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plt.title(f"{today} 基金数据汇总", fontsize=12, pad=10, fontweight='bold')
    now = datetime.now()
    filename = f"fund_data_{now.strftime("%Y-%m-%d")}.png"
    plt.savefig(filename, dpi=200, bbox_inches='tight')
    plt.close()

    # 跨平台打开图片
    if platform.system() == "Windows":
        os.startfile("../output_png/fund_data.png")
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open fund_data.png")
    else:  # Linux
        os.system(f"xdg-open fund_data.png")

    print(f"✅ 图片生成完成（{total_data_rows}条数据）：fund_data.png")


# 生成图片后执行（img_path为图片保存路径，如"fund_table.png"）
def open_image(img_path):
    if platform.system() == "Windows":
        os.startfile(img_path)
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open {img_path}")
    else:  # Linux
        os.system(f"xdg-open {img_path}")


# 生成图片后执行（img_path为图片保存路径，如"fund_table.png"）
def open_image(img_path):
    os.system(f"open {img_path}")  # macOS

