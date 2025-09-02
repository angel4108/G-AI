import xml.etree.ElementTree as ET
import sys
import json  # 导入json模块用于处理JSON数据


def load_filter_list(filter_file):
    """加载过滤文件列表，每行一个路径"""
    try:
        with open(filter_file, "r", encoding="utf-8") as f:
            # 读取所有行，去除空白和换行符，过滤空行
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        print(f"读取过滤文件时出错: {str(e)}", file=sys.stderr)
        sys.exit(1)


def find_zero_coverage_src(xml_file, filter_list):
    """
    解析XML文件，查找所有fn_cov和cd_cov都为0的src元素，并返回其路径

    参数:
        xml_file: XML文件路径

    返回:
        符合条件的src元素路径列表
    """
    try:
        # 解析XML文件
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 验证根元素是否为BullseyeCoverage
        if root.tag != "{http://www.bullseye.com/covxml}BullseyeCoverage":
            raise ValueError("XML文件的根元素必须是BullseyeCoverage")

        result = []

        # 递归遍历XML元素
        def traverse(element, current_path):
            # 处理src元素
            if element.tag == "{http://www.bullseye.com/covxml}fn":
                # 获取属性值，默认为0
                fn_cov = element.get("fn_cov", "0")
                cd_cov = element.get("cd_cov", "0")
                src_name = element.get("name", "")

                # 检查是否两个覆盖率都为0
                if fn_cov == "0" and cd_cov == "0":
                    # 构建完整路径
                    full_path = (
                        f"{current_path}/{src_name}" if current_path else src_name
                    )
                    result.append(full_path)
                return

            # 处理folder元素，继续遍历子元素
            if (
                element.tag == "{http://www.bullseye.com/covxml}folder"
                or element.tag == "{http://www.bullseye.com/covxml}src"
            ):
                folder_name = element.get("name", "")
                # 检查当前文件夹是否在过滤列表中
                if folder_name in filter_list:
                    return
                # 更新当前路径
                new_path = (
                    f"{current_path}/{folder_name}" if current_path else folder_name
                )

                # 递归处理所有子元素
                for child in element:
                    traverse(child, new_path)

        # 从根元素开始遍历，初始路径为空
        for child in root:
            traverse(child, "")

        return result

    except Exception as e:
        print(f"解析XML文件时出错: {str(e)}", file=sys.stderr)
        return []


def main():
    # 命令行参数：XML文件路径、输出JSON路径、过滤文件路径
    if len(sys.argv) != 4:
        print(
            f"用法: {sys.argv[0]} <xml_file_path> <output_json_path> <filter_file_path>",
            file=sys.stderr,
        )
        print("过滤文件格式：每行一个需要排除的文件路径", file=sys.stderr)
        sys.exit(1)

    xml_path = sys.argv[1]
    output_json_path = sys.argv[2]
    filter_file_path = sys.argv[3]  # 新增：过滤文件路径

    # 加载过滤列表
    filter_list = load_filter_list(filter_file_path)

    # 遍历覆盖率为0的文件
    zero_coverage_srcs = find_zero_coverage_src(xml_path, filter_list)

    # 将结果写入JSON文件
    try:
        with open(output_json_path, "w", encoding="utf-8") as f:
            # 写入JSON数据，使用indent参数美化输出，ensure_ascii=False确保中文正常显示
            json.dump(zero_coverage_srcs, f, ensure_ascii=False, indent=4)
        print(f"成功将{len(zero_coverage_srcs)}个结果写入到{output_json_path}")
    except Exception as e:
        print(f"写入JSON文件时出错: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
