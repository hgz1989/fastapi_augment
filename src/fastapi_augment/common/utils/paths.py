"""
@Author         : hangu
@CreateDate     : 2026/9/9
@Description    :
"""
import sys
from pathlib import Path


# 获取项目根目录路径
def get_root_dir(reference_path: str | Path, parent_index: int) -> Path:
    """
    动态获取项目根目录路径，兼容源码开发环境与 PyInstaller/Nuitka 打包二进制环境。

    源码模式：以传入的参考路径为基准，向上回溯 parent_index 层目录得到项目根；
    打包 frozen 模式：自动返回可执行文件(.exe/二进制)所在目录，忽略 reference_path、parent_index。

    Args:
        reference_path: 锚点参考路径，业务调用一般直接传入 __file__
        parent_index: 源码环境向上回溯层级下标

    Returns:
        项目根目录绝对路径

    Notes:
        parent_index >= 0；根据当前文件物理位置调整下标
    """
    if parent_index < 0:
        raise ValueError("parent_index 不能是负数")

    if getattr(sys, "frozen", False):
        path = Path(sys.executable).parent
    else:
        path = Path(reference_path).parents[parent_index]

    return path.resolve()
