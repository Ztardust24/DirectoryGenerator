# -*- encoding: utf-8 -*-
"""
@Time    : 2025/4/15 14:16
@File    : generate_dirs.py
@Version : v1.0
@Author  : Hui Zhang
@Contact : z1172787301@163.com
@Software: PyCharm
@Description: 自动生成十进制文件夹管理系统
"""
import yaml
import datetime
import logging
from pathlib import Path


# ======================
# 日志配置
# ======================
def setup_logger(root_dir):
    """配置日志记录器"""
    log_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("DirectoryGenerator")
    logger.setLevel(logging.DEBUG)

    # 文件日志格式
    file_formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台日志格式
    console_formatter = logging.Formatter(
        fmt='[%(levelname)s] %(message)s'
    )

    # 文件日志处理器
    log_file = log_dir / f"生成日志_{log_time}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # 控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger, log_file


# ======================
# 目录生成脚本
# ======================
class DirectoryGenerator:
    def __init__(self, config_path, root_dir="."):
        self.logger, self.log_file = setup_logger(root_dir)
        self.logger.info(f"初始化目录生成器，根目录: {root_dir}")

        self.config = self._load_config(config_path)
        self.root = Path(root_dir)
        self.created_dirs = set()

    def _load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"成功加载配置文件: {path}")
            return config['directory_structure']
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {str(e)}")
            raise

    def _create_dir(self, path):
        """创建目录并返回是否成功"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                self.logger.error(f"目录创建失败: {path}")
                return False
            self.created_dirs.add(str(path.resolve()))
            self.logger.debug(f"已创建目录: {path}")
            return True
        except Exception as e:
            self.logger.error(f"目录创建错误 ({path}): {str(e)}", exc_info=True)
            return False

    def _process_node(self, node, current_path):
        """递归处理配置节点"""
        if isinstance(node, dict):
            for dir_name, children in node.items():
                new_path = current_path / dir_name.strip()
                if self._create_dir(new_path):
                    self.logger.debug(f"处理子节点: {new_path}")
                    self._process_node(children, new_path)
        elif isinstance(node, list):
            for dir_name in node:
                new_path = current_path / dir_name.strip()
                self._create_dir(new_path)
        elif node is None:
            self.logger.debug("遇到空节点，跳过处理")
        else:
            self.logger.warning(f"忽略不支持的数据类型: {type(node)}")

    def generate(self):
        """生成目录结构"""
        self.logger.info("=" * 50)
        self.logger.info("开始生成目录体系")
        self.logger.info(f"配置文件结构: \n{yaml.dump(self.config, allow_unicode=True)}")

        try:
            self._process_node(self.config, self.root)
            self.logger.info(f"目录生成完成，共创建 {len(self.created_dirs)} 个目录")
            readme_result = self.generate_readme()

            if readme_result:
                self.logger.info(f"README 文件已生成")
            else:
                self.logger.warning("README 文件生成失败")

            return sorted(self.created_dirs)

        except Exception as e:
            self.logger.critical("目录生成过程中断!", exc_info=True)
            raise

    def generate_readme(self, output_file="README.md"):
        """生成目录结构说明文档"""
        readme_path = output_file
        markdown_lines = [
            "# 目录体系结构说明\n",
            "本目录结构按照十进制分类体系自动生成\n",
            f"**生成时间**：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**总目录数**：{len(self.created_dirs)}\n\n",
            "## 完整目录树\n"
        ]

        # 生成目录树结构（按层级缩进）
        dir_tree = []
        for dir_path in sorted(self.created_dirs):
            try:
                rel_path = Path(dir_path).relative_to(self.root)
                indent = "    " * (len(rel_path.parts) - 1)
                dir_tree.append(f"{indent}- {rel_path.parts[-1]}")
            except ValueError:
                # 处理路径相对化错误的情况
                dir_tree.append(f"- {dir_path}")

        markdown_lines.extend(dir_tree)
        markdown_lines.extend([
            "\n## 使用说明",
            "1. 本结构通过 `generate_dirs.py` 自动生成",
            "2. 修改 `config.yaml` 可调整目录结构",
            "3. 重新运行脚本将保留已存在目录\n",
            "## 配置文件示例",
            "```yaml",
            yaml.dump({"directory_structure": self.config}, allow_unicode=True, indent=2),
            "```"
        ])

        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(markdown_lines))
            print(f"\nREADME 文件已生成：{readme_path}")
            return True
        except Exception as e:
            print(f"生成README失败：{str(e)}")
            return False


if __name__ == "__main__":
    root_directory = "./十进制文件夹管理系统"
    generator = DirectoryGenerator("config.yaml", root_dir=root_directory)

    try:
        created_dirs = generator.generate()
        generator.logger.info(f"日志文件位置: {generator.log_file}")
    except Exception as e:
        generator.logger.error("程序运行失败!", exc_info=True)